"""
Hybrid LLM dispatcher for Second Brain.

Wraps an OllamaClient (primary, cheap) and a ClaudeClient (fallback, nuance)
behind a single LLMClient interface. Decides per-capture which backend to
use via `capture_router.route_capture`, validates the output with
`output_validator.validate_markdown_output`, and automatically falls back
to Claude when:

    - The local backend raises (connection error, timeout, bad response).
    - Validation fails in strict mode (one local retry first, then fallback).

Every fallback event is logged at WARNING level with enough detail to
audit cost and reliability later.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from processors.llm_client import LLMClient
from processors.capture_router import (
    CLAUDE,
    LOCAL,
    LOCAL_WITH_FALLBACK,
    route_capture,
)
from processors.output_validator import (
    OFF,
    STRICT,
    ValidationResult,
    validate_markdown_output,
)

logger = setup_logger(__name__)


class HybridLLMClient(LLMClient):
    """Routes captures between a local Ollama backend and Claude."""

    def __init__(
        self,
        ollama: LLMClient,
        claude: LLMClient,
        routing_config: Dict[str, Any] | None = None,
        validation_mode: str = STRICT,
        local_retry_count: int = 1,
        fallback_to_claude: bool = True,
    ):
        self.ollama = ollama
        self.claude = claude
        self.routing_config = routing_config or {}
        self.validation_mode = validation_mode
        self.local_retry_count = max(0, int(local_retry_count))
        self.fallback_to_claude = fallback_to_claude

        logger.info(
            f"Hybrid LLM client initialized "
            f"(validation={self.validation_mode}, "
            f"local_retries={self.local_retry_count}, "
            f"fallback_to_claude={self.fallback_to_claude})"
        )

    # ------------------------------------------------------------------
    # test_connection
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        ollama_ok = False
        claude_ok = False
        try:
            ollama_ok = self.ollama.test_connection()
        except Exception as e:
            logger.error(f"Ollama test_connection raised: {e}")
        try:
            claude_ok = self.claude.test_connection()
        except Exception as e:
            logger.error(f"Claude test_connection raised: {e}")

        if ollama_ok and claude_ok:
            return True
        if claude_ok and self.fallback_to_claude:
            logger.warning(
                "Ollama unreachable but Claude fallback is available — "
                "hybrid client is degraded but functional"
            )
            return True
        return False

    # ------------------------------------------------------------------
    # Dispatch methods (one per LLMClient surface method)
    # ------------------------------------------------------------------

    def process_telegram_capture(
        self,
        capture: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        return self._dispatch(
            capture=capture,
            capture_kind="telegram",
            has_documents=False,
            has_images=False,
            local_call=lambda: self.ollama.process_telegram_capture(capture, specs_dir),
            claude_call=lambda: self.claude.process_telegram_capture(capture, specs_dir),
        )

    def process_capture_with_images(
        self,
        capture: Dict[str, Any],
        image_paths: List[str],
        specs_dir: Path,
        notes_root: Path,
    ) -> str:
        return self._dispatch(
            capture=capture,
            capture_kind="image",
            has_documents=False,
            has_images=True,
            local_call=lambda: self.ollama.process_capture_with_images(
                capture, image_paths, specs_dir, notes_root
            ),
            claude_call=lambda: self.claude.process_capture_with_images(
                capture, image_paths, specs_dir, notes_root
            ),
        )

    def process_source_capture(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        return self._dispatch(
            capture=capture,
            capture_kind="source",
            has_documents=False,
            has_images=False,
            local_call=lambda: self.ollama.process_source_capture(
                capture, web_content, specs_dir
            ),
            claude_call=lambda: self.claude.process_source_capture(
                capture, web_content, specs_dir
            ),
        )

    def process_pdf_capture(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        return self._dispatch(
            capture=capture,
            capture_kind="pdf",
            has_documents=True,
            has_images=False,
            local_call=lambda: self.ollama.process_pdf_capture(
                capture, pdf_content, specs_dir
            ),
            claude_call=lambda: self.claude.process_pdf_capture(
                capture, pdf_content, specs_dir
            ),
        )

    # ------------------------------------------------------------------
    # Core dispatch logic
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        capture: Dict[str, Any],
        capture_kind: str,
        has_documents: bool,
        has_images: bool,
        local_call: Callable[[], str],
        claude_call: Callable[[], str],
    ) -> str:
        decision = route_capture(
            capture,
            routing_config=self.routing_config,
            has_documents=has_documents,
            has_images=has_images,
        )
        capture_id = capture.get("id")
        capture_type = capture.get("type", "?")

        logger.info(
            f"Routing capture {capture_id} (type={capture_type}, kind={capture_kind}) "
            f"-> {decision.route} [{decision.reason}]"
        )

        # Claude-only route: no local attempt.
        if decision.route == CLAUDE:
            return claude_call()

        # Local or local-with-fallback: try local first.
        if decision.route in (LOCAL, LOCAL_WITH_FALLBACK):
            markdown = self._try_local_with_retry(
                capture, capture_kind, local_call
            )
            if markdown is not None:
                return markdown

            # Local path exhausted. Fall back to Claude if allowed.
            if self.fallback_to_claude or decision.route == LOCAL_WITH_FALLBACK:
                logger.warning(
                    f"Capture {capture_id}: falling back to Claude after local failure"
                )
                return claude_call()

            # No fallback permitted — re-raise the last local error.
            raise RuntimeError(
                f"Local backend failed for capture {capture_id} and "
                f"fallback_to_claude is disabled"
            )

        raise ValueError(f"Unknown route decision: {decision.route!r}")

    def _try_local_with_retry(
        self,
        capture: Dict[str, Any],
        capture_kind: str,
        local_call: Callable[[], str],
    ) -> str | None:
        """
        Attempt the local call up to (1 + local_retry_count) times.

        Returns the validated markdown on success, or None if every attempt
        either raised or failed validation. Errors are logged, not raised,
        so the caller can fall back cleanly.
        """
        capture_id = capture.get("id")
        attempts = 1 + self.local_retry_count

        for attempt in range(1, attempts + 1):
            try:
                markdown = local_call()
            except Exception as e:
                logger.warning(
                    f"Capture {capture_id}: local backend raised on attempt "
                    f"{attempt}/{attempts}: {e}"
                )
                continue

            result: ValidationResult = validate_markdown_output(
                markdown,
                capture,
                mode=self.validation_mode,
                capture_kind=capture_kind,
            )
            if result.ok:
                if attempt > 1:
                    logger.info(
                        f"Capture {capture_id}: local succeeded on attempt {attempt}"
                    )
                return result.cleaned_markdown

            logger.warning(
                f"Capture {capture_id}: local output failed validation on "
                f"attempt {attempt}/{attempts}: {result.reason}"
            )

        return None

"""
LLM Client Abstraction for Kani-miso

Defines the backend-agnostic interface that all interpretation backends must
implement (Claude API, local Ollama, hybrid dispatcher, etc.), plus shared
helpers for prompt loading and image encoding, and a `build_llm_client`
factory that wires the configured backend from `config.yaml`.
"""

from __future__ import annotations

import base64
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers (used by both ClaudeClient and OllamaClient)
# ---------------------------------------------------------------------------


def load_prompt_template(prompt_file: Path) -> str:
    """Load a prompt template from disk. Raises if missing."""
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def encode_image_to_base64(image_path: str) -> Tuple[str, str]:
    """
    Encode an image file to (base64_data, media_type).

    Used by backends that need to send images in their request payload.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(path.suffix.lower(), "image/jpeg")

    with open(path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    return image_data, mime_type


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class LLMClient(ABC):
    """
    Abstract interface for capture-interpretation backends.

    Every backend (ClaudeClient, OllamaClient, HybridLLMClient) implements the
    same four process_* methods plus test_connection, so Processor can call
    them interchangeably.
    """

    @abstractmethod
    def process_telegram_capture(
        self,
        capture: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        ...

    @abstractmethod
    def process_capture_with_images(
        self,
        capture: Dict[str, Any],
        image_paths: List[str],
        specs_dir: Path,
        notes_root: Path,
    ) -> str:
        ...

    @abstractmethod
    def process_source_capture(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        ...

    @abstractmethod
    def process_pdf_capture(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        ...


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    Build the configured LLM client from the top-level config dict.

    Reads the `llm:` block if present (primary: hybrid | claude | ollama).
    If the `llm:` block is missing entirely, falls back to Claude-only mode,
    preserving the pre-abstraction behavior for any config.yaml that hasn't
    been migrated yet.

    Args:
        config: Parsed config.yaml as a dict.

    Returns:
        An LLMClient instance (ClaudeClient, OllamaClient, or HybridLLMClient).
    """
    llm_config: Optional[Dict[str, Any]] = config.get("llm")

    # Backwards-compat: no llm: block => pure Claude, matches old processor.
    if not llm_config:
        logger.info("No 'llm:' block in config; defaulting to Claude-only backend")
        return _build_claude_client(config)

    primary = (llm_config.get("primary") or "hybrid").lower()

    if primary == "claude":
        logger.info("Building Claude-only LLM backend")
        return _build_claude_client(config)

    if primary == "ollama":
        logger.info("Building Ollama-only LLM backend")
        return _build_ollama_client(config)

    if primary == "hybrid":
        logger.info("Building hybrid LLM backend (Ollama primary, Claude fallback)")
        return _build_hybrid_client(config)

    raise ValueError(
        f"Unknown llm.primary value: {primary!r}. "
        f"Expected one of: hybrid, claude, ollama."
    )


def _build_claude_client(config: Dict[str, Any]) -> "LLMClient":
    """Build a ClaudeClient from the `claude:` block in config."""
    from processors.claude_client import ClaudeClient  # local import to avoid cycles

    claude_cfg = config.get("claude", {})
    return ClaudeClient(
        model=claude_cfg.get("model", "claude-opus-4-5-20251101"),
        max_tokens=claude_cfg.get("max_tokens", 4096),
        temperature=claude_cfg.get("temperature", 0.7),
    )


def _build_ollama_client(config: Dict[str, Any]) -> "LLMClient":
    """Build an OllamaClient from the `llm.ollama:` block in config."""
    from processors.ollama_client import OllamaClient

    ollama_cfg = config.get("llm", {}).get("ollama", {})
    return OllamaClient(
        base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
        model=ollama_cfg.get("model", "gemma4:e4b"),
        temperature=ollama_cfg.get("temperature", 0.7),
        num_predict=ollama_cfg.get("num_predict", 4096),
        timeout_seconds=ollama_cfg.get("timeout_seconds", 120),
        prompt_profile=ollama_cfg.get("prompt_profile", "local"),
    )


def _build_hybrid_client(config: Dict[str, Any]) -> "LLMClient":
    """Build a HybridLLMClient wrapping both backends."""
    from processors.hybrid_llm_client import HybridLLMClient

    claude = _build_claude_client(config)
    ollama = _build_ollama_client(config)

    llm_cfg = config.get("llm", {})
    return HybridLLMClient(
        ollama=ollama,
        claude=claude,
        routing_config=llm_cfg.get("routing", {}),
        validation_mode=(
            llm_cfg.get("ollama", {}).get("verbatim_validation", "strict")
        ),
        local_retry_count=int(
            llm_cfg.get("ollama", {}).get("retry_on_validation_fail", 1)
        ),
        fallback_to_claude=bool(llm_cfg.get("fallback_to_claude", True)),
    )

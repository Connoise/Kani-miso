"""
LLM Client Abstraction for Kani-miso

Defines the interface that interpretation backends implement (Claude API),
plus shared helpers for prompt loading and image encoding, and a
`build_llm_client` factory that wires the client from `config.yaml`.
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
# Shared helpers
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

    Implemented by ClaudeClient: four process_* methods plus test_connection,
    so Processor can call any backend interchangeably.
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
    Build the Claude client from the top-level config dict.

    Claude is the only backend. A leftover `llm:` block requesting another
    backend (ollama/hybrid, removed in Phase 0) is ignored with a warning.

    Args:
        config: Parsed config.yaml as a dict.

    Returns:
        A ClaudeClient instance.
    """
    from processors.claude_client import ClaudeClient  # local import to avoid cycles

    llm_config: Optional[Dict[str, Any]] = config.get("llm")
    if llm_config:
        primary = (llm_config.get("primary") or "claude").lower()
        if primary != "claude":
            logger.warning(
                f"config llm.primary={primary!r} is no longer supported; "
                f"local/hybrid backends were removed. Using Claude."
            )

    claude_cfg = config.get("claude", {})
    return ClaudeClient(
        model=claude_cfg.get("model", "claude-opus-4-8"),
        max_tokens=claude_cfg.get("max_tokens", 4096),
    )

"""
Ollama LLM backend for Second Brain.

Talks to a local Ollama server over HTTP using the /api/chat endpoint. Uses
a compact prompt profile (specs/prompts/<profile>/) tuned for small local
models — the full Claude-facing prompts in specs/ would overwhelm a 4B model.

Implements the same LLMClient surface as ClaudeClient so the Processor can
use them interchangeably via HybridLLMClient.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import requests

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from processors.llm_client import (
    LLMClient,
    encode_image_to_base64,
    load_prompt_template,
)

logger = setup_logger(__name__)


# Local-path content budget is much smaller than Claude's 80k — a 4B model's
# effective reasoning window is tiny compared to its nominal context. Long
# sources/PDFs route to Claude under the default cheap-first policy anyway.
_LOCAL_MAX_CONTENT_CHARS = 12000


class OllamaClient(LLMClient):
    """LLMClient implementation backed by a local Ollama server."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma4:e4b",
        temperature: float = 0.7,
        num_predict: int = 4096,
        timeout_seconds: int = 120,
        prompt_profile: str = "local",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        self.timeout_seconds = timeout_seconds
        self.prompt_profile = prompt_profile

        logger.info(
            f"Initialized Ollama client (base_url={self.base_url}, "
            f"model={self.model}, profile={self.prompt_profile})"
        )

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """Check that the Ollama server is reachable and the model is pulled."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/tags",
                timeout=min(self.timeout_seconds, 10),
            )
            resp.raise_for_status()
            tags = resp.json()
            models = [m.get("name", "") for m in tags.get("models", [])]
            # Accept exact match or model_name:tag prefix match
            if self.model in models or any(
                m.split(":")[0] == self.model.split(":")[0] for m in models
            ):
                logger.info(f"Ollama connection OK; model {self.model} available")
                return True
            logger.error(
                f"Ollama reachable but model {self.model!r} not pulled. "
                f"Available: {models}"
            )
            return False
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Prompt loading (uses the compact profile under specs/prompts/<profile>/)
    # ------------------------------------------------------------------

    def _profile_dir(self, specs_dir: Path) -> Path:
        return specs_dir / "prompts" / self.prompt_profile

    def _load_prompt(self, specs_dir: Path, filename: str) -> str:
        return load_prompt_template(self._profile_dir(specs_dir) / filename)

    # ------------------------------------------------------------------
    # Chat call
    # ------------------------------------------------------------------

    def _chat(
        self,
        system_prompt: str,
        user_content: str,
        images_b64: List[str] | None = None,
    ) -> str:
        """POST to /api/chat and return the assistant's message content."""
        user_message: Dict[str, Any] = {
            "role": "user",
            "content": user_content,
        }
        if images_b64:
            user_message["images"] = images_b64

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                user_message,
            ],
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            },
        }

        logger.debug(
            f"Ollama chat request: model={self.model}, "
            f"system_chars={len(system_prompt)}, user_chars={len(user_content)}, "
            f"images={len(images_b64) if images_b64 else 0}"
        )

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as e:
            raise OllamaRequestError(f"Ollama request failed: {e}") from e

        if resp.status_code >= 400:
            raise OllamaRequestError(
                f"Ollama returned HTTP {resp.status_code}: {resp.text[:500]}"
            )

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise OllamaRequestError(f"Ollama returned non-JSON response: {e}") from e

        message = data.get("message") or {}
        content = message.get("content", "")
        if not content:
            raise OllamaRequestError(
                f"Ollama returned empty content. Full response keys: {list(data.keys())}"
            )

        logger.debug(
            f"Ollama chat response: chars={len(content)}, "
            f"done={data.get('done')}, total_duration={data.get('total_duration')}"
        )
        return content

    # ------------------------------------------------------------------
    # process_telegram_capture
    # ------------------------------------------------------------------

    def process_telegram_capture(
        self,
        capture: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        system_prompt = self._load_prompt(specs_dir, "telegram-processing-prompt.md")
        user_content = self._build_telegram_user_message(capture)
        markdown = self._chat(system_prompt, user_content)
        logger.info(
            f"Ollama processed capture {capture.get('id')} (telegram)"
        )
        return markdown

    def _build_telegram_user_message(self, capture: Dict[str, Any]) -> str:
        lines = [
            f"Type: {capture.get('type', 'Thought')}",
            "",
            "Raw Capture (copy this text verbatim into the ## Raw Capture section):",
            capture.get("body", ""),
        ]
        for field in ("surface", "mood", "energy", "confidence", "trigger", "context"):
            if capture.get(field):
                lines.append(f"{field.capitalize()}: {capture[field]}")
        lines.append("")
        lines.append("Produce the note now. Output starts with '---' on line 1.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # process_capture_with_images
    # ------------------------------------------------------------------

    def process_capture_with_images(
        self,
        capture: Dict[str, Any],
        image_paths: List[str],
        specs_dir: Path,
        notes_root: Path,
    ) -> str:
        system_prompt = self._load_prompt(specs_dir, "telegram-processing-prompt.md")
        # Append minimal image instructions to the compact system prompt
        system_prompt += (
            "\n\n## Image Handling\n"
            "You will receive one or more images along with text. Describe what "
            "is shown, integrate it with the text, and embed each image using "
            "Obsidian syntax: ![[relative/path]]. Do not invent image paths — "
            "use the paths listed in the user message."
        )

        images_b64: List[str] = []
        rel_paths: List[str] = []
        for image_path in image_paths:
            try:
                data, _mime = encode_image_to_base64(image_path)
                images_b64.append(data)
                try:
                    rel = Path(image_path).relative_to(notes_root)
                    rel_paths.append(str(rel).replace("\\", "/"))
                except ValueError:
                    rel_paths.append(Path(image_path).name)
            except Exception as e:
                logger.error(f"Failed to encode image {image_path} for Ollama: {e}")
                raise OllamaRequestError(f"image encode failed: {e}") from e

        lines = [
            f"Type: {capture.get('type', 'Thought')}",
            f"Number of images: {len(image_paths)}",
            "",
            "Image paths to embed (use these EXACT paths):",
        ]
        for rel in rel_paths:
            lines.append(f"  - {rel}")
        lines.append("")
        lines.append("Associated text (copy verbatim into ## Raw Capture):")
        lines.append(capture.get("body", ""))
        for field in ("surface", "mood", "energy", "confidence", "trigger", "context"):
            if capture.get(field):
                lines.append(f"{field.capitalize()}: {capture[field]}")
        lines.append("")
        lines.append("Produce the note now. Output starts with '---' on line 1.")

        markdown = self._chat(
            system_prompt,
            "\n".join(lines),
            images_b64=images_b64,
        )
        logger.info(
            f"Ollama processed capture {capture.get('id')} with {len(image_paths)} images"
        )
        return markdown

    # ------------------------------------------------------------------
    # process_source_capture
    # ------------------------------------------------------------------

    def process_source_capture(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        system_prompt = self._load_prompt(specs_dir, "source-processing-prompt.md")
        user_content = self._build_source_user_message(capture, web_content)
        markdown = self._chat(system_prompt, user_content)
        logger.info(
            f"Ollama processed source capture {capture.get('id')}"
        )
        return markdown

    def _build_source_user_message(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
    ) -> str:
        metadata = web_content.get("metadata", {}) or {}
        url = web_content.get("url", "")
        body = (capture.get("body") or "").strip()
        user_context = body.replace(url, "").strip() if url else body

        lines = [
            f"Source URL: {url or 'Unknown'}",
            f"Title: {metadata.get('title', 'Unknown')}",
            f"Author: {metadata.get('author', 'Unknown')}",
            f"Published: {metadata.get('date', 'Unknown')}",
            f"Site: {metadata.get('site_name', metadata.get('domain', 'Unknown'))}",
            f"Captured at: {capture.get('captured_at', 'Unknown')}",
            "",
            "User context (why this was captured):",
            user_context if user_context else "(none provided)",
            "",
        ]

        page = web_content.get("markdown_content", "") or ""
        if page:
            if len(page) > _LOCAL_MAX_CONTENT_CHARS:
                page = page[:_LOCAL_MAX_CONTENT_CHARS] + "\n[...truncated for local model...]"
            lines.append("Webpage content (for extraction of summary and key content):")
            lines.append(page)
        else:
            lines.append("Webpage content: (unavailable)")

        lines.append("")
        lines.append("Produce the source note now. Output starts with '---' on line 1.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # process_pdf_capture
    # ------------------------------------------------------------------

    def process_pdf_capture(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        system_prompt = self._load_prompt(specs_dir, "pdf-processing-prompt.md")
        user_content = self._build_pdf_user_message(capture, pdf_content)
        markdown = self._chat(system_prompt, user_content)
        logger.info(
            f"Ollama processed PDF capture {capture.get('id')}"
        )
        return markdown

    def _build_pdf_user_message(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
    ) -> str:
        metadata = pdf_content.get("metadata", {}) or {}
        file_name = pdf_content.get("file_name", "Unknown")

        # Strip "PDF: <filename>" prefix from user body if present
        body = (capture.get("body") or "").strip()
        prefix = f"PDF: {file_name}"
        user_context = body[len(prefix):].strip() if body.startswith(prefix) else body

        lines = [
            f"PDF file: {file_name}",
            f"Pages: {pdf_content.get('page_count', 'Unknown')}",
            f"Title: {metadata.get('title', 'Unknown')}",
            f"Author: {metadata.get('author', 'Unknown')}",
            f"Captured at: {capture.get('captured_at', 'Unknown')}",
            "",
            "User context (why this was captured):",
            user_context if user_context else "(none provided)",
            "",
        ]

        text = pdf_content.get("text", "") or ""
        if text:
            if len(text) > _LOCAL_MAX_CONTENT_CHARS:
                text = text[:_LOCAL_MAX_CONTENT_CHARS] + "\n[...truncated for local model...]"
            lines.append("Extracted PDF text:")
            lines.append(text)
        else:
            lines.append("Extracted PDF text: (unavailable)")

        lines.append("")
        lines.append("Produce the PDF source note now. Output starts with '---' on line 1.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class OllamaRequestError(RuntimeError):
    """Raised when a request to the Ollama server fails for any reason."""

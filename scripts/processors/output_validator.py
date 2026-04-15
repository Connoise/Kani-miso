"""
Output validator for LLM-generated capture notes.

Enforces three things mechanically, since a small local model cannot be
trusted to follow them from prompting alone:

1. No stray code fences wrapping the note.
2. Valid-looking YAML frontmatter beginning on line 1.
3. The raw capture body appears verbatim inside the note's preservation
   section ("## Raw Capture" for most captures, "## Key Content" or
   "## User Context" for source/PDF variants).

The verbatim check is the most important one — CLAUDE.md treats raw-capture
preservation as a non-negotiable rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Modes
STRICT = "strict"
LENIENT = "lenient"
OFF = "off"


@dataclass
class ValidationResult:
    ok: bool
    cleaned_markdown: str
    reason: Optional[str]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate_markdown_output(
    markdown: str,
    capture: Dict[str, Any],
    mode: str = STRICT,
    capture_kind: str = "telegram",
) -> ValidationResult:
    """
    Clean and validate an LLM-produced markdown note.

    Args:
        markdown: Raw model output.
        capture: The capture dict (needs 'body').
        mode: "strict" | "lenient" | "off".
            - strict: any failure returns ok=False
            - lenient: failures log warnings, ok=True
            - off: only fence-stripping runs
        capture_kind: "telegram" | "source" | "pdf" | "image".
            Controls which section is checked for verbatim preservation.

    Returns:
        ValidationResult with cleaned markdown and ok flag.
    """
    cleaned = _strip_code_fences(markdown)

    if mode == OFF:
        return ValidationResult(ok=True, cleaned_markdown=cleaned, reason=None)

    # 1. Frontmatter check
    fm_ok, fm_reason = _check_frontmatter(cleaned)
    if not fm_ok:
        return _fail(cleaned, fm_reason, mode)

    # 2. Verbatim check
    verbatim_ok, verbatim_reason = _check_verbatim(cleaned, capture, capture_kind)
    if not verbatim_ok:
        return _fail(cleaned, verbatim_reason, mode)

    return ValidationResult(ok=True, cleaned_markdown=cleaned, reason=None)


# ---------------------------------------------------------------------------
# Internal checks
# ---------------------------------------------------------------------------


_FENCE_OPEN = re.compile(r"^\s*```(?:markdown|md)?\s*\n", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\n\s*```\s*$", re.IGNORECASE)


def _strip_code_fences(markdown: str) -> str:
    """Remove leading/trailing ```markdown or ``` wrappers, if present."""
    s = markdown.strip("\ufeff")  # strip BOM if any
    s = s.strip()
    # Leading fence
    m = _FENCE_OPEN.match(s)
    if m:
        s = s[m.end():]
    # Trailing fence
    m2 = _FENCE_CLOSE.search(s)
    if m2:
        s = s[: m2.start()]
    return s.strip() + "\n"


def _check_frontmatter(markdown: str) -> tuple[bool, Optional[str]]:
    """Check that the note starts with a YAML frontmatter block."""
    lines = markdown.splitlines()
    if not lines:
        return False, "empty output"
    if lines[0].strip() != "---":
        return False, "line 1 is not '---' (missing frontmatter opener)"
    # Find closing --- within first 40 lines
    for i in range(1, min(40, len(lines))):
        if lines[i].strip() == "---":
            return True, None
    return False, "no closing '---' within first 40 lines of output"


# Section headers checked for verbatim preservation per capture kind.
# First matching section that actually exists in the output will be used.
_VERBATIM_SECTIONS = {
    "telegram": ["## Raw Capture"],
    "image": ["## Raw Capture"],
    "source": ["## Why This Was Captured", "## Key Content", "## Raw Capture"],
    "pdf": ["## Why This Was Captured", "## Extracted PDF Text", "## Raw Capture"],
}


def _check_verbatim(
    markdown: str,
    capture: Dict[str, Any],
    capture_kind: str,
) -> tuple[bool, Optional[str]]:
    """
    Verify the capture body appears verbatim inside a preservation section.

    Whitespace is normalized (collapse runs of whitespace to single spaces,
    normalize line endings) before comparison so the check is robust to
    harmless reformatting but still rejects any rewrite or summarization.
    """
    body = (capture.get("body") or "").strip()
    if not body:
        # Nothing to preserve — edge case (image-only capture with empty text).
        return True, None

    # For source captures, the "body" often contains the URL and maybe a
    # short user context. We don't want to fail just because the URL isn't
    # quoted verbatim inside the note. Only enforce verbatim when the body
    # has meaningful prose beyond a URL.
    if capture_kind in ("source", "pdf"):
        stripped = _strip_urls(body).strip()
        if len(stripped) < 8:
            # Essentially just a URL or "PDF: filename.pdf" — nothing to preserve.
            return True, None
        body = stripped

    section_headers = _VERBATIM_SECTIONS.get(capture_kind, ["## Raw Capture"])
    section_text = _extract_first_section(markdown, section_headers)
    if section_text is None:
        return False, (
            f"none of the expected preservation sections "
            f"{section_headers} found in output"
        )

    if _normalize(body) in _normalize(section_text):
        return True, None

    return False, (
        f"capture body not found verbatim in preservation section "
        f"(kind={capture_kind})"
    )


def _extract_first_section(markdown: str, headers: list[str]) -> Optional[str]:
    """Return the text of the first header that exists, up to the next ## header."""
    for header in headers:
        idx = markdown.find(header)
        if idx == -1:
            continue
        start = idx + len(header)
        # Find next top-level heading (## ) after this one
        rest = markdown[start:]
        next_idx = re.search(r"\n## ", rest)
        if next_idx:
            return rest[: next_idx.start()]
        return rest
    return None


_WS_RUN = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Collapse whitespace runs, lowercase, strip."""
    return _WS_RUN.sub(" ", text).strip().lower()


_URL_RE = re.compile(r"https?://\S+")


def _strip_urls(text: str) -> str:
    return _URL_RE.sub("", text)


def _fail(cleaned: str, reason: str, mode: str) -> ValidationResult:
    if mode == LENIENT:
        logger.warning(f"Output validation (lenient) failed: {reason}")
        return ValidationResult(ok=True, cleaned_markdown=cleaned, reason=reason)
    # strict
    logger.warning(f"Output validation (strict) failed: {reason}")
    return ValidationResult(ok=False, cleaned_markdown=cleaned, reason=reason)

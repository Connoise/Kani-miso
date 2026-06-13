"""
Page snapshotter for link captures (specs/02-capture.md, link-capture design).

Preservation is deterministic and code-owned: the raw fetched HTML and the
full extracted text are always written; a self-contained offline snapshot
(CSS/images/fonts inlined) is added when the `monolith` binary is available.
The LLM never transcribes page content — the pipeline injects it into the
catalog note from the files written here.

Snapshot failures never fail a capture: whatever could be preserved is kept,
the rest is logged.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Subdirectory of sources/ that holds one folder per captured page
SNAPSHOTS_DIRNAME = "snapshots"


class Snapshotter:
    """Writes preservation artifacts for a fetched webpage."""

    def __init__(self, notes_root: Path, link_config: Optional[Dict[str, Any]] = None):
        """
        Args:
            notes_root: Vault root; snapshots go to sources/snapshots/<stem>/.
            link_config: The `link_capture:` block from config.yaml.
        """
        cfg = link_config or {}
        self.notes_root = Path(notes_root)
        self.snapshots_root = self.notes_root / "sources" / SNAPSHOTS_DIRNAME
        self.mode = str(cfg.get("snapshot", "monolith")).lower()
        self.timeout = int(cfg.get("snapshot_timeout_seconds", 60))
        self.max_bytes = int(cfg.get("max_snapshot_mb", 25)) * 1024 * 1024

    def snapshot(self, url: str, html: str, extracted_markdown: str, stem: str) -> Dict[str, Any]:
        """
        Write preservation artifacts for one captured page.

        Args:
            url: The (final) URL the page was fetched from.
            html: Raw fetched HTML, exactly as received.
            extracted_markdown: Deterministic full-text extraction.
            stem: Folder name, matching the catalog note's filename stem.

        Returns:
            Dict of vault-relative paths (as strings, POSIX separators):
            {'folder', 'raw_html', 'extracted', 'offline_html' (or None)}
        """
        folder = self.snapshots_root / stem
        folder.mkdir(parents=True, exist_ok=True)

        raw_path = folder / "page.html"
        raw_path.write_text(html, encoding="utf-8")

        extracted_path = folder / "extracted.md"
        header = (
            f"<!-- Deterministic text extraction of {url} -->\n"
            f"<!-- This file is a preservation artifact; do not edit. -->\n\n"
        )
        extracted_path.write_text(header + extracted_markdown, encoding="utf-8")

        offline_rel = None
        if self.mode == "monolith":
            offline_rel = self._monolith_snapshot(url, folder)

        rel = folder.relative_to(self.notes_root).as_posix()
        logger.info(
            f"Snapshot written: {rel} "
            f"(raw + extracted{' + offline' if offline_rel else ''})"
        )
        return {
            "folder": rel,
            "raw_html": f"{rel}/page.html",
            "extracted": f"{rel}/extracted.md",
            "offline_html": offline_rel,
        }

    def _monolith_snapshot(self, url: str, folder: Path) -> Optional[str]:
        """
        Produce a self-contained offline copy via the `monolith` binary.

        Returns the vault-relative path, or None when monolith is missing,
        times out, errors, or exceeds the size cap — never raises.
        """
        monolith = shutil.which("monolith")
        if not monolith:
            logger.info(
                "monolith not installed; skipping offline snapshot "
                "(raw HTML and extracted text were still preserved). "
                "See SETUP.md to enable full-page snapshots."
            )
            return None

        out_path = folder / "page.offline.html"
        try:
            result = subprocess.run(
                [monolith, url, "-o", str(out_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                logger.warning(
                    f"monolith failed for {url} (exit {result.returncode}): "
                    f"{result.stderr.strip()[:300]}"
                )
                out_path.unlink(missing_ok=True)
                return None

            if not out_path.exists() or out_path.stat().st_size == 0:
                logger.warning(f"monolith produced no output for {url}")
                out_path.unlink(missing_ok=True)
                return None

            if out_path.stat().st_size > self.max_bytes:
                logger.warning(
                    f"Offline snapshot of {url} is "
                    f"{out_path.stat().st_size // (1024 * 1024)} MB, over the "
                    f"{self.max_bytes // (1024 * 1024)} MB cap; discarding "
                    f"(raw HTML and extracted text were still preserved)"
                )
                out_path.unlink(missing_ok=True)
                return None

            return out_path.relative_to(self.notes_root).as_posix()

        except subprocess.TimeoutExpired:
            logger.warning(f"monolith timed out after {self.timeout}s for {url}")
            out_path.unlink(missing_ok=True)
            return None
        except Exception as e:
            logger.warning(f"monolith snapshot failed for {url}: {e}")
            out_path.unlink(missing_ok=True)
            return None


def head_by_words(markdown: str, word_cap: int) -> tuple[str, bool]:
    """
    Return the leading portion of `markdown` up to ~word_cap words, cut at a
    paragraph boundary, plus whether truncation occurred. Used to inject a
    readable head of the page into the catalog note while the full text lives
    in extracted.md.
    """
    paragraphs = markdown.split("\n\n")
    kept: list[str] = []
    count = 0
    for para in paragraphs:
        words = len(para.split())
        if kept and count + words > word_cap:
            return "\n\n".join(kept), True
        kept.append(para)
        count += words
    return markdown, False

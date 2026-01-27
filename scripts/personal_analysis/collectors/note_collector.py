"""
Note collector for personal analysis.

Collects and parses notes from /notes/ directory.
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from ..models import Note

logger = logging.getLogger(__name__)


class NoteCollector:
    """Collect and parse notes from the notes directory."""

    def __init__(self, notes_dir: Path):
        """
        Initialize the note collector.

        Args:
            notes_dir: Path to the /notes/ directory
        """
        self.notes_dir = notes_dir

    def collect_all(
        self,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[Note]:
        """
        Collect all notes from the directory.

        Args:
            date_start: Optional start date filter
            date_end: Optional end date filter

        Returns:
            List of Note objects sorted by creation date
        """
        notes = []

        if not self.notes_dir.exists():
            logger.warning(f"Notes directory does not exist: {self.notes_dir}")
            return notes

        for md_file in self.notes_dir.glob("*.md"):
            try:
                note = self._parse_note(md_file)
                if note:
                    # Apply date filters
                    if date_start and note.created_at < date_start:
                        continue
                    if date_end and note.created_at > date_end:
                        continue
                    notes.append(note)
            except Exception as e:
                logger.error(f"Error parsing note {md_file}: {e}")

        # Sort by creation date
        return sorted(notes, key=lambda n: n.created_at)

    def _parse_note(self, path: Path) -> Optional[Note]:
        """
        Parse a note file into a Note object.

        Args:
            path: Path to the markdown file

        Returns:
            Note object or None if parsing fails
        """
        content = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(content)

        # Extract raw capture section
        raw_capture = self._extract_section(body, "Raw Capture") or body

        # Extract other sections
        interpretation = self._extract_section(body, "Initial Interpretation")
        themes = self._extract_themes(body)

        # Get creation date from frontmatter or filename
        created_at = self._get_created_at(frontmatter, path)

        # Extract title from first heading or filename
        title = self._extract_title(body, path)

        # Extract hub links
        hub_links = self._extract_wikilinks(body)

        return Note(
            path=path,
            title=title,
            raw_capture=raw_capture.strip(),
            created_at=created_at,
            source_type="note",
            frontmatter=frontmatter,
            interpretation=interpretation,
            themes=themes,
            tags=frontmatter.get("tags", []),
            hub_links=hub_links,
            mood=frontmatter.get("mood"),
            energy=frontmatter.get("energy"),
        )

    def _split_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Split content into frontmatter and body."""
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            frontmatter = {}

        body = parts[2].strip()
        return frontmatter, body

    def _extract_section(self, body: str, section_name: str) -> Optional[str]:
        """Extract content from a named section."""
        # Match ## Section Name or # Section Name
        pattern = rf"##?\s*{re.escape(section_name)}\s*\n(.*?)(?=\n##?\s|\Z)"
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_themes(self, body: str) -> List[str]:
        """Extract themes from the Themes section."""
        themes_text = self._extract_section(body, "Themes")
        if not themes_text:
            return []

        themes = []
        for line in themes_text.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                theme = line.lstrip("-").strip()
                if theme:
                    themes.append(theme)
        return themes

    def _extract_title(self, body: str, path: Path) -> str:
        """Extract title from first heading or derive from filename."""
        # Look for # Title
        match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Derive from filename: 2026-01-15--my-note.md -> My Note
        stem = path.stem
        if "--" in stem:
            title_part = stem.split("--", 1)[1]
        else:
            title_part = stem

        return title_part.replace("-", " ").title()

    def _extract_wikilinks(self, body: str) -> List[str]:
        """Extract all wikilinks from body."""
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, body)
        # Remove any link aliases (e.g., [[Note|Alias]] -> Note)
        return [m.split("|")[0] for m in matches]

    def _get_created_at(self, frontmatter: Dict[str, Any], path: Path) -> datetime:
        """Get creation date from frontmatter or filename."""
        # Try frontmatter fields
        for field in ["created_at", "captured_at", "date"]:
            if field in frontmatter:
                value = frontmatter[field]
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        pass

        # Try to extract from filename (YYYY-MM-DD--slug.md)
        match = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                pass

        # Fallback to file modification time
        return datetime.fromtimestamp(path.stat().st_mtime)

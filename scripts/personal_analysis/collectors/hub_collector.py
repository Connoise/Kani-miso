"""
Hub collector for personal analysis.

Collects hub metadata from /hubs/ directory.
Hubs are used for linking context only, not analyzed as content.
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ..models import Hub

logger = logging.getLogger(__name__)


class HubCollector:
    """Collect hub metadata for linking context."""

    def __init__(self, hubs_dir: Path):
        """
        Initialize the hub collector.

        Args:
            hubs_dir: Path to the /hubs/ directory
        """
        self.hubs_dir = hubs_dir

    def collect_all(self) -> List[Hub]:
        """
        Collect all hub metadata from the directory.

        Returns:
            List of Hub objects
        """
        hubs = []

        if not self.hubs_dir.exists():
            logger.warning(f"Hubs directory does not exist: {self.hubs_dir}")
            return hubs

        for md_file in self.hubs_dir.glob("*.md"):
            try:
                hub = self._parse_hub(md_file)
                if hub:
                    hubs.append(hub)
            except Exception as e:
                logger.error(f"Error parsing hub {md_file}: {e}")

        logger.info(f"Collected {len(hubs)} hubs")
        return sorted(hubs, key=lambda h: h.title)

    def _parse_hub(self, path: Path) -> Optional[Hub]:
        """Parse a hub file into metadata."""
        content = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(content)

        # Get title from first heading or filename
        title = self._extract_title(body, path)

        # Get status from frontmatter
        status = frontmatter.get("status", "unknown")

        # Get creation date
        created_at = None
        if "created_at" in frontmatter:
            value = frontmatter["created_at"]
            if isinstance(value, datetime):
                created_at = value
            elif isinstance(value, str):
                try:
                    created_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass

        # Extract linked notes from body
        linked_notes = self._extract_linked_notes(body)

        return Hub(
            path=path,
            title=title,
            status=status,
            created_at=created_at,
            linked_notes=linked_notes,
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

    def _extract_title(self, body: str, path: Path) -> str:
        """Extract title from first heading or filename."""
        match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return path.stem

    def _extract_linked_notes(self, body: str) -> List[str]:
        """Extract note wikilinks from the body."""
        # Find all wikilinks
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, body)

        # Filter to likely note links (have date prefix or are in notes format)
        note_links = []
        for match in matches:
            link = match.split("|")[0]  # Remove alias
            # Check if it looks like a note (has date prefix)
            if re.match(r"\d{4}-\d{2}-\d{2}", link):
                note_links.append(link)

        return note_links

    def get_hub_map(self, hubs: List[Hub]) -> Dict[str, Hub]:
        """
        Create a map of hub titles to Hub objects.

        Useful for quick lookups when linking notes to hubs.
        """
        return {hub.title.lower(): hub for hub in hubs}

    def get_hub_connectivity(self, hubs: List[Hub]) -> Dict[str, int]:
        """
        Get connectivity count for each hub.

        Returns dict mapping hub title to number of linked notes.
        """
        return {hub.title: len(hub.linked_notes) for hub in hubs}

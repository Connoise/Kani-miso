"""
Evidence linker for personal analysis.

Helps create and validate wikilinks to source notes.
"""

import re
from pathlib import Path
from typing import List, Dict, Set
import logging

from ..models import Note, Tweet, CollectedContent

logger = logging.getLogger(__name__)


class EvidenceLinker:
    """Create and validate wikilinks to source notes."""

    def __init__(self, content: CollectedContent):
        """
        Initialize the evidence linker.

        Args:
            content: Collected content for reference
        """
        self.content = content
        self._note_map = self._build_note_map()

    def _build_note_map(self) -> Dict[str, Note]:
        """Build a map of note names to Note objects."""
        note_map = {}
        for note in self.content.all_notes:
            # Map by filename stem
            note_map[note.path.stem] = note
            # Also map by title if different
            if note.title.lower() != note.path.stem.lower():
                note_map[note.title] = note
        return note_map

    def validate_link(self, link: str) -> bool:
        """
        Check if a wikilink is valid.

        Args:
            link: The link text (without [[ ]])

        Returns:
            True if the link points to a real note
        """
        # Remove any alias
        link_target = link.split("|")[0].strip()
        return link_target in self._note_map

    def get_all_valid_links(self) -> Set[str]:
        """Get all valid note link targets."""
        return set(self._note_map.keys())

    def find_matching_notes(self, term: str, limit: int = 5) -> List[str]:
        """
        Find notes that might match a term.

        Args:
            term: Search term
            limit: Maximum results

        Returns:
            List of matching note names
        """
        term_lower = term.lower()
        matches = []

        for name, note in self._note_map.items():
            if term_lower in name.lower():
                matches.append(name)
            elif term_lower in note.raw_capture.lower():
                matches.append(name)

            if len(matches) >= limit:
                break

        return matches

    def add_evidence_links(self, content: str, max_links: int = 10) -> str:
        """
        Add evidence links to content where appropriate.

        This is a simple implementation that could be enhanced
        to identify specific claims and link them to sources.

        Args:
            content: Markdown content
            max_links: Maximum links to add

        Returns:
            Content with added links
        """
        # For now, just validate existing links
        # A more sophisticated version would identify claims
        # and automatically find supporting notes

        existing_links = self._extract_links(content)
        valid_links = []
        invalid_links = []

        for link in existing_links:
            if self.validate_link(link):
                valid_links.append(link)
            else:
                invalid_links.append(link)

        if invalid_links:
            logger.warning(f"Found {len(invalid_links)} invalid links: {invalid_links[:5]}")

        return content

    def _extract_links(self, content: str) -> List[str]:
        """Extract all wikilinks from content."""
        pattern = r"\[\[([^\]]+)\]\]"
        return re.findall(pattern, content)

    def generate_citation_section(self, links: List[str]) -> str:
        """
        Generate a formatted citation section.

        Args:
            links: List of note links

        Returns:
            Markdown formatted citation section
        """
        if not links:
            return ""

        valid_links = [link for link in links if self.validate_link(link)]

        if not valid_links:
            return ""

        section = "> [!evidence] Evidence Base\n"
        for link in valid_links[:10]:  # Limit to 10
            note = self._note_map.get(link.split("|")[0])
            if note:
                date_str = note.created_at.strftime("%Y-%m-%d")
                section += f"> - [[{note.path.stem}]] ({date_str})\n"

        return section

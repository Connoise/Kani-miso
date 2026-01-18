"""
File Writer for Second Brain
Handles creation and writing of markdown files.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from utils.slugify import create_slug

logger = setup_logger(__name__)


class FileWriter:
    """Handles writing processed captures to markdown files."""

    def __init__(self, repo_root: Path, folders: Dict[str, str], notes_root: Path = None):
        """
        Initialize file writer.

        Args:
            repo_root: Path to repository root (for specs, config, etc.)
            folders: Dictionary mapping note types to folder names
            notes_root: Path to notes storage directory (defaults to repo_root)
                       Set to a different path to store notes separately from the repo
        """
        self.repo_root = Path(repo_root)
        self.notes_root = Path(notes_root) if notes_root else self.repo_root
        self.folders = folders

        # Ensure folders exist in notes_root
        for folder in self.folders.values():
            (self.notes_root / folder).mkdir(parents=True, exist_ok=True)

        if self.notes_root != self.repo_root:
            logger.info(f"Notes will be saved to: {self.notes_root}")

    def get_destination_folder(self, note_type: str) -> Path:
        """
        Determine destination folder based on note type.

        Args:
            note_type: Type of note (Thought, Reflection, Source, etc.)

        Returns:
            Path to destination folder (in notes_root directory)
        """
        type_to_folder = {
            'Thought': self.folders['notes'],
            'Reflection': self.folders['reflections'],
            'Question': self.folders['notes'],
            'Source': self.folders['sources'],
            'Log': self.folders['notes'],
            'Idea': self.folders['notes'],
            'Quote': self.folders['notes'],
            'Tweet': self.folders.get('tweets', 'tweets'),
        }

        folder_name = type_to_folder.get(note_type, self.folders['inbox'])
        return self.notes_root / folder_name

    def extract_title_from_markdown(self, markdown_content: str) -> str:
        """
        Extract the title (first # heading) from markdown content.

        Args:
            markdown_content: Processed markdown content from Claude

        Returns:
            Extracted title or 'untitled'
        """
        # Look for first # heading
        match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fallback: use first line of non-empty text
        for line in markdown_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('---'):
                return line[:100]  # Limit length

        return "untitled"

    def generate_filename(self, captured_at: datetime, title: str) -> str:
        """
        Generate filename following convention: YYYY-MM-DD--slug.md

        Args:
            captured_at: Capture timestamp
            title: Note title

        Returns:
            Filename string
        """
        date_str = captured_at.strftime("%Y-%m-%d")
        slug = create_slug(title, max_length=50)
        return f"{date_str}--{slug}.md"

    def write_note(
        self,
        markdown_content: str,
        capture: Dict[str, Any],
    ) -> Path:
        """
        Write processed markdown to appropriate file.

        Args:
            markdown_content: Processed markdown from Claude
            capture: Original capture dictionary from queue

        Returns:
            Path to created file
        """
        # Extract title from markdown
        title = self.extract_title_from_markdown(markdown_content)

        # Determine destination folder
        note_type = capture.get('type', 'Thought')
        dest_folder = self.get_destination_folder(note_type)

        # Generate filename
        captured_at = datetime.fromisoformat(capture['captured_at'])
        filename = self.generate_filename(captured_at, title)
        file_path = dest_folder / filename

        # Check for conflicts
        if file_path.exists():
            # Append timestamp to make unique
            timestamp = datetime.now().strftime("%H%M%S")
            base = file_path.stem
            file_path = dest_folder / f"{base}-{timestamp}.md"
            logger.warning(f"File exists, using: {file_path.name}")

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Wrote note: {file_path.relative_to(self.notes_root)}")
        return file_path

    def get_relative_path(self, file_path: Path) -> str:
        """
        Get path relative to notes root.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path string
        """
        return str(file_path.relative_to(self.notes_root))

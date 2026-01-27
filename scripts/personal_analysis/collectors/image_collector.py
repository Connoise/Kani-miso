"""
Image collector for personal analysis.

Collects images from /images/ directory and embedded in notes.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import logging

from ..models import Image, Note

logger = logging.getLogger(__name__)

# Supported image formats
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".heif"}


class ImageCollector:
    """Collect images for visual analysis."""

    def __init__(self, images_dir: Path, notes_root: Path):
        """
        Initialize the image collector.

        Args:
            images_dir: Path to the /images/ directory
            notes_root: Root path for resolving embedded image paths
        """
        self.images_dir = images_dir
        self.notes_root = notes_root

    def collect_all(
        self,
        notes: Optional[List[Note]] = None,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[Image]:
        """
        Collect all images from directory and embedded in notes.

        Args:
            notes: Optional list of notes to scan for embedded images
            date_start: Optional start date filter
            date_end: Optional end date filter

        Returns:
            List of Image objects
        """
        images = []
        seen_paths: Set[Path] = set()

        # Collect from images directory
        if self.images_dir.exists():
            for img_file in self._find_images(self.images_dir):
                if img_file not in seen_paths:
                    image = self._create_image(img_file)
                    if image:
                        images.append(image)
                        seen_paths.add(img_file)

        # Collect embedded images from notes
        if notes:
            for note in notes:
                embedded = self._find_embedded_images(note)
                for img_path in embedded:
                    if img_path not in seen_paths and img_path.exists():
                        image = self._create_image(img_path, associated_note=note.path)
                        if image:
                            images.append(image)
                            seen_paths.add(img_path)

        # Apply date filters
        filtered_images = []
        for image in images:
            if date_start and image.created_at and image.created_at < date_start:
                continue
            if date_end and image.created_at and image.created_at > date_end:
                continue
            filtered_images.append(image)

        logger.info(f"Collected {len(filtered_images)} images")
        return filtered_images

    def _find_images(self, directory: Path) -> List[Path]:
        """Find all image files in a directory recursively."""
        images = []
        for ext in IMAGE_EXTENSIONS:
            images.extend(directory.rglob(f"*{ext}"))
            images.extend(directory.rglob(f"*{ext.upper()}"))
        return sorted(images)

    def _find_embedded_images(self, note: Note) -> List[Path]:
        """Find images embedded in a note."""
        images = []
        content = note.raw_capture + (note.interpretation or "")

        # Match Obsidian/Markdown image embeds: ![[image.png]] or ![alt](path/to/image.png)
        patterns = [
            r"!\[\[([^\]]+\.(?:jpg|jpeg|png|gif|webp|bmp|heic|heif))\]\]",  # Obsidian style
            r"!\[[^\]]*\]\(([^)]+\.(?:jpg|jpeg|png|gif|webp|bmp|heic|heif))\)",  # Markdown style
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Resolve path relative to notes_root
                img_path = self._resolve_image_path(match, note.path)
                if img_path:
                    images.append(img_path)

        return images

    def _resolve_image_path(self, image_ref: str, note_path: Path) -> Optional[Path]:
        """Resolve an image reference to an absolute path."""
        # Remove any alias part (e.g., image.png|500)
        image_ref = image_ref.split("|")[0].strip()

        # Try different resolution strategies
        candidates = [
            # Relative to note
            note_path.parent / image_ref,
            # Relative to notes_root
            self.notes_root / image_ref,
            # In images directory
            self.images_dir / image_ref,
            # In images directory with just filename
            self.images_dir / Path(image_ref).name,
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        return None

    def _create_image(
        self, path: Path, associated_note: Optional[Path] = None
    ) -> Optional[Image]:
        """Create an Image object from a path."""
        try:
            # Try to get creation date from file metadata
            stat = path.stat()
            created_at = datetime.fromtimestamp(stat.st_mtime)

            return Image(
                path=path,
                created_at=created_at,
                associated_note=associated_note,
            )
        except Exception as e:
            logger.error(f"Error creating image object for {path}: {e}")
            return None

    def get_image_paths_for_api(self, images: List[Image], max_images: int = 20) -> List[Path]:
        """
        Get image paths suitable for Claude API calls.

        Args:
            images: List of Image objects
            max_images: Maximum number of images to include (API limit considerations)

        Returns:
            List of image paths
        """
        # Sort by date to get a temporal spread
        sorted_images = sorted(images, key=lambda i: i.created_at or datetime.min)

        if len(sorted_images) <= max_images:
            return [img.path for img in sorted_images]

        # Sample evenly across the timeline
        step = len(sorted_images) / max_images
        selected = []
        for i in range(max_images):
            idx = int(i * step)
            selected.append(sorted_images[idx].path)

        return selected

"""
Reflection collector for personal analysis.

Collects and parses reflections from /reflections/ directory.
Reflections are treated the same as notes but marked as emotional content.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from .note_collector import NoteCollector
from ..models import Note

logger = logging.getLogger(__name__)


class ReflectionCollector(NoteCollector):
    """
    Collect and parse reflections from the reflections directory.

    Inherits from NoteCollector since reflections have the same format,
    but marks them as source_type="reflection" for sampling prioritization.
    """

    def __init__(self, reflections_dir: Path):
        """
        Initialize the reflection collector.

        Args:
            reflections_dir: Path to the /reflections/ directory
        """
        super().__init__(reflections_dir)

    def collect_all(
        self,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[Note]:
        """
        Collect all reflections from the directory.

        Args:
            date_start: Optional start date filter
            date_end: Optional end date filter

        Returns:
            List of Note objects (marked as reflections) sorted by creation date
        """
        notes = super().collect_all(date_start, date_end)

        # Mark all as reflections
        for note in notes:
            note.source_type = "reflection"

        return notes

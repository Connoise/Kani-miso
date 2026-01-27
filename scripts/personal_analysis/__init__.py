"""
Personal Analysis Module

Deep personal analysis of notes and tweets using Claude Opus 4.5.
Generates multidisciplinary character analysis with Obsidian-formatted output.
"""

from .analyzer import PersonalAnalyzer
from .config import AnalysisConfig

__all__ = ["PersonalAnalyzer", "AnalysisConfig"]

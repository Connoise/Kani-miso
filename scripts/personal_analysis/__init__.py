"""
Personal Analysis Module

Deep personal analysis of notes and tweets using Claude Opus 4.5.
Generates multidisciplinary character analysis with Obsidian-formatted output.

Also includes condensation functionality to create compact, shareable
profile documents from full analysis output.
"""

from .analyzer import PersonalAnalyzer
from .config import AnalysisConfig
from .condenser import AnalysisCondenser

__all__ = ["PersonalAnalyzer", "AnalysisConfig", "AnalysisCondenser"]

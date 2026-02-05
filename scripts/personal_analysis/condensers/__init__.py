"""
Condensers module for personal analysis.

This module provides functionality to condense full analysis output
into compact, shareable profile documents.
"""

from .models import (
    PersonalBackground,
    CategorySummary,
    CondensationResult,
    FieldDef,
    CategoryDef,
)
from .analysis_reader import AnalysisReader, AnalysisDocument
from .background_condenser import BackgroundCondenser
from .category_condenser import CategoryCondenser
from .user_verifier import UserVerifier
from .profile_generator import ProfileGenerator

__all__ = [
    # Models
    "PersonalBackground",
    "CategorySummary",
    "CondensationResult",
    "FieldDef",
    "CategoryDef",
    # Components
    "AnalysisReader",
    "AnalysisDocument",
    "BackgroundCondenser",
    "CategoryCondenser",
    "UserVerifier",
    "ProfileGenerator",
]

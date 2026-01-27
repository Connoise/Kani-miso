"""Analysis modules for different dimensions of personal analysis."""

from .base import BaseAnalyzer, AnalysisResult
from .psychological import PsychologicalAnalyzer
from .emotional import EmotionalAnalyzer
from .intellectual import IntellectualAnalyzer
from .ethical import EthicalAnalyzer
from .spiritual import SpiritualAnalyzer
from .philosophical import PhilosophicalAnalyzer
from .visual import VisualAnalyzer
from .pattern import PatternAnalyzer
from .relational import RelationalAnalyzer
from .synthesis import SynthesisAnalyzer

__all__ = [
    "BaseAnalyzer",
    "AnalysisResult",
    "PsychologicalAnalyzer",
    "EmotionalAnalyzer",
    "IntellectualAnalyzer",
    "EthicalAnalyzer",
    "SpiritualAnalyzer",
    "PhilosophicalAnalyzer",
    "VisualAnalyzer",
    "PatternAnalyzer",
    "RelationalAnalyzer",
    "SynthesisAnalyzer",
]

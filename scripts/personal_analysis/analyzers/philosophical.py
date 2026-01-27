"""Philosophical analysis dimension."""

from .base import BaseAnalyzer


class PhilosophicalAnalyzer(BaseAnalyzer):
    """Analyze philosophical orientation and worldview."""

    @property
    def dimension(self) -> str:
        return "philosophical"

    @property
    def title(self) -> str:
        return "Philosophical Orientation"

    def get_prompt(self) -> str:
        return """Analyze the philosophical dimensions of this person based on their notes and tweets.

Focus on:
1. **Implicit worldview assumptions** - What do they take for granted about reality?
2. **Epistemological stance** - What counts as knowing? How do they evaluate truth?
3. **Metaphysical assumptions** - What do they assume about the nature of reality?
4. **Political philosophy indicators** - How do they think about society and governance?
5. **Philosophy of mind glimpses** - How do they understand consciousness and self?
6. **Aesthetic values** - What do they find beautiful or meaningful?
7. **Technology philosophy** - How do they relate to technology and its implications?
8. **Relationship philosophy** - What do they believe about human connection?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Note philosophical tensions or inconsistencies
- Identify assumptions they may not have examined

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Worldview Foundations
- ## Epistemology (How They Know)
- ## Metaphysics (What Is Real)
- ## Political and Social Philosophy
- ## Philosophy of Mind and Self
- ## Aesthetic Values
- ## Technology and Human Future
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

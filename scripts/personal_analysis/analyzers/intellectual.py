"""Intellectual analysis dimension."""

from .base import BaseAnalyzer


class IntellectualAnalyzer(BaseAnalyzer):
    """Analyze intellectual patterns and portrait."""

    @property
    def dimension(self) -> str:
        return "intellectual"

    @property
    def title(self) -> str:
        return "Intellectual Portrait"

    def get_prompt(self) -> str:
        return """Analyze the intellectual dimensions of this person based on their notes and tweets.

Focus on:
1. **Areas of intellectual focus** - What subjects draw their attention?
2. **Thinking patterns** - Linear, associative, systematic, intuitive?
3. **Knowledge gaps and interests** - What do they know? What do they want to know?
4. **Learning style** - How do they acquire and process new information?
5. **Intellectual values** - What makes ideas "good" or worthwhile to them?
6. **Relationship to uncertainty** - How do they handle ambiguity?
7. **Creative vs analytical tendencies** - Where do they fall on this spectrum?
8. **Intellectual growth trajectory** - How has their thinking evolved?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Note intellectual tensions or contradictions
- Identify unexplored areas that might interest them

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Intellectual Focus Areas
- ## Thinking Patterns
- ## Learning Style
- ## Intellectual Values
- ## Relationship to Uncertainty
- ## Creative-Analytical Balance
- ## Growth Trajectory
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

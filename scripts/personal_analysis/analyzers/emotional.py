"""Emotional analysis dimension."""

from .base import BaseAnalyzer


class EmotionalAnalyzer(BaseAnalyzer):
    """Analyze emotional patterns and landscape."""

    @property
    def dimension(self) -> str:
        return "emotional"

    @property
    def title(self) -> str:
        return "Emotional Landscape"

    def get_prompt(self) -> str:
        return """Analyze the emotional dimensions of this person based on their notes and tweets.

Focus on:
1. **Emotional range** - What feelings appear? Which are notably absent?
2. **Emotional triggers** - What provokes strong responses?
3. **Emotional regulation** - How are feelings managed?
4. **Dominant emotional themes** - What recurring emotional states appear?
5. **Emotional growth patterns** - How has emotional expression changed over time?
6. **Cognition-emotion relationship** - How do thinking and feeling interact?
7. **Unexpressed emotions** - What's implied but not directly stated?
8. **Emotional authenticity** - Is there alignment between felt and expressed?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Note contradictions between stated feelings and patterns
- Identify emotional blind spots

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Emotional Range
- ## Triggers and Responses
- ## Emotional Regulation Patterns
- ## Dominant Themes
- ## Growth Over Time
- ## The Unspoken
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

"""Spiritual analysis dimension."""

from .base import BaseAnalyzer


class SpiritualAnalyzer(BaseAnalyzer):
    """Analyze spiritual dimensions and meaning-making."""

    @property
    def dimension(self) -> str:
        return "spiritual"

    @property
    def title(self) -> str:
        return "Spiritual Dimensions"

    def get_prompt(self) -> str:
        return """Analyze the spiritual dimensions of this person based on their notes and tweets.

Note: "Spiritual" here is interpreted broadly - it includes religious belief but also secular meaning-making, existential questioning, and relationship to transcendence.

Focus on:
1. **Meaning-making patterns** - How do they construct meaning in their life?
2. **Relationship to transcendence** - What, if anything, feels larger than themselves?
3. **Existential themes and questions** - What big questions recur?
4. **Connection to something larger** - Community, nature, humanity, cosmos?
5. **Sacred/profane distinctions** - What is treated as sacred or inviolable?
6. **Ritualistic patterns** - What repeated practices give structure or meaning?
7. **Death and mortality themes** - How do they relate to finitude?
8. **Purpose and calling indicators** - Is there a sense of mission or calling?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Respect both religious and secular expressions of spirituality
- Note absence of spiritual themes if applicable

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Meaning-Making
- ## Transcendence and Connection
- ## Existential Questions
- ## The Sacred
- ## Rituals and Practices
- ## Mortality and Finitude
- ## Purpose and Calling
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

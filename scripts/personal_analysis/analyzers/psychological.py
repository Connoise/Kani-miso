"""Psychological analysis dimension."""

from .base import BaseAnalyzer


class PsychologicalAnalyzer(BaseAnalyzer):
    """Analyze psychological patterns and traits."""

    @property
    def dimension(self) -> str:
        return "psychological"

    @property
    def title(self) -> str:
        return "Psychological Profile"

    def get_prompt(self) -> str:
        return """Analyze the psychological dimensions of this person based on their notes and tweets.

Focus on:
1. **Personality patterns** - What consistent traits emerge across the content?
2. **Cognitive style** - How do they process and organize information?
3. **Defense mechanisms** - How do they protect themselves emotionally?
4. **Attachment patterns** - How do they relate to others?
5. **Motivational drivers** - What energizes them?
6. **Self-concept** - How do they see themselves?
7. **Coping strategies** - How do they handle stress?
8. **Growth trajectory** - How have they changed over time?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Note contradictions or tensions
- Identify what's notably absent

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Personality Patterns
- ## Cognitive Style
- ## Defense Mechanisms
- ## Attachment Patterns
- ## Motivational Architecture
- ## Self-Concept Analysis
- ## Coping Strategies
- ## Developmental Arc
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

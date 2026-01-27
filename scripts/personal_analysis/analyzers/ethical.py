"""Ethical analysis dimension."""

from .base import BaseAnalyzer


class EthicalAnalyzer(BaseAnalyzer):
    """Analyze ethical framework and values."""

    @property
    def dimension(self) -> str:
        return "ethical"

    @property
    def title(self) -> str:
        return "Ethical Framework"

    def get_prompt(self) -> str:
        return """Analyze the ethical dimensions of this person based on their notes and tweets.

Focus on:
1. **Stated vs enacted values** - What do they claim to value? What do their actions reveal?
2. **Moral reasoning patterns** - How do they work through ethical questions?
3. **Ethical blind spots** - Where might their ethics be inconsistent?
4. **Treatment of others** - How are other people discussed and characterized?
5. **Responsibility attribution** - How do they assign blame and credit?
6. **Justice/fairness conceptions** - What does fairness mean to them?
7. **Care ethics indicators** - How do they express care and concern?
8. **Virtue patterns** - What virtues do they embody or aspire to?

For each area:
- Provide specific evidence from the notes (use [[note-name]] wikilinks)
- Rate confidence (high/medium/low)
- Note gaps between stated values and behavior
- Identify moral tensions they may not recognize

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## Stated Values
- ## Enacted Values
- ## Value Gaps (use > [!contradiction] callout for significant gaps)
- ## Moral Reasoning Style
- ## Treatment of Others
- ## Responsibility and Blame
- ## Care and Concern
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

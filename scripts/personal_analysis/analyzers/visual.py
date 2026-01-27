"""Visual analysis dimension."""

from .base import BaseAnalyzer


class VisualAnalyzer(BaseAnalyzer):
    """Analyze visual patterns in images."""

    @property
    def dimension(self) -> str:
        return "visual"

    @property
    def title(self) -> str:
        return "Visual Patterns"

    def _uses_images(self) -> bool:
        """This analyzer requires images."""
        return True

    def get_prompt(self) -> str:
        return """Analyze the images captured by this person to understand visual patterns in their life.

The images provided are a representative sample from their collection. Analyze them alongside the text content for a complete picture.

Focus on:
1. **Subject matter** - What do they photograph? (people, places, objects, nature, etc.)
2. **Recurring visual themes** - What appears again and again?
3. **Emotional tone** - Do images convey joy, melancholy, curiosity, anxiety?
4. **Moments captured** - What kinds of moments are deemed worth preserving?
5. **Composition patterns** - Close-ups vs landscapes, centered vs off-center, etc.
6. **Notable absences** - What is never photographed that you might expect?
7. **Context clues** - What do images reveal about lifestyle, environment, relationships?
8. **Change over time** - How has visual focus shifted (if dates available)?

For each finding:
- Describe the pattern clearly
- Reference specific images when possible
- Note confidence level
- Connect to broader character insights from the text content

Structure your output with clear markdown sections:
- ## Summary (2-3 paragraph overview)
- ## What Is Captured
- ## Visual Themes
- ## Emotional Tone
- ## Moments Worth Preserving
- ## The Unseen (what's notably absent)
- ## Lifestyle and Environment Clues
- ## Connection to Text Analysis
- ## Key Insights (use > [!insight] callout)
- ## Questions This Raises"""

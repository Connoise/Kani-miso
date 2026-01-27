"""Pattern analysis dimension (covers multiple pattern types)."""

from .base import BaseAnalyzer


class PatternAnalyzer(BaseAnalyzer):
    """Base for pattern analysis dimensions."""

    def __init__(self, config, client=None, pattern_type: str = "recurring_themes"):
        """
        Initialize the pattern analyzer.

        Args:
            config: Analysis configuration
            client: Optional Anthropic client
            pattern_type: Type of pattern analysis to perform
        """
        super().__init__(config, client)
        self._pattern_type = pattern_type

    @property
    def dimension(self) -> str:
        return self._pattern_type

    @property
    def title(self) -> str:
        titles = {
            "recurring_themes": "Recurring Themes",
            "temporal_patterns": "Temporal Patterns",
            "contradiction_map": "Contradiction Map",
            "blind_spots": "Blind Spots",
            "obsessions_avoidances": "Obsessions and Avoidances",
        }
        return titles.get(self._pattern_type, self._pattern_type.replace("_", " ").title())

    def get_prompt(self) -> str:
        prompts = {
            "recurring_themes": self._recurring_themes_prompt(),
            "temporal_patterns": self._temporal_patterns_prompt(),
            "contradiction_map": self._contradiction_map_prompt(),
            "blind_spots": self._blind_spots_prompt(),
            "obsessions_avoidances": self._obsessions_avoidances_prompt(),
        }
        return prompts.get(self._pattern_type, "")

    def _recurring_themes_prompt(self) -> str:
        return """Identify concepts, ideas, or concerns that appear repeatedly across the notes and tweets.

Focus on:
1. **Frequency analysis** - What topics come up most often?
2. **Context variations** - How does the same theme appear in different contexts?
3. **Evolution of themes** - How have recurring themes changed over time?
4. **Theme interconnections** - Which themes cluster together?

For each major theme:
- Estimate how frequently it appears
- List representative examples with [[note-name]] wikilinks
- Note how the theme has evolved
- Rate its apparent importance to the creator

Structure your output:
- ## Summary
- ## Top Recurring Themes (ranked by frequency and intensity)
- ## Theme Evolution Over Time
- ## Theme Interconnections
- ## Key Insights (use > [!insight] callout)"""

    def _temporal_patterns_prompt(self) -> str:
        return """Analyze how the content changes over time.

Focus on:
1. **Mood cycles** - Are there patterns in emotional states over time?
2. **Interest evolution** - How have topics of interest shifted?
3. **Growth indicators** - What signs of development or maturation appear?
4. **Regression indicators** - Are there patterns of backsliding or repetition?
5. **Seasonal patterns** - Any cyclical patterns tied to time of year?
6. **Life event correlations** - Do major events correspond to content shifts?

For each pattern:
- Describe the temporal dimension clearly
- Provide dated evidence using [[note-name]] wikilinks
- Note confidence level based on data density
- Distinguish trends from noise

Structure your output:
- ## Summary
- ## Mood and Emotional Cycles
- ## Interest Evolution
- ## Growth Trajectory
- ## Cyclical Patterns
- ## Key Insights (use > [!insight] callout)
- ## Questions About Timing"""

    def _contradiction_map_prompt(self) -> str:
        return """Document internal contradictions WITHOUT resolving them.

Contradictions are signals, not errors. Your job is to illuminate them, not fix them.

Focus on:
1. **Stated belief vs behavior contradictions** - Where do words and actions diverge?
2. **Value conflicts** - Which stated values conflict with each other?
3. **Identity tensions** - Where does self-description contradict self-evidence?
4. **Aspiration vs reality gaps** - What is desired vs what is enacted?

For each contradiction:
- State both sides clearly and fairly
- Provide evidence for each side using [[note-name]] wikilinks
- Do NOT suggest which side is "right"
- Note if the person seems aware of the contradiction
- Use > [!contradiction] callout for each major finding

Structure your output:
- ## Summary (acknowledge that contradictions are human)
- ## Belief-Behavior Contradictions
- ## Value Conflicts
- ## Identity Tensions
- ## Aspiration-Reality Gaps
- ## Key Insights (use > [!insight] callout)"""

    def _blind_spots_prompt(self) -> str:
        return """Identify what is notably ABSENT from the content.

Sometimes what someone doesn't say is as revealing as what they do say.

Focus on:
1. **Topics never discussed** - What subjects that might be relevant are never mentioned?
2. **Emotions never expressed** - What feelings seem absent from the archive?
3. **Perspectives never considered** - What viewpoints are missing?
4. **Questions never asked** - What obvious questions are avoided?
5. **People never mentioned** - Who might be missing from the narrative?

For each blind spot:
- Describe what's absent
- Explain why its absence is notable
- Speculate carefully about possible reasons (marked as speculation)
- Note confidence level
- Use > [!question] callout for uncertain observations

Structure your output:
- ## Summary
- ## Absent Topics
- ## Unexpressed Emotions
- ## Missing Perspectives
- ## Unasked Questions
- ## Key Insights (use > [!insight] callout)"""

    def _obsessions_avoidances_prompt(self) -> str:
        return """Map patterns in what captures attention vs what is avoided.

Focus on:
1. **Disproportionate attention** - What gets more focus than seems warranted?
2. **Conspicuous avoidance** - What seems deliberately not discussed?
3. **Approach-avoidance conflicts** - What is both drawn to and pushed away?
4. **Attention shifts** - How have obsessions/avoidances changed over time?

For each pattern:
- Describe what draws or repels attention
- Quantify if possible (frequency, intensity)
- Provide evidence using [[note-name]] wikilinks
- Distinguish between healthy focus and concerning fixation
- Note approach-avoidance patterns with > [!warning] callout if significant

Structure your output:
- ## Summary
- ## What Captures Attention (potential obsessions)
- ## What Is Avoided
- ## Approach-Avoidance Conflicts
- ## Changes Over Time
- ## Key Insights (use > [!insight] callout)"""

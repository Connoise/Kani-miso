"""Relational analysis dimension (covers multiple relational types)."""

from .base import BaseAnalyzer


class RelationalAnalyzer(BaseAnalyzer):
    """Analyze how others might perceive the creator."""

    def __init__(self, config, client=None, relational_type: str = "external_perception"):
        """
        Initialize the relational analyzer.

        Args:
            config: Analysis configuration
            client: Optional Anthropic client
            relational_type: Type of relational analysis to perform
        """
        super().__init__(config, client)
        self._relational_type = relational_type

    @property
    def dimension(self) -> str:
        return self._relational_type

    @property
    def title(self) -> str:
        titles = {
            "external_perception": "External Perception",
            "communication_patterns": "Communication Patterns",
            "relationship_dynamics": "Relationship Dynamics",
            "social_presentation": "Social Presentation",
        }
        return titles.get(self._relational_type, self._relational_type.replace("_", " ").title())

    def get_prompt(self) -> str:
        prompts = {
            "external_perception": self._external_perception_prompt(),
            "communication_patterns": self._communication_patterns_prompt(),
            "relationship_dynamics": self._relationship_dynamics_prompt(),
            "social_presentation": self._social_presentation_prompt(),
        }
        return prompts.get(self._relational_type, "")

    def _external_perception_prompt(self) -> str:
        return """Analyze how others might perceive the creator based on these notes and tweets.

You're looking at private thoughts, but considering how the person comes across.

Focus on:
1. **First impressions likely generated** - What would someone think meeting this person?
2. **Strengths others would notice** - What positive qualities are evident?
3. **Weaknesses others would notice** - What negative patterns might others see?
4. **Misunderstandings likely to occur** - Where might others get the wrong idea?
5. **Trust signals and warning signs** - What would make others trust or distrust them?

For each area:
- Provide evidence from the content
- Distinguish between private self and likely presented self
- Note discrepancies between self-perception and likely external perception
- Be honest but not cruel

Structure your output:
- ## Summary
- ## Likely First Impressions
- ## Visible Strengths
- ## Visible Weaknesses
- ## Likely Misunderstandings
- ## Trust Profile
- ## Key Insights (use > [!insight] callout)"""

    def _communication_patterns_prompt(self) -> str:
        return """Analyze how ideas and feelings are expressed in the content.

Focus on:
1. **Writing style** - What characterizes their prose?
2. **Vocabulary patterns** - What words and phrases recur?
3. **Metaphor usage** - What metaphors do they reach for?
4. **Directness vs indirectness** - How direct is their communication?
5. **Emotional expression style** - How do they express feelings?
6. **Rhetorical patterns** - How do they make arguments?

For each pattern:
- Provide specific examples with [[note-name]] wikilinks
- Note what the pattern might reveal about the person
- Identify communication strengths and weaknesses
- Note any changes in style over time

Structure your output:
- ## Summary
- ## Writing Style Analysis
- ## Vocabulary Patterns
- ## Metaphors and Images
- ## Directness Spectrum
- ## Emotional Expression
- ## Key Insights (use > [!insight] callout)"""

    def _relationship_dynamics_prompt(self) -> str:
        return """Analyze patterns in how relationships are discussed in the content.

Focus on:
1. **How others are characterized** - How do they describe other people?
2. **Boundary patterns** - How do they establish and maintain boundaries?
3. **Intimacy approach** - How do they handle closeness?
4. **Conflict patterns** - How do they discuss and handle conflict?
5. **Support-seeking patterns** - How do they ask for or offer help?
6. **Relationship values** - What seems to matter most in relationships?

For each pattern:
- Provide evidence from the content
- Note both healthy and potentially concerning patterns
- Distinguish between different relationship types (romantic, family, friends)
- Use > [!warning] callout for patterns worth monitoring

Structure your output:
- ## Summary
- ## How Others Are Described
- ## Boundaries
- ## Intimacy and Closeness
- ## Conflict and Tension
- ## Giving and Receiving Support
- ## Key Insights (use > [!insight] callout)"""

    def _social_presentation_prompt(self) -> str:
        return """Analyze the difference between public and private self.

Focus on:
1. **Public vs private voice** - How do tweets differ from private notes?
2. **Performance vs authenticity** - Where does presentation seem performative?
3. **Identity construction** - How do they construct their public identity?
4. **Audience awareness** - How does audience affect expression?
5. **Vulnerability gradient** - What is shared publicly vs kept private?

For each area:
- Compare public content (tweets) with private content (notes/reflections)
- Note discrepancies and what they might mean
- Identify authentic vs performed elements
- Assess the health of the public/private balance

Structure your output:
- ## Summary
- ## Public Voice vs Private Voice
- ## Performance Elements
- ## Authentic Elements
- ## What Gets Hidden
- ## Audience Awareness
- ## Key Insights (use > [!insight] callout)"""

"""Synthesis analysis - integrates all other analyses."""

from typing import Dict
from .base import BaseAnalyzer
from ..models import AnalysisResult


class SynthesisAnalyzer(BaseAnalyzer):
    """Generate synthesis documents from previous analyses."""

    def __init__(self, config, client=None, synthesis_type: str = "unified_portrait"):
        """
        Initialize the synthesis analyzer.

        Args:
            config: Analysis configuration
            client: Optional Anthropic client
            synthesis_type: Type of synthesis to generate
        """
        super().__init__(config, client)
        self._synthesis_type = synthesis_type
        self._previous_analyses: Dict[str, AnalysisResult] = {}

    def set_previous_analyses(self, analyses: Dict[str, AnalysisResult]) -> None:
        """Set the previous analyses to synthesize from."""
        self._previous_analyses = analyses

    @property
    def dimension(self) -> str:
        return self._synthesis_type

    @property
    def title(self) -> str:
        titles = {
            "unified_portrait": "Unified Portrait",
            "hidden_truths": "Hidden Truths",
            "core_tensions": "Core Tensions",
            "essence_distillation": "Essence Distillation",
            # Guidance types
            "growth_opportunities": "Growth Opportunities",
            "shadow_work": "Shadow Work",
            "strength_amplification": "Strength Amplification",
            "warning_signs": "Warning Signs",
            "actionable_practices": "Actionable Practices",
        }
        return titles.get(self._synthesis_type, self._synthesis_type.replace("_", " ").title())

    def get_prompt(self) -> str:
        # Build context from previous analyses
        context = self._build_analysis_context()

        prompts = {
            "unified_portrait": self._unified_portrait_prompt(context),
            "hidden_truths": self._hidden_truths_prompt(context),
            "core_tensions": self._core_tensions_prompt(context),
            "essence_distillation": self._essence_distillation_prompt(context),
            # Guidance
            "growth_opportunities": self._growth_opportunities_prompt(context),
            "shadow_work": self._shadow_work_prompt(context),
            "strength_amplification": self._strength_amplification_prompt(context),
            "warning_signs": self._warning_signs_prompt(context),
            "actionable_practices": self._actionable_practices_prompt(context),
        }
        return prompts.get(self._synthesis_type, "")

    def _build_analysis_context(self) -> str:
        """Build context string from previous analyses."""
        if not self._previous_analyses:
            return "(No previous analyses available)"

        sections = ["## Previous Analysis Summaries\n"]
        for name, result in self._previous_analyses.items():
            if result.content and not result.error:
                # Extract just the summary section or first 500 chars
                content = result.content
                summary_end = content.find("## ", 10)  # Find next section after summary
                if summary_end > 0:
                    summary = content[:summary_end]
                else:
                    summary = content[:1000]
                sections.append(f"### {result.title}\n{summary}\n")

        return "\n".join(sections)

    def _unified_portrait_prompt(self, context: str) -> str:
        return f"""Integrate all the analyses into a coherent character portrait.

{context}

Now synthesize these analyses into a unified portrait. Focus on:
1. **Core identity themes** - What defines this person at their core?
2. **Central tensions** - What fundamental conflicts shape them?
3. **Defining characteristics** - What would someone need to know to understand them?
4. **Unique combination** - What makes this particular person unique?

This should be the definitive summary that captures who this person is.

Structure your output:
- ## The Unified Portrait (narrative form, 3-5 paragraphs)
- ## Core Identity Themes
- ## Central Tensions
- ## Defining Characteristics
- ## What Makes Them Unique
- ## Key Insights (use > [!insight] callout)"""

    def _hidden_truths_prompt(self, context: str) -> str:
        return f"""Based on all the analyses, identify truths about this person that they may not know or acknowledge about themselves.

{context}

Look for:
1. **Unconscious patterns** - Behaviors repeated without apparent awareness
2. **Self-deceptions** - Where stated beliefs contradict behavior
3. **Denied emotions** - Feelings that seem present but unacknowledged
4. **Hidden strengths** - Capabilities they undervalue
5. **Shadow elements** - Aspects of self that are disowned
6. **Blind spots** - Areas of consistent non-awareness
7. **Projection patterns** - What they criticize that mirrors themselves
8. **Compensations** - What behaviors mask what insecurities

Be direct and clear. State difficult findings plainly, grounded in the evidence — candor means following what the notes show, not softening it.

For each hidden truth:
- State it clearly
- Provide evidence from the analyses
- Explain why it may be hidden
- Suggest how awareness could help

Structure your output:
- ## Introduction (frame these as invitations to self-exploration)
- ## Hidden Truth 1: [Title]
- ## Hidden Truth 2: [Title]
- (continue for each major truth)
- ## Key Insights (use > [!insight] callout)"""

    def _core_tensions_prompt(self, context: str) -> str:
        return f"""Identify the fundamental internal conflicts that drive this person's behavior.

{context}

Focus on:
1. **Identity tensions** - Conflicts about who they are
2. **Value conflicts** - When values pull in opposite directions
3. **Desire conflicts** - Wanting incompatible things
4. **Role conflicts** - Tension between different roles they play

For each tension:
- Name it clearly
- Show both sides of the conflict
- Explain how it manifests in behavior
- Note if it seems productive or destructive
- Use > [!contradiction] callout for each major tension

Structure your output:
- ## Summary (tensions are not flaws)
- ## Identity Tensions
- ## Value Conflicts
- ## Desire Conflicts
- ## Role Conflicts
- ## How Tensions Interact
- ## Key Insights (use > [!insight] callout)"""

    def _essence_distillation_prompt(self, context: str) -> str:
        return f"""Extract the deepest meaning from this person's archive. What is the essence of who they are?

{context}

Answer these questions:
1. **What is this person fundamentally about?** - At their core, what drives them?
2. **What are they seeking?** - What is the fundamental quest or goal?
3. **What are they fleeing?** - What do they most want to avoid or escape?
4. **What would completion look like?** - If they achieved what they're after, what would it be?

This should be the most distilled, essential truth about this person. Write it as if you only had one page to capture who they are for someone who would never meet them.

Structure your output:
- ## The Essence (1-2 paragraphs capturing who they fundamentally are)
- ## What They Are About
- ## What They Seek
- ## What They Flee
- ## What Completion Would Look Like
- ## Final Reflection"""

    # Guidance prompts

    def _growth_opportunities_prompt(self, context: str) -> str:
        return f"""Based on all the analyses, identify areas where development is possible and beneficial.

{context}

Focus on:
1. **Skill development opportunities** - What skills could they develop?
2. **Mindset shifts to consider** - What beliefs might be limiting them?
3. **Relationship improvements** - How could relationships be enhanced?
4. **Career/life direction insights** - What directions align with their nature?

For each opportunity:
- Ground it in the analysis evidence
- Explain why it would be beneficial
- Acknowledge barriers that exist
- Suggest realistic starting points

Structure your output:
- ## Summary
- ## Skill Development
- ## Mindset Opportunities
- ## Relationship Growth
- ## Life Direction
- ## Key Insights (use > [!insight] callout)"""

    def _shadow_work_prompt(self, context: str) -> str:
        return f"""Outline unconscious patterns that would benefit from conscious examination.

{context}

Focus on:
1. **Projection patterns** - What do they criticize in others that exists in themselves?
2. **Denied aspects of self** - What parts of themselves do they reject?
3. **Triggers to explore** - What situations provoke disproportionate reactions?
4. **Integration opportunities** - How could shadow elements be constructively integrated?

Be direct but compassionate. Shadow work is challenging but valuable.

Structure your output:
- ## Introduction (what shadow work is and why it matters)
- ## Projection Patterns
- ## Denied Self
- ## Trigger Points
- ## Integration Paths
- ## Key Insights (use > [!insight] callout)"""

    def _strength_amplification_prompt(self, context: str) -> str:
        return f"""Identify how to leverage and amplify existing strengths.

{context}

Focus on:
1. **Underutilized strengths** - What strengths are present but not fully used?
2. **Strength combinations** - How could strengths be combined powerfully?
3. **Optimal environments** - What conditions let their strengths flourish?
4. **Natural gifts to develop** - What innate abilities deserve more investment?

Structure your output:
- ## Summary
- ## Underutilized Strengths
- ## Powerful Combinations
- ## Optimal Environments
- ## Gifts Worth Developing
- ## Key Insights (use > [!insight] callout)"""

    def _warning_signs_prompt(self, context: str) -> str:
        return f"""Identify patterns to monitor for potential issues.

{context}

Focus on:
1. **Stress indicators** - What signals they're under too much pressure?
2. **Regression patterns** - What behaviors indicate backsliding?
3. **Relationship warning signs** - What patterns could harm relationships?
4. **Well-being indicators** - What suggests declining mental/emotional health?

Be honest but not alarmist. These are things to watch, not diagnoses.

Structure your output:
- ## Summary
- ## Stress Indicators
- ## Regression Patterns
- ## Relationship Warning Signs
- ## Well-being Indicators
- ## What To Do If Signs Appear
- ## Key Insights (use > [!warning] callout for important items)"""

    def _actionable_practices_prompt(self, context: str) -> str:
        return f"""Provide concrete, actionable recommendations for self-improvement.

{context}

Focus on:
1. **Daily practices** - Small habits to build
2. **Weekly practices** - Regular reflections or activities
3. **Quarterly reviews** - Periodic assessments
4. **Specific exercises** - Targeted activities for growth areas
5. **Resources to explore** - Books, practices, or approaches to investigate

Make recommendations specific and actionable, not vague.

Structure your output:
- ## Summary
- ## Daily Practices
- ## Weekly Practices
- ## Quarterly Reviews
- ## Specific Exercises (organized by growth area)
- ## Recommended Resources
- ## Key Insights (use > [!insight] callout)"""

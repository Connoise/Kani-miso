"""
Cost estimation for personal analysis.

Estimates API costs and displays confirmation prompts.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import logging

from .config import (
    AnalysisConfig,
    CLAUDE_OPUS_INPUT_PRICE_PER_1M,
    CLAUDE_OPUS_OUTPUT_PRICE_PER_1M,
    CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M,
    estimate_cost,
)
from .models import CollectedContent

logger = logging.getLogger(__name__)


@dataclass
class CostEstimate:
    """Estimated costs for an analysis run."""

    # Content stats
    note_count: int
    reflection_count: int
    tweet_count: int
    image_count: int
    total_content_tokens: int

    # API call estimates
    estimated_api_calls: int
    estimated_input_tokens: int
    estimated_output_tokens: int

    # Cost estimates
    min_cost: float
    max_cost: float

    # Sampling info
    requires_sampling: bool
    sampling_ratio: float = 1.0


class CostEstimator:
    """Estimate costs for personal analysis runs."""

    # Estimated output tokens per analysis type
    OUTPUT_ESTIMATES = {
        # Core analyses
        "psychological": 8000,
        "emotional": 6000,
        "intellectual": 6000,
        "ethical": 5000,
        "spiritual": 5000,
        "philosophical": 6000,
        "visual": 4000,
        # Pattern analyses
        "recurring_themes": 6000,
        "temporal_patterns": 5000,
        "contradiction_map": 5000,
        "blind_spots": 4000,
        "obsessions_avoidances": 4000,
        # Relational analyses
        "external_perception": 5000,
        "communication_patterns": 4000,
        "relationship_dynamics": 4000,
        "social_presentation": 4000,
        # Synthesis
        "unified_portrait": 10000,
        "hidden_truths": 8000,
        "core_tensions": 6000,
        "essence_distillation": 5000,
        # Guidance
        "growth_opportunities": 6000,
        "shadow_work": 5000,
        "strength_amplification": 4000,
        "warning_signs": 4000,
        "actionable_practices": 6000,
    }

    def __init__(self, config: AnalysisConfig):
        """
        Initialize the cost estimator.

        Args:
            config: Analysis configuration
        """
        self.config = config

    def estimate(self, content: CollectedContent) -> CostEstimate:
        """
        Estimate costs for analyzing the given content.

        Args:
            content: Collected content to analyze

        Returns:
            CostEstimate with detailed breakdown
        """
        # Content token estimate
        total_content_tokens = content.total_tokens

        # Check if sampling will be needed
        requires_sampling = total_content_tokens > self.config.max_context_tokens
        sampling_ratio = 1.0
        if requires_sampling:
            sampling_ratio = self.config.max_context_tokens / total_content_tokens

        # Calculate per-call input tokens (content + prompt overhead)
        prompt_overhead = 2000  # System prompt and instructions
        per_call_input = min(total_content_tokens, self.config.max_context_tokens) + prompt_overhead

        # Calculate number of API calls based on dimensions
        api_calls = self._count_api_calls()

        # Total input tokens (content repeated for each call, but may be cached)
        total_input_tokens = per_call_input * api_calls

        # Total output tokens
        total_output_tokens = self._estimate_output_tokens()

        # Calculate cost range
        # Best case: high cache hit ratio (50%)
        min_cost, _ = estimate_cost(total_input_tokens, total_output_tokens, cache_hit_ratio=0.5)
        # Worst case: no caching
        _, max_cost = estimate_cost(total_input_tokens, total_output_tokens, cache_hit_ratio=0.0)

        return CostEstimate(
            note_count=len(content.notes),
            reflection_count=len(content.reflections),
            tweet_count=len(content.tweets),
            image_count=len(content.images),
            total_content_tokens=total_content_tokens,
            estimated_api_calls=api_calls,
            estimated_input_tokens=total_input_tokens,
            estimated_output_tokens=total_output_tokens,
            min_cost=min_cost,
            max_cost=max_cost,
            requires_sampling=requires_sampling,
            sampling_ratio=sampling_ratio,
        )

    def _count_api_calls(self) -> int:
        """Count expected API calls based on config."""
        calls = 0

        # Core analysis (parallel)
        calls += len(self.config.core_dimensions)

        # Pattern analysis (parallel)
        calls += len(self.config.pattern_dimensions)

        # Relational analysis (parallel)
        calls += len(self.config.relational_dimensions)

        # Synthesis (sequential, 4 calls)
        if self.config.generate_synthesis:
            calls += 4

        # Guidance (sequential, 5 calls)
        if self.config.generate_guidance:
            calls += 5

        return calls

    def _estimate_output_tokens(self) -> int:
        """Estimate total output tokens based on dimensions."""
        total = 0

        for dim in self.config.active_dimensions:
            total += self.OUTPUT_ESTIMATES.get(dim, 5000)

        # Synthesis outputs
        if self.config.generate_synthesis:
            for key in ["unified_portrait", "hidden_truths", "core_tensions", "essence_distillation"]:
                total += self.OUTPUT_ESTIMATES.get(key, 6000)

        # Guidance outputs
        if self.config.generate_guidance:
            for key in ["growth_opportunities", "shadow_work", "strength_amplification", "warning_signs", "actionable_practices"]:
                total += self.OUTPUT_ESTIMATES.get(key, 5000)

        return total

    def format_estimate(self, estimate: CostEstimate) -> str:
        """Format the cost estimate for display."""
        sampling_status = "Not required (under context limit)"
        if estimate.requires_sampling:
            sampling_status = f"Required (ratio: {estimate.sampling_ratio:.1%})"

        return f"""
═══════════════════════════════════════════════════════════════════
                    PERSONAL ANALYSIS - COST ESTIMATE
═══════════════════════════════════════════════════════════════════

Content detected:
  • Notes:        {estimate.note_count:,} files (~{estimate.total_content_tokens * len([1 for _ in range(estimate.note_count)]) // max(1, estimate.note_count + estimate.reflection_count + estimate.tweet_count):,} tokens)
  • Reflections:  {estimate.reflection_count:,} files
  • Tweets:       {estimate.tweet_count:,} items
  • Images:       {estimate.image_count:,} files
  ─────────────────────────────────
  Total:          ~{estimate.total_content_tokens:,} tokens

Sampling: {sampling_status}

Estimated API calls: {estimate.estimated_api_calls}
Estimated input tokens: ~{estimate.estimated_input_tokens:,} (with repetition across calls)
Estimated output tokens: ~{estimate.estimated_output_tokens:,}

───────────────────────────────────────────────────────────────────
ESTIMATED COST: ${estimate.min_cost:.2f} - ${estimate.max_cost:.2f} (depending on caching)
───────────────────────────────────────────────────────────────────
"""

    def check_budget(self, estimate: CostEstimate) -> Tuple[bool, str]:
        """
        Check if estimate is within budget.

        Args:
            estimate: Cost estimate to check

        Returns:
            Tuple of (is_within_budget, message)
        """
        if self.config.max_budget is None:
            return True, "No budget limit set"

        if estimate.max_cost <= self.config.max_budget:
            return True, f"Within budget (max ${estimate.max_cost:.2f} <= ${self.config.max_budget:.2f})"

        return False, f"Exceeds budget (max ${estimate.max_cost:.2f} > ${self.config.max_budget:.2f})"

    def prompt_confirmation(self, estimate: CostEstimate) -> bool:
        """
        Display cost estimate and prompt for confirmation.

        Args:
            estimate: Cost estimate to display

        Returns:
            True if user confirms, False otherwise
        """
        print(self.format_estimate(estimate))

        # Check budget
        within_budget, budget_msg = self.check_budget(estimate)
        if not within_budget:
            print(f"\n⚠️  WARNING: {budget_msg}")
            print("Consider using --max-budget to set a higher limit, or use --dimensions to analyze fewer dimensions.\n")

        if self.config.skip_confirmation:
            print("Proceeding automatically (--yes flag set)\n")
            return within_budget

        try:
            response = input("Proceed with analysis? [y/N]: ").strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return False

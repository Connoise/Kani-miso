"""
Cost estimation for personal analysis.

Estimates API costs and displays confirmation prompts.
Supports two-phase extraction and model tiers for accurate estimates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import logging

from .config import (
    AnalysisConfig,
    CLAUDE_OPUS_INPUT_PRICE_PER_1M,
    CLAUDE_OPUS_OUTPUT_PRICE_PER_1M,
    CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M,
    CLAUDE_SONNET_INPUT_PRICE_PER_1M,
    CLAUDE_SONNET_OUTPUT_PRICE_PER_1M,
    CLAUDE_SONNET_CACHED_INPUT_PRICE_PER_1M,
    MODEL_OPUS,
    MODEL_SONNET,
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

    # Two-phase extraction info
    uses_extraction: bool = False
    extraction_input_tokens: int = 0
    extraction_output_tokens: int = 0
    post_extraction_input_tokens: int = 0

    # Model tier info
    uses_model_tiers: bool = False
    opus_calls: int = 0
    sonnet_calls: int = 0
    opus_input_tokens: int = 0
    opus_output_tokens: int = 0
    sonnet_input_tokens: int = 0
    sonnet_output_tokens: int = 0


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

    # Extraction output is typically 15-20% of input
    EXTRACTION_COMPRESSION_RATIO = 0.15

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

        # Effective content size after sampling
        effective_content_tokens = min(total_content_tokens, self.config.max_context_tokens)
        prompt_overhead = 2000  # System prompt and instructions

        # Calculate based on extraction mode
        if self.config.use_extraction_phase:
            return self._estimate_with_extraction(
                content, effective_content_tokens, prompt_overhead,
                requires_sampling, sampling_ratio, total_content_tokens
            )
        else:
            return self._estimate_without_extraction(
                content, effective_content_tokens, prompt_overhead,
                requires_sampling, sampling_ratio, total_content_tokens
            )

    def _estimate_with_extraction(
        self,
        content: CollectedContent,
        effective_content_tokens: int,
        prompt_overhead: int,
        requires_sampling: bool,
        sampling_ratio: float,
        total_content_tokens: int,
    ) -> CostEstimate:
        """Estimate costs using two-phase extraction."""

        # Check if multipass extraction will be used
        if self.config.use_multipass_extraction and requires_sampling:
            # Multipass: estimate 2-3 extraction passes for full content
            num_passes = max(1, (total_content_tokens // self.config.multipass_chunk_tokens) + 1)
            extraction_input = total_content_tokens + (prompt_overhead * num_passes)
            extraction_output = self.config.extraction_output_tokens * num_passes
            # With multipass, we analyze all content
            sampling_ratio = 1.0
            requires_sampling = False
        else:
            # Single pass extraction
            extraction_input = effective_content_tokens + prompt_overhead
            extraction_output = self.config.extraction_output_tokens

        # Phase 2+: Analysis calls use extraction instead of full content
        # Extraction is typically 15-20% of original size
        extraction_size = int(effective_content_tokens * self.EXTRACTION_COMPRESSION_RATIO)
        per_analysis_input = extraction_size + prompt_overhead

        # Count calls and categorize by model
        all_dimensions = self._get_all_analysis_dimensions()
        opus_dims = []
        sonnet_dims = []

        for dim in all_dimensions:
            model = self.config.get_model_for_dimension(dim)
            if model == MODEL_OPUS or not self.config.use_model_tiers:
                opus_dims.append(dim)
            else:
                sonnet_dims.append(dim)

        # Calculate tokens per model tier
        opus_input = 0
        opus_output = 0
        sonnet_input = 0
        sonnet_output = 0

        for dim in opus_dims:
            opus_input += per_analysis_input
            opus_output += self.OUTPUT_ESTIMATES.get(dim, 5000)

        for dim in sonnet_dims:
            sonnet_input += per_analysis_input
            sonnet_output += self.OUTPUT_ESTIMATES.get(dim, 5000)

        # Extraction always uses Opus (or configured extraction model)
        opus_input += extraction_input
        opus_output += extraction_output

        # Total API calls
        api_calls = 1 + len(all_dimensions)  # 1 extraction + all analyses

        # Calculate costs
        min_cost, max_cost = self._calculate_tiered_cost(
            opus_input, opus_output,
            sonnet_input, sonnet_output,
        )

        return CostEstimate(
            note_count=len(content.notes),
            reflection_count=len(content.reflections),
            tweet_count=len(content.tweets),
            image_count=len(content.images),
            total_content_tokens=total_content_tokens,
            estimated_api_calls=api_calls,
            estimated_input_tokens=opus_input + sonnet_input,
            estimated_output_tokens=opus_output + sonnet_output,
            min_cost=min_cost,
            max_cost=max_cost,
            requires_sampling=requires_sampling,
            sampling_ratio=sampling_ratio,
            uses_extraction=True,
            extraction_input_tokens=extraction_input,
            extraction_output_tokens=extraction_output,
            post_extraction_input_tokens=per_analysis_input,
            uses_model_tiers=self.config.use_model_tiers,
            opus_calls=len(opus_dims) + 1,  # +1 for extraction
            sonnet_calls=len(sonnet_dims),
            opus_input_tokens=opus_input,
            opus_output_tokens=opus_output,
            sonnet_input_tokens=sonnet_input,
            sonnet_output_tokens=sonnet_output,
        )

    def _estimate_without_extraction(
        self,
        content: CollectedContent,
        effective_content_tokens: int,
        prompt_overhead: int,
        requires_sampling: bool,
        sampling_ratio: float,
        total_content_tokens: int,
    ) -> CostEstimate:
        """Estimate costs without extraction (legacy mode)."""
        per_call_input = effective_content_tokens + prompt_overhead
        api_calls = self._count_api_calls()
        total_input_tokens = per_call_input * api_calls
        total_output_tokens = self._estimate_output_tokens()

        # Calculate cost (all Opus in legacy mode)
        min_cost = self._calculate_opus_cost(total_input_tokens, total_output_tokens, cache_ratio=0.5)
        max_cost = self._calculate_opus_cost(total_input_tokens, total_output_tokens, cache_ratio=0.0)

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
            uses_extraction=False,
            uses_model_tiers=False,
        )

    def _get_all_analysis_dimensions(self) -> List[str]:
        """Get all dimensions that will be analyzed."""
        dims = list(self.config.active_dimensions)

        if self.config.generate_synthesis:
            dims.extend(["unified_portrait", "hidden_truths", "core_tensions", "essence_distillation"])

        if self.config.generate_guidance:
            dims.extend(["growth_opportunities", "shadow_work", "strength_amplification", "warning_signs", "actionable_practices"])

        return dims

    def _count_api_calls(self) -> int:
        """Count expected API calls based on config (legacy mode)."""
        calls = 0
        calls += len(self.config.core_dimensions)
        calls += len(self.config.pattern_dimensions)
        calls += len(self.config.relational_dimensions)

        if self.config.generate_synthesis:
            calls += 4
        if self.config.generate_guidance:
            calls += 5

        return calls

    def _estimate_output_tokens(self) -> int:
        """Estimate total output tokens based on dimensions."""
        total = 0

        for dim in self.config.active_dimensions:
            total += self.OUTPUT_ESTIMATES.get(dim, 5000)

        if self.config.generate_synthesis:
            for key in ["unified_portrait", "hidden_truths", "core_tensions", "essence_distillation"]:
                total += self.OUTPUT_ESTIMATES.get(key, 6000)

        if self.config.generate_guidance:
            for key in ["growth_opportunities", "shadow_work", "strength_amplification", "warning_signs", "actionable_practices"]:
                total += self.OUTPUT_ESTIMATES.get(key, 5000)

        return total

    def _calculate_tiered_cost(
        self,
        opus_input: int,
        opus_output: int,
        sonnet_input: int,
        sonnet_output: int,
    ) -> Tuple[float, float]:
        """Calculate cost with model tiers."""
        # Best case: 50% cache hit on input
        min_opus_input_cost = (
            (opus_input * 0.5 / 1_000_000) * CLAUDE_OPUS_INPUT_PRICE_PER_1M
            + (opus_input * 0.5 / 1_000_000) * CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M
        )
        min_sonnet_input_cost = (
            (sonnet_input * 0.5 / 1_000_000) * CLAUDE_SONNET_INPUT_PRICE_PER_1M
            + (sonnet_input * 0.5 / 1_000_000) * CLAUDE_SONNET_CACHED_INPUT_PRICE_PER_1M
        )

        # Worst case: no caching
        max_opus_input_cost = (opus_input / 1_000_000) * CLAUDE_OPUS_INPUT_PRICE_PER_1M
        max_sonnet_input_cost = (sonnet_input / 1_000_000) * CLAUDE_SONNET_INPUT_PRICE_PER_1M

        # Output costs (no caching)
        opus_output_cost = (opus_output / 1_000_000) * CLAUDE_OPUS_OUTPUT_PRICE_PER_1M
        sonnet_output_cost = (sonnet_output / 1_000_000) * CLAUDE_SONNET_OUTPUT_PRICE_PER_1M

        min_cost = min_opus_input_cost + min_sonnet_input_cost + opus_output_cost + sonnet_output_cost
        max_cost = max_opus_input_cost + max_sonnet_input_cost + opus_output_cost + sonnet_output_cost

        return min_cost, max_cost

    def _calculate_opus_cost(self, input_tokens: int, output_tokens: int, cache_ratio: float) -> float:
        """Calculate cost for Opus only."""
        cached = int(input_tokens * cache_ratio)
        uncached = input_tokens - cached

        input_cost = (
            (uncached / 1_000_000) * CLAUDE_OPUS_INPUT_PRICE_PER_1M
            + (cached / 1_000_000) * CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M
        )
        output_cost = (output_tokens / 1_000_000) * CLAUDE_OPUS_OUTPUT_PRICE_PER_1M

        return input_cost + output_cost

    def format_estimate(self, estimate: CostEstimate) -> str:
        """Format the cost estimate for display."""
        sampling_status = "Not required (under context limit)"
        if estimate.requires_sampling:
            sampling_status = f"Required (ratio: {estimate.sampling_ratio:.1%})"

        # Build mode description
        mode_parts = []
        if estimate.uses_extraction:
            mode_parts.append("Two-phase extraction")
        if estimate.uses_model_tiers:
            mode_parts.append("Model tiers (Opus + Sonnet)")
        mode_str = " + ".join(mode_parts) if mode_parts else "Standard (all Opus)"

        # Build detailed breakdown
        breakdown = ""
        if estimate.uses_extraction:
            breakdown += f"""
Extraction phase:
  *Input:  ~{estimate.extraction_input_tokens:,} tokens (full content)
  *Output: ~{estimate.extraction_output_tokens:,} tokens (compressed)

Analysis phase (per call):
  *Input:  ~{estimate.post_extraction_input_tokens:,} tokens (extraction)
"""

        if estimate.uses_model_tiers:
            breakdown += f"""
Model breakdown:
  *Opus calls:   {estimate.opus_calls} (~{estimate.opus_input_tokens:,} in / ~{estimate.opus_output_tokens:,} out)
  *Sonnet calls: {estimate.sonnet_calls} (~{estimate.sonnet_input_tokens:,} in / ~{estimate.sonnet_output_tokens:,} out)
"""

        return f"""
===================================================================
                    PERSONAL ANALYSIS - COST ESTIMATE
===================================================================

Content detected:
  * Notes:        {estimate.note_count:,} files
  * Reflections:  {estimate.reflection_count:,} files
  * Tweets:       {estimate.tweet_count:,} items
  * Images:       {estimate.image_count:,} files
  ---------------------------------
  Total:          ~{estimate.total_content_tokens:,} tokens

Sampling: {sampling_status}
Mode: {mode_str}
{breakdown}
Estimated API calls: {estimate.estimated_api_calls}
Estimated input tokens: ~{estimate.estimated_input_tokens:,}
Estimated output tokens: ~{estimate.estimated_output_tokens:,}

-------------------------------------------------------------------
ESTIMATED COST: ${estimate.min_cost:.2f} - ${estimate.max_cost:.2f} (depending on caching)
-------------------------------------------------------------------
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
            print(f"\n[!]  WARNING: {budget_msg}")
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

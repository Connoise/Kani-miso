"""
Configuration for personal analysis.

ASSUMPTION: User is psychologically healthy and stable
ASSUMPTION: User genuinely wants honest analysis
ASSUMPTION: User will use insights constructively
ASSUMPTION: User can handle critical feedback
ASSUMPTION: User poses no risk to self or others

These assumptions are documented in PLAN.md and must be
accepted by the user before running analysis.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Set
from datetime import datetime


# Pricing constants (as of 2026-01)
CLAUDE_OPUS_INPUT_PRICE_PER_1M = 15.00  # USD per 1M input tokens
CLAUDE_OPUS_OUTPUT_PRICE_PER_1M = 75.00  # USD per 1M output tokens
CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M = 1.50  # USD per 1M cached input tokens

CLAUDE_SONNET_INPUT_PRICE_PER_1M = 3.00  # USD per 1M input tokens
CLAUDE_SONNET_OUTPUT_PRICE_PER_1M = 15.00  # USD per 1M output tokens
CLAUDE_SONNET_CACHED_INPUT_PRICE_PER_1M = 0.30  # USD per 1M cached input tokens

# Model identifiers
MODEL_OPUS = "claude-opus-4-5-20251101"
MODEL_SONNET = "claude-sonnet-4-20250514"

# Default model tiers - which dimensions use which model
# Tier 1 (Opus): Complex synthesis, deep psychological analysis
# Tier 2 (Sonnet): Pattern detection, simpler dimensional analyses
DEFAULT_OPUS_DIMENSIONS: Set[str] = {
    "psychological",
    "emotional",
    "philosophical",
    "unified_portrait",
    "hidden_truths",
    "core_tensions",
    "essence_distillation",
    "growth_opportunities",
    "shadow_work",
}

DEFAULT_SONNET_DIMENSIONS: Set[str] = {
    "intellectual",
    "ethical",
    "spiritual",
    "visual",
    "recurring_themes",
    "temporal_patterns",
    "contradiction_map",
    "blind_spots",
    "obsessions_avoidances",
    "external_perception",
    "communication_patterns",
    "relationship_dynamics",
    "social_presentation",
    "strength_amplification",
    "warning_signs",
    "actionable_practices",
}


@dataclass
class AnalysisConfig:
    """Configuration for personal analysis runs."""

    # Paths
    notes_root: Path
    output_root: Optional[Path] = None  # Defaults to notes_root / "analysis"

    # Content selection (based on clarifications)
    include_notes: bool = True  # /notes/
    include_reflections: bool = True  # /reflections/ - treated same as notes
    include_tweets: bool = True  # /tweets/
    include_images: bool = True  # /images/ and embedded images
    include_sources: bool = False  # /sources/ - EXCLUDED (external materials)
    hub_usage: str = "metadata_only"  # "metadata_only" | "exclude"
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

    # Sampling (when content exceeds context limits)
    # Note: Token estimates are rough (~1.3x word count), so we need significant headroom
    # Actual tokenization can be 20-30% higher than estimates
    max_context_tokens: int = 150000  # Conservative limit to stay under 200K API limit
    sampling_strategy: str = "stratified_temporal"  # Only option currently
    sampling_prioritize: List[str] = field(
        default_factory=lambda: [
            "emotional_content",  # Reflections weighted higher
            "hub_connectivity",  # Well-linked notes prioritized
            "content_length",  # Longer notes have more signal
        ]
    )

    # Analysis options
    dimensions: Optional[List[str]] = None  # None = all
    generate_guidance: bool = True
    generate_synthesis: bool = True

    # Model settings
    model: str = "claude-opus-4-5-20251101"  # Default/fallback model
    thinking_budget: int = 10000
    max_output_tokens: int = 16000

    # Two-phase extraction (reduces token usage significantly)
    use_extraction_phase: bool = True  # If True, extract once then analyze extraction
    extraction_model: str = "claude-opus-4-5-20251101"  # Model for extraction phase
    extraction_output_tokens: int = 25000  # Target extraction size per pass

    # Multi-pass extraction (analyze 100% of content)
    use_multipass_extraction: bool = True  # Split content into chunks, extract from each
    # Note: Token estimates are ~40% lower than actual, so 110K estimated ≈ 155K actual
    multipass_chunk_tokens: int = 110000  # Max estimated tokens per extraction pass

    # Model tiers (use cheaper models for simpler analyses)
    use_model_tiers: bool = True  # If True, use Sonnet for simpler dimensions
    opus_dimensions: Optional[List[str]] = None  # Override DEFAULT_OPUS_DIMENSIONS
    sonnet_dimensions: Optional[List[str]] = None  # Override DEFAULT_SONNET_DIMENSIONS

    # Output options
    include_evidence_links: bool = True
    confidence_threshold: str = "low"  # Include all
    output_format: str = "timestamped"  # "timestamped" creates /analysis/YYYY-MM/

    # Cost and confirmation
    require_cost_confirmation: bool = True
    max_budget: Optional[float] = None  # None = no limit, else max USD
    skip_confirmation: bool = False  # --yes flag

    # Checkpointing
    enable_checkpoints: bool = True
    checkpoint_dir: Optional[Path] = None  # Defaults to output_root / "_meta" / "checkpoints"

    # Safety
    dry_run: bool = False  # Preview without writing or API calls

    # Rate limiting
    rate_limit_delay: int = 60  # Seconds to wait after extraction (for rate limit reset)
    sequential_mode: bool = False  # Run analyses one at a time instead of parallel

    def __post_init__(self):
        """Validate and set defaults after initialization."""
        # Convert string paths to Path objects
        if isinstance(self.notes_root, str):
            self.notes_root = Path(self.notes_root)

        if self.output_root is None:
            self.output_root = self.notes_root / "analysis"
        elif isinstance(self.output_root, str):
            self.output_root = Path(self.output_root)

        if self.checkpoint_dir is None:
            self.checkpoint_dir = self.output_root / "_meta" / "checkpoints"
        elif isinstance(self.checkpoint_dir, str):
            self.checkpoint_dir = Path(self.checkpoint_dir)

        # Validate hub_usage
        if self.hub_usage not in ("metadata_only", "exclude"):
            raise ValueError(f"hub_usage must be 'metadata_only' or 'exclude', got '{self.hub_usage}'")

        # Validate sampling_strategy
        if self.sampling_strategy != "stratified_temporal":
            raise ValueError(f"Only 'stratified_temporal' sampling is currently supported")

        # Validate confidence_threshold
        if self.confidence_threshold not in ("low", "medium", "high"):
            raise ValueError(f"confidence_threshold must be 'low', 'medium', or 'high'")

    @property
    def all_dimensions(self) -> List[str]:
        """Return list of all available analysis dimensions."""
        return [
            # Core analysis
            "psychological",
            "emotional",
            "intellectual",
            "ethical",
            "spiritual",
            "philosophical",
            "visual",
            # Pattern analysis
            "recurring_themes",
            "temporal_patterns",
            "contradiction_map",
            "blind_spots",
            "obsessions_avoidances",
            # Relational analysis
            "external_perception",
            "communication_patterns",
            "relationship_dynamics",
            "social_presentation",
        ]

    @property
    def active_dimensions(self) -> List[str]:
        """Return list of dimensions to analyze based on config."""
        if self.dimensions is None:
            return self.all_dimensions
        return [d for d in self.dimensions if d in self.all_dimensions]

    @property
    def core_dimensions(self) -> List[str]:
        """Return core analysis dimensions."""
        core = ["psychological", "emotional", "intellectual", "ethical", "spiritual", "philosophical"]
        if self.include_images:
            core.append("visual")
        return [d for d in core if d in self.active_dimensions]

    @property
    def pattern_dimensions(self) -> List[str]:
        """Return pattern analysis dimensions."""
        patterns = ["recurring_themes", "temporal_patterns", "contradiction_map", "blind_spots", "obsessions_avoidances"]
        return [d for d in patterns if d in self.active_dimensions]

    @property
    def relational_dimensions(self) -> List[str]:
        """Return relational analysis dimensions."""
        relational = ["external_perception", "communication_patterns", "relationship_dynamics", "social_presentation"]
        return [d for d in relational if d in self.active_dimensions]

    def get_output_folder(self) -> Path:
        """Get the timestamped output folder for this run."""
        if self.output_format == "timestamped":
            timestamp = datetime.now().strftime("%Y-%m")
            return self.output_root / timestamp
        return self.output_root

    def get_content_dirs(self) -> dict:
        """Get dictionary of content directories to scan."""
        dirs = {}
        if self.include_notes:
            dirs["notes"] = self.notes_root / "notes"
        if self.include_reflections:
            dirs["reflections"] = self.notes_root / "reflections"
        if self.include_tweets:
            dirs["tweets"] = self.notes_root / "tweets"
        if self.include_images:
            dirs["images"] = self.notes_root / "images"
        if self.hub_usage == "metadata_only":
            dirs["hubs"] = self.notes_root / "hubs"
        return dirs

    def get_model_for_dimension(self, dimension: str) -> str:
        """
        Get the appropriate model for a given analysis dimension.

        Args:
            dimension: The analysis dimension name

        Returns:
            Model identifier string
        """
        if not self.use_model_tiers:
            return self.model

        # Check custom overrides first
        opus_dims = set(self.opus_dimensions) if self.opus_dimensions else DEFAULT_OPUS_DIMENSIONS
        sonnet_dims = set(self.sonnet_dimensions) if self.sonnet_dimensions else DEFAULT_SONNET_DIMENSIONS

        if dimension in opus_dims:
            return MODEL_OPUS
        elif dimension in sonnet_dims:
            return MODEL_SONNET
        else:
            # Default to Opus for unknown dimensions
            return MODEL_OPUS


def estimate_cost(input_tokens: int, output_tokens: int, cache_hit_ratio: float = 0.0) -> tuple[float, float]:
    """
    Estimate API cost for given token counts.

    Args:
        input_tokens: Total input tokens
        output_tokens: Total output tokens
        cache_hit_ratio: Fraction of input tokens that may hit cache (0.0-1.0)

    Returns:
        Tuple of (min_cost, max_cost) in USD
    """
    cached_tokens = int(input_tokens * cache_hit_ratio)
    uncached_tokens = input_tokens - cached_tokens

    min_input_cost = (
        (uncached_tokens / 1_000_000) * CLAUDE_OPUS_INPUT_PRICE_PER_1M
        + (cached_tokens / 1_000_000) * CLAUDE_OPUS_CACHED_INPUT_PRICE_PER_1M
    )
    max_input_cost = (input_tokens / 1_000_000) * CLAUDE_OPUS_INPUT_PRICE_PER_1M

    output_cost = (output_tokens / 1_000_000) * CLAUDE_OPUS_OUTPUT_PRICE_PER_1M

    return (min_input_cost + output_cost, max_input_cost + output_cost)

"""
Data models for personal analysis.

These models represent the collected content and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib


@dataclass
class Note:
    """Represents a processed note from /notes/ or /reflections/."""

    path: Path
    title: str
    raw_capture: str
    created_at: datetime
    source_type: str  # "note" or "reflection"

    # Optional fields from frontmatter
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    interpretation: Optional[str] = None
    themes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    hub_links: List[str] = field(default_factory=list)

    # Metadata for sampling
    mood: Optional[str] = None
    energy: Optional[str] = None
    word_count: int = 0
    token_estimate: int = 0

    def __post_init__(self):
        """Calculate derived fields."""
        full_text = self.raw_capture + (self.interpretation or "")
        self.word_count = len(full_text.split())
        # Rough token estimate: ~0.75 tokens per word for English
        self.token_estimate = int(self.word_count * 1.3)

    @property
    def wikilink(self) -> str:
        """Return Obsidian wikilink format."""
        return f"[[{self.path.stem}]]"

    @property
    def is_emotional(self) -> bool:
        """Check if this note has emotional content markers."""
        emotional_markers = ["reflection", "feeling", "emotion", "mood", "energy"]
        text_lower = (self.raw_capture + str(self.tags)).lower()
        return any(marker in text_lower for marker in emotional_markers) or self.source_type == "reflection"


@dataclass
class Tweet:
    """Represents an imported tweet."""

    tweet_id: str
    text: str
    created_at: datetime
    path: Optional[Path] = None  # If stored as markdown

    # Tweet metadata
    is_retweet: bool = False
    is_reply: bool = False
    reply_to: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    # For analysis
    word_count: int = 0
    token_estimate: int = 0

    def __post_init__(self):
        """Calculate derived fields."""
        self.word_count = len(self.text.split())
        self.token_estimate = int(self.word_count * 1.3)


@dataclass
class Image:
    """Represents an image for visual analysis."""

    path: Path
    created_at: Optional[datetime] = None

    # Image metadata
    format: str = ""  # jpg, png, etc.
    size_bytes: int = 0
    associated_note: Optional[Path] = None  # If embedded in a note

    # For token estimation (images use fixed token counts)
    token_estimate: int = 1000  # Approximate tokens for image in Claude

    def __post_init__(self):
        """Extract metadata from path."""
        if self.path.exists():
            self.format = self.path.suffix.lower().lstrip(".")
            self.size_bytes = self.path.stat().st_size


@dataclass
class Hub:
    """Represents a hub note (metadata only, not analyzed as content)."""

    path: Path
    title: str
    status: str  # "empty", "active", etc.
    created_at: Optional[datetime] = None
    linked_notes: List[str] = field(default_factory=list)

    @property
    def wikilink(self) -> str:
        """Return Obsidian wikilink format."""
        return f"[[{self.path.stem}]]"


@dataclass
class CollectedContent:
    """Container for all collected content ready for analysis."""

    notes: List[Note] = field(default_factory=list)
    reflections: List[Note] = field(default_factory=list)
    tweets: List[Tweet] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    hubs: List[Hub] = field(default_factory=list)

    # Collection metadata
    collected_at: datetime = field(default_factory=datetime.now)
    was_sampled: bool = False
    sampling_ratio: float = 1.0
    sampling_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_notes(self) -> List[Note]:
        """Return all notes and reflections combined."""
        return self.notes + self.reflections

    @property
    def total_items(self) -> int:
        """Return total number of content items."""
        return len(self.notes) + len(self.reflections) + len(self.tweets) + len(self.images)

    @property
    def total_tokens(self) -> int:
        """Estimate total tokens across all content."""
        note_tokens = sum(n.token_estimate for n in self.notes)
        reflection_tokens = sum(r.token_estimate for r in self.reflections)
        tweet_tokens = sum(t.token_estimate for t in self.tweets)
        image_tokens = sum(i.token_estimate for i in self.images)
        return note_tokens + reflection_tokens + tweet_tokens + image_tokens

    @property
    def content_hash(self) -> str:
        """Generate hash of content for checkpoint validation."""
        content_str = ""
        for note in sorted(self.all_notes, key=lambda n: str(n.path)):
            content_str += str(note.path) + note.raw_capture[:100]
        for tweet in sorted(self.tweets, key=lambda t: t.tweet_id):
            content_str += tweet.tweet_id + tweet.text[:50]
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def get_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get earliest and latest dates in content."""
        all_dates = []
        for note in self.all_notes:
            if note.created_at:
                all_dates.append(note.created_at)
        for tweet in self.tweets:
            if tweet.created_at:
                all_dates.append(tweet.created_at)

        if not all_dates:
            return None, None
        return min(all_dates), max(all_dates)

    def create_subset(
        self,
        include_notes: bool = False,
        include_reflections: bool = False,
        include_tweets: bool = False,
        include_images: bool = False,
    ) -> "CollectedContent":
        """Create a subset of this content with only specified types."""
        return CollectedContent(
            notes=self.notes if include_notes else [],
            reflections=self.reflections if include_reflections else [],
            tweets=self.tweets if include_tweets else [],
            images=self.images if include_images else [],
            hubs=self.hubs,  # Always include hub metadata
            collected_at=self.collected_at,
        )

    def to_analysis_text(self, include_images: bool = False) -> str:
        """
        Convert all content to a single text for analysis.

        Note: Images are handled separately via Claude's vision API.
        """
        sections = []

        # Notes section
        if self.notes:
            sections.append("=== NOTES ===\n")
            for note in sorted(self.notes, key=lambda n: n.created_at):
                sections.append(f"\n--- {note.wikilink} ({note.created_at.strftime('%Y-%m-%d')}) ---")
                sections.append(note.raw_capture)
                if note.interpretation:
                    sections.append(f"\n[Interpretation]: {note.interpretation}")
                if note.themes:
                    sections.append(f"[Themes]: {', '.join(note.themes)}")

        # Reflections section
        if self.reflections:
            sections.append("\n\n=== REFLECTIONS ===\n")
            for note in sorted(self.reflections, key=lambda n: n.created_at):
                sections.append(f"\n--- {note.wikilink} ({note.created_at.strftime('%Y-%m-%d')}) ---")
                sections.append(note.raw_capture)
                if note.mood:
                    sections.append(f"[Mood]: {note.mood}")
                if note.energy:
                    sections.append(f"[Energy]: {note.energy}")

        # Tweets section
        if self.tweets:
            sections.append("\n\n=== TWEETS ===\n")
            for tweet in sorted(self.tweets, key=lambda t: t.created_at):
                date_str = tweet.created_at.strftime('%Y-%m-%d %H:%M')
                prefix = ""
                if tweet.is_retweet:
                    prefix = "[RT] "
                elif tweet.is_reply:
                    prefix = f"[Reply to @{tweet.reply_to}] " if tweet.reply_to else "[Reply] "
                sections.append(f"\n{date_str}: {prefix}{tweet.text}")

        return "\n".join(sections)


@dataclass
class Extraction:
    """
    Extracted key information from raw content.

    This is the output of phase 1 (extraction) that gets passed to
    all subsequent analysis phases instead of the full raw content.
    This dramatically reduces token usage.
    """

    # The extracted content as structured text
    content: str

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.now)
    model: str = ""
    input_tokens: int = 0  # Tokens from raw content
    output_tokens: int = 0  # Tokens in extraction

    # Source statistics
    source_notes: int = 0
    source_reflections: int = 0
    source_tweets: int = 0
    source_images: int = 0
    original_tokens: int = 0  # Original content token count

    @property
    def token_estimate(self) -> int:
        """Estimate tokens in the extraction content."""
        return int(len(self.content.split()) * 1.3)

    @property
    def compression_ratio(self) -> float:
        """Calculate how much the content was compressed."""
        if self.original_tokens == 0:
            return 1.0
        return self.token_estimate / self.original_tokens

    @classmethod
    def combine(cls, extractions: list["Extraction"]) -> "Extraction":
        """Combine multiple extractions into one."""
        if not extractions:
            return cls(content="")

        # Filter out failed extractions
        valid = [e for e in extractions if e.content and not e.content.startswith("[Extraction failed")]

        if not valid:
            return cls(content="[All extractions failed]")

        # Combine content with section headers
        combined_parts = []
        total_input = 0
        total_output = 0
        total_notes = 0
        total_reflections = 0
        total_tweets = 0
        total_images = 0
        total_original = 0

        for i, ext in enumerate(valid, 1):
            combined_parts.append(f"=== EXTRACTION PASS {i} ===\n")
            combined_parts.append(ext.content)
            combined_parts.append("\n\n")

            total_input += ext.input_tokens
            total_output += ext.output_tokens
            total_notes += ext.source_notes
            total_reflections += ext.source_reflections
            total_tweets += ext.source_tweets
            total_images += ext.source_images
            total_original += ext.original_tokens

        return cls(
            content="\n".join(combined_parts).strip(),
            model=valid[0].model if valid else "",
            input_tokens=total_input,
            output_tokens=total_output,
            source_notes=total_notes,
            source_reflections=total_reflections,
            source_tweets=total_tweets,
            source_images=total_images,
            original_tokens=total_original,
        )


@dataclass
class AnalysisResult:
    """Result from a single analysis dimension."""

    dimension: str
    title: str
    content: str  # The generated markdown content
    confidence: str  # "high", "medium", "low"

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0

    # Evidence tracking
    cited_notes: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)

    # Error handling
    error: Optional[str] = None
    is_partial: bool = False


@dataclass
class FullAnalysisResult:
    """Container for all analysis results from a complete run."""

    run_id: str
    output_folder: Path
    config_used: Dict[str, Any]

    # Results by phase
    core_analyses: Dict[str, AnalysisResult] = field(default_factory=dict)
    pattern_analyses: Dict[str, AnalysisResult] = field(default_factory=dict)
    relational_analyses: Dict[str, AnalysisResult] = field(default_factory=dict)
    synthesis_results: Dict[str, AnalysisResult] = field(default_factory=dict)
    guidance_results: Dict[str, AnalysisResult] = field(default_factory=dict)

    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0

    # Content info
    content_summary: Dict[str, int] = field(default_factory=dict)
    was_sampled: bool = False

    @property
    def is_complete(self) -> bool:
        """Check if all analyses completed successfully."""
        all_results = (
            list(self.core_analyses.values())
            + list(self.pattern_analyses.values())
            + list(self.relational_analyses.values())
            + list(self.synthesis_results.values())
            + list(self.guidance_results.values())
        )
        return all(r.error is None for r in all_results)

    @property
    def all_results(self) -> Dict[str, AnalysisResult]:
        """Return all results in a single dictionary."""
        return {
            **self.core_analyses,
            **self.pattern_analyses,
            **self.relational_analyses,
            **self.synthesis_results,
            **self.guidance_results,
        }

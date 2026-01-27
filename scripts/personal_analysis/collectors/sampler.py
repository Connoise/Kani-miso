"""
Content sampler for personal analysis.

Implements stratified temporal sampling when content exceeds context limits.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
import math

from ..models import Note, Tweet, Image, CollectedContent

logger = logging.getLogger(__name__)


@dataclass
class SamplingResult:
    """Result of content sampling."""

    content: CollectedContent
    was_sampled: bool
    sampling_ratio: float
    details: Dict[str, Any] = field(default_factory=dict)


class ContentSampler:
    """
    Sample content when it exceeds context window limits.

    Uses stratified temporal sampling to maintain representation
    across the full timeline.
    """

    def __init__(
        self,
        max_tokens: int = 180000,
        prioritize: List[str] = None,
    ):
        """
        Initialize the sampler.

        Args:
            max_tokens: Maximum tokens to include
            prioritize: List of prioritization strategies
        """
        self.max_tokens = max_tokens
        self.prioritize = prioritize or [
            "emotional_content",
            "hub_connectivity",
            "content_length",
        ]

    def sample_if_needed(self, content: CollectedContent) -> SamplingResult:
        """
        Sample content if it exceeds the token limit.

        Args:
            content: Collected content to potentially sample

        Returns:
            SamplingResult with sampled content and metadata
        """
        total_tokens = content.total_tokens

        if total_tokens <= self.max_tokens:
            logger.info(f"Content within limit ({total_tokens} <= {self.max_tokens}), no sampling needed")
            return SamplingResult(
                content=content,
                was_sampled=False,
                sampling_ratio=1.0,
            )

        logger.info(f"Content exceeds limit ({total_tokens} > {self.max_tokens}), sampling required")

        # Calculate target sampling ratio
        target_ratio = self.max_tokens / total_tokens * 0.95  # 5% buffer

        # Sample each content type
        sampled_notes = self._sample_notes(content.notes, target_ratio)
        sampled_reflections = self._sample_notes(content.reflections, target_ratio)
        sampled_tweets = self._sample_tweets(content.tweets, target_ratio)
        sampled_images = self._sample_images(content.images, target_ratio)

        # Create new CollectedContent with sampled data
        sampled_content = CollectedContent(
            notes=sampled_notes,
            reflections=sampled_reflections,
            tweets=sampled_tweets,
            images=sampled_images,
            hubs=content.hubs,  # Keep all hub metadata
            collected_at=content.collected_at,
            was_sampled=True,
            sampling_ratio=target_ratio,
            sampling_details={
                "original_tokens": total_tokens,
                "target_tokens": self.max_tokens,
                "target_ratio": target_ratio,
                "original_counts": {
                    "notes": len(content.notes),
                    "reflections": len(content.reflections),
                    "tweets": len(content.tweets),
                    "images": len(content.images),
                },
                "sampled_counts": {
                    "notes": len(sampled_notes),
                    "reflections": len(sampled_reflections),
                    "tweets": len(sampled_tweets),
                    "images": len(sampled_images),
                },
            },
        )

        actual_ratio = sampled_content.total_tokens / total_tokens
        logger.info(f"Sampled content: {sampled_content.total_tokens} tokens (ratio: {actual_ratio:.2f})")

        return SamplingResult(
            content=sampled_content,
            was_sampled=True,
            sampling_ratio=actual_ratio,
            details=sampled_content.sampling_details,
        )

    def _sample_notes(self, notes: List[Note], ratio: float) -> List[Note]:
        """
        Sample notes using stratified temporal sampling.

        Prioritizes:
        - First and last 10% chronologically
        - Notes with emotional content
        - Notes with high hub connectivity
        - Longer notes
        """
        if not notes or ratio >= 1.0:
            return notes

        # Sort by date
        sorted_notes = sorted(notes, key=lambda n: n.created_at)
        n = len(sorted_notes)

        # Calculate how many to keep
        target_count = max(1, int(n * ratio))

        # Always include first and last 10%
        first_last_count = max(1, int(n * 0.1))
        first_notes = sorted_notes[:first_last_count]
        last_notes = sorted_notes[-first_last_count:]
        guaranteed = set(id(note) for note in first_notes + last_notes)

        # Score remaining notes for prioritization
        remaining = [n for n in sorted_notes if id(n) not in guaranteed]
        scored = [(self._score_note(note), note) for note in remaining]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Calculate how many more we need
        additional_needed = target_count - len(guaranteed)

        if additional_needed > 0:
            # Use stratified sampling from scored notes
            selected_additional = self._stratified_select(
                [note for _, note in scored],
                additional_needed,
            )
        else:
            selected_additional = []

        # Combine and sort by date
        selected = list(first_notes) + list(last_notes) + selected_additional
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for note in selected:
            if id(note) not in seen:
                seen.add(id(note))
                unique.append(note)

        return sorted(unique, key=lambda n: n.created_at)

    def _score_note(self, note: Note) -> float:
        """Score a note for sampling priority."""
        score = 0.0

        # Emotional content priority
        if "emotional_content" in self.prioritize:
            if note.is_emotional:
                score += 3.0
            if note.mood or note.energy:
                score += 1.0

        # Hub connectivity priority
        if "hub_connectivity" in self.prioritize:
            score += len(note.hub_links) * 0.5

        # Content length priority
        if "content_length" in self.prioritize:
            # Log scale to prevent very long notes from dominating
            score += math.log(note.word_count + 1) * 0.3

        return score

    def _sample_tweets(self, tweets: List[Tweet], ratio: float) -> List[Tweet]:
        """Sample tweets using stratified temporal sampling."""
        if not tweets or ratio >= 1.0:
            return tweets

        sorted_tweets = sorted(tweets, key=lambda t: t.created_at)
        target_count = max(1, int(len(tweets) * ratio))

        # For tweets, use simple stratified sampling
        return self._stratified_select(sorted_tweets, target_count)

    def _sample_images(self, images: List[Image], ratio: float) -> List[Image]:
        """Sample images using stratified temporal sampling."""
        if not images or ratio >= 1.0:
            return images

        sorted_images = sorted(images, key=lambda i: i.created_at or datetime.min)
        target_count = max(1, int(len(images) * ratio))

        # For images, use simple stratified sampling
        return self._stratified_select(sorted_images, target_count)

    def _stratified_select(self, items: List, count: int) -> List:
        """
        Select items evenly distributed across the list.

        This ensures temporal coverage when items are sorted by date.
        """
        if count >= len(items):
            return items

        if count == 0:
            return []

        # Calculate step size
        step = len(items) / count
        selected = []

        for i in range(count):
            idx = int(i * step)
            selected.append(items[idx])

        return selected

    def generate_sampling_report(self, result: SamplingResult) -> str:
        """Generate a markdown report of the sampling."""
        if not result.was_sampled:
            return "No sampling was required - all content fits within context limits."

        details = result.details
        original = details.get("original_counts", {})
        sampled = details.get("sampled_counts", {})

        report = f"""## Sampling Report

### Summary

- **Original token count**: {details.get('original_tokens', 'N/A'):,}
- **Target token limit**: {details.get('target_tokens', 'N/A'):,}
- **Sampling ratio**: {result.sampling_ratio:.1%}

### Content Counts

| Type | Original | Sampled | Retained |
|------|----------|---------|----------|
| Notes | {original.get('notes', 0)} | {sampled.get('notes', 0)} | {sampled.get('notes', 0) / max(1, original.get('notes', 1)):.1%} |
| Reflections | {original.get('reflections', 0)} | {sampled.get('reflections', 0)} | {sampled.get('reflections', 0) / max(1, original.get('reflections', 1)):.1%} |
| Tweets | {original.get('tweets', 0)} | {sampled.get('tweets', 0)} | {sampled.get('tweets', 0) / max(1, original.get('tweets', 1)):.1%} |
| Images | {original.get('images', 0)} | {sampled.get('images', 0)} | {sampled.get('images', 0) / max(1, original.get('images', 1)):.1%} |

### Sampling Strategy

Stratified temporal sampling was applied with the following priorities:
1. First and last 10% of content chronologically (always included)
2. Emotional content (reflections, notes with mood/energy)
3. Notes with high hub connectivity
4. Longer notes (more information content)

### Confidence Impact

Due to sampling, analysis confidence may be affected:
- Temporal patterns may miss some fluctuations
- Rare themes might be underrepresented
- Individual insights should be verified against full archive
"""
        return report

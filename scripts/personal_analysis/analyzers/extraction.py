"""
Extraction analyzer for two-phase analysis.

This analyzer runs first and extracts key information from raw content.
Subsequent analyses use the extraction instead of the full content,
dramatically reducing token usage.
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import anthropic

from ..config import AnalysisConfig
from ..models import CollectedContent, Extraction, Image

logger = logging.getLogger(__name__)


class ExtractionAnalyzer:
    """
    Extract key information from raw content for subsequent analysis.

    This is phase 1 of the two-phase analysis approach. It processes
    all raw content once and produces a structured extraction that
    contains the essential information needed for all analysis dimensions.
    """

    EXTRACTION_SYSTEM_PROMPT = """You are an expert content analyst preparing materials for deep personal analysis.

Your task is to extract and organize the essential information from someone's personal notes, reflections, and tweets. The extraction you produce will be used by specialized analysts to understand this person's psychology, emotions, values, patterns, and relationships.

## Your Extraction Must Include

### 1. Key Facts & Biography
- Important life events mentioned
- Relationships referenced (family, friends, romantic, professional)
- Places, jobs, activities mentioned
- Timeline of significant events

### 2. Recurring Themes & Obsessions
- Topics that appear repeatedly
- Ideas the person returns to often
- Questions they keep asking
- Problems they keep encountering

### 3. Emotional Patterns
- How they express different emotions
- What triggers strong reactions
- Emotional vocabulary they use
- Mood patterns over time

### 4. Values & Beliefs
- What they explicitly value
- What they criticize or reject
- Moral positions taken
- Philosophical stances

### 5. Self-Perception
- How they describe themselves
- Self-criticism patterns
- Self-praise patterns
- Identity statements

### 6. Relationship Patterns
- How they talk about others
- Communication style
- Conflict patterns
- Connection patterns

### 7. Contradictions & Tensions
- Statements that contradict each other
- Unresolved internal conflicts
- Things they say vs. things they do
- Evolving positions on topics

### 8. Notable Quotes
- Particularly revealing statements (quote verbatim with [[note-name]] reference)
- Emotionally charged passages
- Unusual or striking phrasings
- Moments of insight or blindness

### 9. What's NOT Said
- Obvious topics that seem avoided
- Gaps in the narrative
- Questions never asked
- Emotions never expressed

### 10. Temporal Patterns
- How their thinking has evolved
- Recurring cycles
- Before/after shifts
- Seasonal or contextual patterns

## Output Format

Structure your extraction with clear markdown headers for each section above.
Use bullet points for individual items.
Always cite sources using [[note-name]] or tweet dates.
Preserve exact quotes when they're revealing.
Note confidence levels when evidence is thin.

## Critical Instructions

- Extract, don't interpret. Save analysis for the specialists.
- Preserve ambiguity. Don't resolve contradictions.
- Include unflattering material. Don't sanitize.
- Quote verbatim when possible. Don't paraphrase away meaning.
- Note what's missing. Absences are data.
- Be comprehensive. This extraction is all the analysts will see.
"""

    EXTRACTION_PROMPT = """Please extract the key information from this personal content archive.

This extraction will be used by multiple specialized analysts (psychological, emotional, ethical, pattern detection, etc.) so it must contain all the relevant raw material they'll need.

Be thorough - analysts will only see your extraction, not the original content.
Preserve the person's own words through direct quotes where revealing.
Note contradictions and tensions without resolving them.
Include unflattering material - honesty is essential.

Structure your extraction using the categories from your instructions."""

    def __init__(self, config: AnalysisConfig, client: Optional[anthropic.Anthropic] = None):
        """
        Initialize the extraction analyzer.

        Args:
            config: Analysis configuration
            client: Optional Anthropic client (created if not provided)
        """
        self.config = config
        self.client = client or anthropic.Anthropic()

    def extract(
        self,
        content: CollectedContent,
        images: Optional[List[Image]] = None,
    ) -> Extraction:
        """
        Extract key information from the collected content.

        Args:
            content: Collected content to extract from
            images: Optional list of images to include

        Returns:
            Extraction containing the key information
        """
        logger.info("Starting content extraction (phase 1)")

        try:
            # Build messages
            messages = self._build_messages(content, images)

            # Build API call kwargs (adaptive thinking + effort; see base.py)
            api_kwargs = {
                "model": self.config.extraction_model,
                "max_tokens": self.config.extraction_output_tokens,
                "system": self.EXTRACTION_SYSTEM_PROMPT,
                "messages": messages,
                "thinking": {"type": "adaptive"},
                "output_config": {"effort": self.config.effort},
            }

            # Use streaming for long operations (required by SDK for >10min requests)
            response = self._call_with_streaming(api_kwargs)

            # Extract content
            extraction_content = self._extract_content(response)

            extraction = Extraction(
                content=extraction_content,
                extracted_at=datetime.now(),
                model=self.config.extraction_model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                source_notes=len(content.notes),
                source_reflections=len(content.reflections),
                source_tweets=len(content.tweets),
                source_images=len(content.images),
                original_tokens=content.total_tokens,
            )

            logger.info(
                f"Extraction complete: {extraction.output_tokens} tokens "
                f"(compression ratio: {extraction.compression_ratio:.1%})"
            )

            return extraction

        except anthropic.APIError as e:
            logger.error(f"API error during extraction: {e}")
            # Return empty extraction on error
            return Extraction(
                content="[Extraction failed - using fallback]",
                original_tokens=content.total_tokens,
            )
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            return Extraction(
                content="[Extraction failed - using fallback]",
                original_tokens=content.total_tokens,
            )

    def _call_with_streaming(self, api_kwargs: Dict[str, Any]):
        """
        Make API call with streaming to handle long operations.

        Returns a response-like object with the accumulated content.
        """
        collected_content = []
        input_tokens = 0
        output_tokens = 0

        with self.client.messages.stream(**api_kwargs) as stream:
            for event in stream:
                pass  # Just consume the stream

            # Get the final message
            response = stream.get_final_message()

        return response

    def _build_messages(
        self,
        content: CollectedContent,
        images: Optional[List[Image]] = None,
    ) -> List[Dict[str, Any]]:
        """Build the messages array for the API call."""
        # Start with the content
        content_text = content.to_analysis_text()

        # Build the user message
        user_content = []

        # Add text content
        user_content.append({
            "type": "text",
            "text": f"""Here is the complete content archive to extract from:

{content_text}

---

{self.EXTRACTION_PROMPT}"""
        })

        # Add images if provided (limit to 20)
        if images:
            for image in images[:20]:
                image_data = self._encode_image(image.path)
                if image_data:
                    user_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": self._get_media_type(image.path),
                            "data": image_data,
                        }
                    })

        return [{"role": "user", "content": user_content}]

    def _encode_image(self, path: Path) -> Optional[str]:
        """Encode an image as base64."""
        try:
            with open(path, "rb") as f:
                return base64.standard_b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image {path}: {e}")
            return None

    def _get_media_type(self, path: Path) -> str:
        """Get the media type for an image file."""
        ext = path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(ext, "image/jpeg")

    def _extract_content(self, response) -> str:
        """Extract text content from API response."""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

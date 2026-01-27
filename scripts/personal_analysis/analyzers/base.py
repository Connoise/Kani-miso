"""
Base analyzer class for personal analysis.

All dimension analyzers inherit from this class.
"""

import base64
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import anthropic

from ..config import AnalysisConfig
from ..models import CollectedContent, AnalysisResult, Image

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Base class for all analysis dimensions.

    Subclasses must implement:
    - dimension: The dimension name
    - title: Human-readable title
    - get_prompt(): Returns the analysis prompt
    """

    # Master system prompt shared by all analyzers
    MASTER_SYSTEM_PROMPT = """You are conducting a deep personal analysis of someone's private notes and tweets.
Your role is that of a highly skilled analyst combining expertise in:
- Clinical psychology
- Emotional intelligence research
- Ethics and moral philosophy
- Spiritual and existential psychology
- Intellectual and cognitive analysis
- Social psychology and perception

## Your Mandate

You MUST:
- Be completely honest, even when findings are unflattering
- Base every claim on evidence from the notes
- Acknowledge uncertainty when it exists
- Surface patterns that may be invisible to the creator
- Identify both strengths AND weaknesses
- Look for what is NOT said as well as what is said

You MUST NOT:
- Soften findings to protect feelings
- Fill gaps with speculation presented as fact
- Withhold negative insights
- Flatter or placate
- Diagnose medical conditions (describe patterns instead)
- Use outside information not in the notes

## Assumptions

You may assume the creator:
- Is psychologically healthy and stable
- Genuinely wants honest analysis
- Will use insights for self-improvement
- Can handle critical feedback
- Poses no risk to self or others

## Evidence Standards

For each claim:
- Cite specific notes when possible (use [[note-name]] format)
- Indicate confidence level (high/medium/low)
- Distinguish between observed patterns and inferences
- Note when evidence is thin

## Output Format

Structure your analysis in clear markdown sections.
Use Obsidian-compatible formatting:
- Wikilinks: [[note-name]] for references
- Callouts: > [!insight], > [!warning], > [!question], > [!evidence], > [!contradiction]
- Clear headings and bullet points
"""

    def __init__(self, config: AnalysisConfig, client: Optional[anthropic.Anthropic] = None):
        """
        Initialize the analyzer.

        Args:
            config: Analysis configuration
            client: Optional Anthropic client (created if not provided)
        """
        self.config = config
        self.client = client or anthropic.Anthropic()

    @property
    @abstractmethod
    def dimension(self) -> str:
        """Return the dimension name (e.g., 'psychological')."""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """Return the human-readable title (e.g., 'Psychological Profile')."""
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        """Return the specific prompt for this analysis dimension."""
        pass

    def analyze(
        self,
        content: CollectedContent,
        images: Optional[List[Image]] = None,
    ) -> AnalysisResult:
        """
        Run the analysis on the given content.

        Args:
            content: Collected content to analyze
            images: Optional list of images for visual analysis

        Returns:
            AnalysisResult with the generated analysis
        """
        logger.info(f"Starting {self.dimension} analysis")

        try:
            # Build messages
            messages = self._build_messages(content, images)

            # Call Claude API
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_output_tokens,
                thinking={
                    "type": "enabled",
                    "budget_tokens": self.config.thinking_budget,
                },
                system=self.MASTER_SYSTEM_PROMPT,
                messages=messages,
            )

            # Extract content and metadata
            analysis_content = self._extract_content(response)
            thinking_tokens = self._count_thinking_tokens(response)

            # Extract cited notes and key insights
            cited_notes = self._extract_citations(analysis_content)
            key_insights = self._extract_insights(analysis_content)

            # Determine confidence
            confidence = self._determine_confidence(content, analysis_content)

            return AnalysisResult(
                dimension=self.dimension,
                title=self.title,
                content=analysis_content,
                confidence=confidence,
                generated_at=datetime.now(),
                model=self.config.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                thinking_tokens=thinking_tokens,
                cited_notes=cited_notes,
                key_insights=key_insights,
            )

        except anthropic.APIError as e:
            logger.error(f"API error during {self.dimension} analysis: {e}")
            return AnalysisResult(
                dimension=self.dimension,
                title=self.title,
                content="",
                confidence="low",
                error=str(e),
                is_partial=True,
            )
        except Exception as e:
            logger.error(f"Error during {self.dimension} analysis: {e}")
            return AnalysisResult(
                dimension=self.dimension,
                title=self.title,
                content="",
                confidence="low",
                error=str(e),
                is_partial=True,
            )

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
            "text": f"""Here is the content to analyze:

{content_text}

---

{self.get_prompt()}"""
        })

        # Add images if provided and this analyzer uses them
        if images and self._uses_images():
            for image in images[:20]:  # Limit to 20 images
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

    def _uses_images(self) -> bool:
        """Override in subclasses that analyze images."""
        return False

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

    def _count_thinking_tokens(self, response) -> int:
        """Count thinking tokens from response."""
        count = 0
        for block in response.content:
            if block.type == "thinking":
                # Estimate tokens from thinking text
                count += len(block.thinking.split()) * 1.3
        return int(count)

    def _extract_citations(self, content: str) -> List[str]:
        """Extract wikilink citations from content."""
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, content)
        # Remove duplicates while preserving order
        seen = set()
        citations = []
        for match in matches:
            link = match.split("|")[0]  # Remove alias
            if link not in seen:
                seen.add(link)
                citations.append(link)
        return citations

    def _extract_insights(self, content: str) -> List[str]:
        """Extract key insights from callout blocks."""
        insights = []

        # Match > [!insight] blocks
        pattern = r"> \[!insight\][^\n]*\n((?:>.*\n)*)"
        matches = re.findall(pattern, content)

        for match in matches:
            # Clean up the insight text
            lines = match.strip().split("\n")
            for line in lines:
                line = line.lstrip(">").strip()
                if line.startswith("-"):
                    insight = line.lstrip("-").strip()
                    if insight:
                        insights.append(insight)
                elif line:
                    insights.append(line)

        return insights[:10]  # Limit to top 10

    def _determine_confidence(self, content: CollectedContent, analysis: str) -> str:
        """Determine confidence level based on data quantity and analysis quality."""
        total_items = content.total_items

        # Low confidence if very limited data
        if total_items < 10:
            return "low"

        # Check if analysis acknowledges limitations
        low_confidence_markers = [
            "insufficient data",
            "limited evidence",
            "cannot determine",
            "unclear",
            "speculative",
        ]
        analysis_lower = analysis.lower()
        marker_count = sum(1 for marker in low_confidence_markers if marker in analysis_lower)

        if total_items < 50 or marker_count >= 3:
            return "low"
        elif total_items < 200 or marker_count >= 1:
            return "medium"
        else:
            return "high"

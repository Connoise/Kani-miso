"""
Category condenser for personal analysis.

Generates condensed category summaries from full analyses.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import anthropic

from ..config import MODEL_SONNET
from .models import CategorySummary, CATEGORY_DEFINITIONS, CategoryDef
from .analysis_reader import AnalysisDocument

logger = logging.getLogger(__name__)


# Base prompt template for category condensation
CONDENSATION_PROMPT_TEMPLATE = """You are condensing detailed personal analysis documents into a concise summary.

This summary will be read by:
- Mental health professionals (therapists, psychiatrists, counselors)
- LLMs that need context about the person
- The person themselves for self-reference

REQUIREMENTS:
1. Write in CLINICAL THIRD-PERSON voice (e.g., "The subject demonstrates..." not "You demonstrate...")
2. Preserve ALL clinically significant information - do not redact
3. Maintain evidence citations using [[note-name]] wikilink format where present
4. Flag concerning patterns clearly using "> [!warning]" callouts
5. Note confidence levels for key claims
6. Keep contradictions and tensions visible - do NOT resolve them
7. Link to relevant hub notes using [[Hub Name]] format where appropriate
8. Integrate relevant visual/image analysis insights if mentioned in source material

TARGET: Comprehensive coverage - no length limit, but every sentence should carry meaning.

CATEGORY: {category_name}
DESCRIPTION: {category_description}

SOURCE DOCUMENTS:
{source_content}

{hub_context}

Generate a condensed summary following this structure:

# {category_name}

## Overview
[Comprehensive overview capturing the essential picture for this category]

## Key Patterns
[Bullet points of the most significant patterns with evidence citations]

## Notable Insights
> [!insight] [Insight title]
> [Detailed insight with citation]

[Repeat for each major insight]

## Concerns & Flags
> [!warning] [Concern title]
> [Description of pattern to monitor, with evidence]

[Include if there are concerning patterns]

## Contradictions & Tensions
[Internal contradictions relevant to this category - do not resolve, just document]

## Confidence Assessment
[What claims are high/medium/low confidence based on evidence]

## Evidence Base
[List of primary source documents cited]

---

Generate the complete summary now:"""


class CategoryCondenser:
    """
    Generates condensed category summaries from full analyses.
    """

    def __init__(
        self,
        client: Optional[anthropic.Anthropic] = None,
        hub_names: Optional[List[str]] = None,
    ):
        """
        Initialize the condenser.

        Args:
            client: Anthropic client (created if not provided)
            hub_names: List of existing hub names for linking
        """
        self.client = client or anthropic.Anthropic()
        self.hub_names = hub_names or []

    def condense_all(
        self,
        analyses: Dict[str, AnalysisDocument],
        source_analysis: Optional[Path] = None,
    ) -> List[CategorySummary]:
        """
        Generate all category summaries.

        Args:
            analyses: Dictionary of dimension -> AnalysisDocument
            source_analysis: Path to source analysis folder

        Returns:
            List of CategorySummary objects
        """
        summaries = []

        for category in CATEGORY_DEFINITIONS:
            logger.info(f"Condensing category: {category.name}")

            # Gather source documents for this category
            source_content = self._gather_sources(analyses, category.sources)

            if not source_content:
                logger.warning(f"No source content for category {category.name}, skipping")
                continue

            # Generate condensed summary
            summary = self._condense_category(category, source_content, analyses, source_analysis)

            if summary:
                summaries.append(summary)
                logger.info(f"Generated {category.name}: {summary.word_count} words")

        return summaries

    def condense_single(
        self,
        category_id: str,
        analyses: Dict[str, AnalysisDocument],
        source_analysis: Optional[Path] = None,
    ) -> Optional[CategorySummary]:
        """
        Generate a single category summary.

        Args:
            category_id: ID of the category to condense
            analyses: Dictionary of dimension -> AnalysisDocument
            source_analysis: Path to source analysis folder

        Returns:
            CategorySummary or None if category not found
        """
        category = next((c for c in CATEGORY_DEFINITIONS if c.id == category_id), None)
        if not category:
            logger.error(f"Unknown category: {category_id}")
            return None

        source_content = self._gather_sources(analyses, category.sources)
        if not source_content:
            return None

        return self._condense_category(category, source_content, analyses, source_analysis)

    def _gather_sources(
        self,
        analyses: Dict[str, AnalysisDocument],
        source_dimensions: List[str],
    ) -> str:
        """
        Gather source content for a category.

        Args:
            analyses: Dictionary of analysis documents
            source_dimensions: List of dimensions to include

        Returns:
            Combined source content string
        """
        sections = []

        for dim in source_dimensions:
            if dim in analyses:
                doc = analyses[dim]
                section = f"\n=== {doc.title} (confidence: {doc.confidence}) ===\n{doc.content}"
                sections.append(section)

        return "\n".join(sections)

    def _condense_category(
        self,
        category: CategoryDef,
        source_content: str,
        analyses: Dict[str, AnalysisDocument],
        source_analysis: Optional[Path],
    ) -> Optional[CategorySummary]:
        """
        Use Claude to condense a single category.

        Args:
            category: Category definition
            source_content: Combined source content
            analyses: All analysis documents (for context)
            source_analysis: Path to source analysis folder

        Returns:
            CategorySummary or None on failure
        """
        # Build hub context if we have hub names
        hub_context = ""
        if self.hub_names:
            hub_context = f"AVAILABLE HUBS for linking: {', '.join(self.hub_names[:50])}"

        prompt = CONDENSATION_PROMPT_TEMPLATE.format(
            category_name=category.name,
            category_description=category.description,
            source_content=source_content,
            hub_context=hub_context,
        )

        try:
            response = self.client.messages.create(
                model=MODEL_SONNET,
                max_tokens=16000,  # No length limit, but reasonable max
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Extract hub links from the generated content
            hub_links = self._extract_hub_links(content)

            # Determine aggregate confidence from sources
            confidence = self._aggregate_confidence(analyses, category.sources)

            return CategorySummary(
                category_id=category.id,
                category_name=category.name,
                filename=category.filename,
                content=content,
                source_documents=category.sources,
                source_analysis=source_analysis,
                confidence=confidence,
                hub_links=hub_links,
            )

        except Exception as e:
            logger.error(f"Failed to condense category {category.name}: {e}")
            return None

    def _extract_hub_links(self, content: str) -> List[str]:
        """
        Extract hub links from generated content.

        Args:
            content: Generated markdown content

        Returns:
            List of hub names that were linked
        """
        # Find all [[...]] links
        links = re.findall(r'\[\[([^\]]+)\]\]', content)

        # Filter to only known hubs
        hub_links = [link for link in links if link in self.hub_names]

        return list(set(hub_links))

    def _aggregate_confidence(
        self,
        analyses: Dict[str, AnalysisDocument],
        source_dimensions: List[str],
    ) -> str:
        """
        Aggregate confidence from source documents.

        Returns the lowest confidence level found.

        Args:
            analyses: Dictionary of analysis documents
            source_dimensions: List of dimensions to check

        Returns:
            Aggregated confidence level
        """
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        min_confidence = 3

        for dim in source_dimensions:
            if dim in analyses:
                conf = analyses[dim].confidence
                if conf in confidence_order:
                    min_confidence = min(min_confidence, confidence_order[conf])

        reverse_order = {3: "high", 2: "medium", 1: "low"}
        return reverse_order.get(min_confidence, "medium")

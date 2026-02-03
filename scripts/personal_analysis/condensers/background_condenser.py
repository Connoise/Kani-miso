"""
Background condenser for personal analysis.

Extracts and generates personal background information from analysis content.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import anthropic

from .models import PersonalBackground, ALL_FIELD_SECTIONS
from .analysis_reader import AnalysisDocument

logger = logging.getLogger(__name__)


# Prompt for extracting background information from analysis content
BACKGROUND_EXTRACTION_PROMPT = """You are extracting factual biographical information from personal analysis documents.

IMPORTANT: Only extract information that is EXPLICITLY stated or VERY STRONGLY implied in the content.
Do NOT guess, infer, or make up any information that isn't clearly present.

For each field:
- If the information is clearly stated, extract it exactly
- If the information is not present, use null
- Include a confidence level (high/medium/low) only for extracted values

Content to analyze:
{content}

Extract the following information and return as JSON:

{{
  "basic_identity": {{
    "name": {{"value": "...", "confidence": "high/medium/low"}} or null,
    "date_of_birth": {{"value": "YYYY-MM-DD", "confidence": "..."}} or null,
    "gender_identity": {{"value": "...", "confidence": "..."}} or null,
    "pronouns": {{"value": "...", "confidence": "..."}} or null
  }},
  "physical": {{
    "height": {{"value": "...", "confidence": "..."}} or null,
    "weight": {{"value": "...", "confidence": "..."}} or null,
    "notable_traits": {{"value": "...", "confidence": "..."}} or null
  }},
  "location": {{
    "current_residence": {{"value": "...", "confidence": "..."}} or null,
    "hometown": {{"value": "...", "confidence": "..."}} or null,
    "places_lived": {{"value": "...", "confidence": "..."}} or null,
    "cultural_background": {{"value": "...", "confidence": "..."}} or null
  }},
  "education": {{
    "highest_level": {{"value": "...", "confidence": "..."}} or null,
    "fields_of_study": {{"value": "...", "confidence": "..."}} or null,
    "institutions": {{"value": "...", "confidence": "..."}} or null
  }},
  "employment": {{
    "current_occupation": {{"value": "...", "confidence": "..."}} or null,
    "career_summary": {{"value": "...", "confidence": "..."}} or null
  }},
  "family": {{
    "relationship_status": {{"value": "...", "confidence": "..."}} or null,
    "children": {{"value": "...", "confidence": "..."}} or null,
    "family_structure": {{"value": "...", "confidence": "..."}} or null
  }},
  "health_physical": {{
    "chronic_conditions": {{"value": "...", "confidence": "..."}} or null,
    "medications": {{"value": "...", "confidence": "..."}} or null,
    "allergies": {{"value": "...", "confidence": "..."}} or null,
    "sleep_patterns": {{"value": "...", "confidence": "..."}} or null,
    "exercise": {{"value": "...", "confidence": "..."}} or null,
    "diet": {{"value": "...", "confidence": "..."}} or null
  }},
  "health_mental": {{
    "diagnosed_conditions": {{"value": "...", "confidence": "..."}} or null,
    "current_treatment": {{"value": "...", "confidence": "..."}} or null,
    "treatment_history": {{"value": "...", "confidence": "..."}} or null,
    "substance_use": {{"value": "...", "confidence": "..."}} or null
  }},
  "interests": {{
    "interests": {{"value": "...", "confidence": "..."}} or null,
    "dislikes": {{"value": "...", "confidence": "..."}} or null
  }},
  "goals": {{
    "short_term_goals": {{"value": "...", "confidence": "..."}} or null,
    "long_term_goals": {{"value": "...", "confidence": "..."}} or null,
    "life_vision": {{"value": "...", "confidence": "..."}} or null
  }},
  "life_events": {{
    "major_events": {{"value": "...", "confidence": "..."}} or null
  }}
}}

Return ONLY the JSON object, no other text."""


class BackgroundCondenser:
    """
    Generates personal background document.

    Extracts factual information from analyses and/or prompts user.
    """

    def __init__(self, client: Optional[anthropic.Anthropic] = None):
        """
        Initialize the condenser.

        Args:
            client: Anthropic client (created if not provided)
        """
        self.client = client or anthropic.Anthropic()

    def generate(
        self,
        analyses: Dict[str, AnalysisDocument],
        source_analysis: Optional[Path] = None,
    ) -> PersonalBackground:
        """
        Generate personal background from analysis content.

        Attempts to extract what can be inferred from the analyses,
        leaving other fields empty for user verification.

        Args:
            analyses: Dictionary of dimension -> AnalysisDocument
            source_analysis: Path to source analysis folder

        Returns:
            PersonalBackground with extracted and empty fields
        """
        # Attempt to extract what can be inferred
        extracted = self._extract_from_analyses(analyses)

        # Create background with extracted + empty fields
        background = PersonalBackground(source_analysis=source_analysis)

        # Populate each section
        extracted_fields = []
        missing_fields = []

        for section_key, (section_name, fields) in ALL_FIELD_SECTIONS.items():
            section_data = {}
            section_extracted = extracted.get(section_key, {})

            for f in fields:
                if f.derived:
                    continue  # Skip derived fields

                field_data = section_extracted.get(f.key)
                if field_data and isinstance(field_data, dict) and field_data.get("value"):
                    section_data[f.key] = field_data["value"]
                    extracted_fields.append(f"{section_key}.{f.key}")
                else:
                    section_data[f.key] = None
                    if not f.optional:
                        missing_fields.append(f"{section_key}.{f.key}")

            background.set_section(section_key, section_data)

        background.extracted_fields = extracted_fields
        background.missing_fields = missing_fields

        logger.info(f"Extracted {len(extracted_fields)} fields, {len(missing_fields)} required fields missing")
        return background

    def generate_standalone(self) -> PersonalBackground:
        """
        Generate an empty background for standalone mode (no analysis).

        Returns:
            PersonalBackground with all fields empty
        """
        background = PersonalBackground()

        for section_key, (section_name, fields) in ALL_FIELD_SECTIONS.items():
            section_data = {f.key: None for f in fields if not f.derived}
            background.set_section(section_key, section_data)

        # All fields are missing
        missing_fields = []
        for section_key, (_, fields) in ALL_FIELD_SECTIONS.items():
            for f in fields:
                if not f.derived and not f.optional:
                    missing_fields.append(f"{section_key}.{f.key}")

        background.missing_fields = missing_fields
        return background

    def _extract_from_analyses(self, analyses: Dict[str, AnalysisDocument]) -> Dict[str, Any]:
        """
        Use Claude to extract factual information from analyses.

        Args:
            analyses: Dictionary of analysis documents

        Returns:
            Dictionary of extracted field values
        """
        # Combine relevant analysis content
        content = self._prepare_extraction_content(analyses)

        if not content.strip():
            logger.warning("No analysis content available for extraction")
            return {}

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{
                    "role": "user",
                    "content": BACKGROUND_EXTRACTION_PROMPT.format(content=content)
                }]
            )

            return self._parse_extraction_response(response)

        except Exception as e:
            logger.error(f"Failed to extract background information: {e}")
            return {}

    def _prepare_extraction_content(self, analyses: Dict[str, AnalysisDocument]) -> str:
        """
        Prepare content for extraction prompt.

        Prioritizes documents most likely to contain biographical information.

        Args:
            analyses: Dictionary of analysis documents

        Returns:
            Combined content string
        """
        # Priority order for extraction
        priority_dimensions = [
            "psychological",
            "unified_portrait",
            "essence_distillation",
            "relationship_dynamics",
            "emotional",
            "intellectual",
            "temporal_patterns",
        ]

        sections = []
        total_chars = 0
        max_chars = 100000  # Limit content to avoid token limits

        for dim in priority_dimensions:
            if dim in analyses and total_chars < max_chars:
                doc = analyses[dim]
                section = f"\n=== {doc.title} ===\n{doc.content}"
                sections.append(section)
                total_chars += len(section)

        # Add remaining analyses if space permits
        for dim, doc in analyses.items():
            if dim not in priority_dimensions and total_chars < max_chars:
                section = f"\n=== {doc.title} ===\n{doc.content}"
                sections.append(section)
                total_chars += len(section)

        return "\n".join(sections)

    def _parse_extraction_response(self, response) -> Dict[str, Any]:
        """
        Parse the extraction response from Claude.

        Args:
            response: Anthropic API response

        Returns:
            Dictionary of extracted values
        """
        try:
            content = response.content[0].text.strip()

            # Try to find JSON in the response
            # Sometimes Claude wraps it in markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extraction response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return {}

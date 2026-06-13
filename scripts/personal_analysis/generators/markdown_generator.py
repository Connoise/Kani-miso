"""
Obsidian-compatible markdown generator for personal analysis.

Generates formatted markdown files with proper frontmatter and callouts.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from ..models import AnalysisResult, CollectedContent, FullAnalysisResult

logger = logging.getLogger(__name__)


class ObsidianMarkdownGenerator:
    """Generate Obsidian-compatible markdown files from analysis results."""

    def __init__(self, output_folder: Path):
        """
        Initialize the generator.

        Args:
            output_folder: Root folder for output (e.g., /analysis/2026-01/)
        """
        self.output_folder = output_folder
        self._ensure_folders()

    def _ensure_folders(self) -> None:
        """Create the output folder structure."""
        folders = [
            self.output_folder,
            self.output_folder / "core-analysis",
            self.output_folder / "pattern-analysis",
            self.output_folder / "relational-analysis",
            self.output_folder / "synthesis",
            self.output_folder / "guidance",
            self.output_folder / "appendices",
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def write_analysis(self, result: AnalysisResult) -> Path:
        """
        Write an analysis result to a markdown file.

        Args:
            result: Analysis result to write

        Returns:
            Path to the written file
        """
        # Determine output path based on dimension
        folder = self._get_folder_for_dimension(result.dimension)
        filename = self._dimension_to_filename(result.dimension)
        output_path = folder / filename

        # Build frontmatter
        frontmatter = self._build_frontmatter(result)

        # Build full content
        content = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)}---

# {result.title}

{result.content}
"""

        # Write file
        output_path.write_text(content, encoding="utf-8")
        logger.info(f"Wrote analysis to {output_path}")

        return output_path

    def _get_folder_for_dimension(self, dimension: str) -> Path:
        """Map dimension to output folder."""
        core = ["psychological", "emotional", "intellectual", "ethical", "spiritual", "philosophical", "visual"]
        patterns = ["recurring_themes", "temporal_patterns", "contradiction_map", "blind_spots", "obsessions_avoidances"]
        relational = ["external_perception", "communication_patterns", "relationship_dynamics", "social_presentation"]
        synthesis = ["unified_portrait", "hidden_truths", "core_tensions", "essence_distillation"]
        guidance = ["growth_opportunities", "shadow_work", "strength_amplification", "warning_signs", "actionable_practices"]

        if dimension in core:
            return self.output_folder / "core-analysis"
        elif dimension in patterns:
            return self.output_folder / "pattern-analysis"
        elif dimension in relational:
            return self.output_folder / "relational-analysis"
        elif dimension in synthesis:
            return self.output_folder / "synthesis"
        elif dimension in guidance:
            return self.output_folder / "guidance"
        else:
            return self.output_folder

    def _dimension_to_filename(self, dimension: str) -> str:
        """Convert dimension name to filename."""
        return dimension.replace("_", "-") + ".md"

    def _build_frontmatter(self, result: AnalysisResult) -> Dict[str, Any]:
        """Build YAML frontmatter for an analysis document."""
        frontmatter = {
            "type": "analysis",
            "dimension": result.dimension,
            "generated_at": result.generated_at.isoformat(),
            "model": result.model,
            "confidence": result.confidence,
        }

        if result.input_tokens:
            frontmatter["input_tokens"] = result.input_tokens
        if result.output_tokens:
            frontmatter["output_tokens"] = result.output_tokens
        if result.error:
            frontmatter["error"] = result.error
            frontmatter["is_partial"] = True

        return frontmatter

    def write_manifest(
        self,
        content: CollectedContent,
        full_result: FullAnalysisResult,
    ) -> Path:
        """
        Write the analysis manifest file.

        Args:
            content: Collected content that was analyzed
            full_result: Complete analysis results

        Returns:
            Path to manifest file
        """
        date_start, date_end = content.get_date_range()

        manifest = {
            "run_id": full_result.run_id,
            "generated_at": datetime.now().isoformat(),
            "completed_at": full_result.completed_at.isoformat() if full_result.completed_at else None,
            "content": {
                "notes": len(content.notes),
                "reflections": len(content.reflections),
                "tweets": len(content.tweets),
                "images": len(content.images),
                "total_tokens": content.total_tokens,
                "date_range": {
                    "start": date_start.isoformat() if date_start else None,
                    "end": date_end.isoformat() if date_end else None,
                },
            },
            "sampling": {
                "was_sampled": content.was_sampled,
                "sampling_ratio": content.sampling_ratio,
                "details": content.sampling_details if content.was_sampled else None,
            },
            "analyses": {
                "completed": [name for name, r in full_result.all_results.items() if not r.error],
                "failed": [name for name, r in full_result.all_results.items() if r.error],
            },
            "cost": {
                "total_input_tokens": full_result.total_input_tokens,
                "total_output_tokens": full_result.total_output_tokens,
                "estimated_cost_usd": full_result.total_cost,
            },
        }

        manifest_path = self.output_folder / "manifest.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Wrote manifest to {manifest_path}")
        return manifest_path

    def write_evidence_citations(
        self,
        full_result: FullAnalysisResult,
    ) -> Path:
        """
        Write the evidence citations document.

        Args:
            full_result: Complete analysis results

        Returns:
            Path to evidence citations file
        """
        # Collect all citations from all analyses
        all_citations: Dict[str, List[str]] = {}

        for dimension, result in full_result.all_results.items():
            if result.cited_notes:
                all_citations[result.title] = result.cited_notes

        content = """---
type: appendix
title: Evidence Citations
generated_at: {date}
---

# Evidence Citations

This document lists all notes cited across the analysis documents.

""".format(date=datetime.now().isoformat())

        for title, citations in all_citations.items():
            content += f"## {title}\n\n"
            for citation in citations:
                content += f"- [[{citation}]]\n"
            content += "\n"

        output_path = self.output_folder / "appendices" / "evidence-citations.md"
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote evidence citations to {output_path}")
        return output_path

    def write_confidence_levels(
        self,
        full_result: FullAnalysisResult,
    ) -> Path:
        """
        Write the confidence levels document.

        Args:
            full_result: Complete analysis results

        Returns:
            Path to confidence levels file
        """
        content = """---
type: appendix
title: Confidence Levels
generated_at: {date}
---

# Confidence Levels

This document summarizes the confidence levels for each analysis.

| Analysis | Confidence | Notes |
|----------|------------|-------|
""".format(date=datetime.now().isoformat())

        for dimension, result in full_result.all_results.items():
            notes = ""
            if result.error:
                notes = f"Error: {result.error}"
            elif result.is_partial:
                notes = "Partial analysis"

            content += f"| {result.title} | {result.confidence} | {notes} |\n"

        content += """

## Confidence Level Definitions

- **High**: Strong evidence from multiple sources, clear patterns
- **Medium**: Moderate evidence, some uncertainty in interpretation
- **Low**: Limited evidence, significant uncertainty, or partial analysis

## Factors Affecting Confidence

Confidence is determined by:
1. Amount of relevant data available
2. Clarity of patterns observed
3. Consistency across different content types
4. Presence of contradicting evidence
"""

        output_path = self.output_folder / "appendices" / "confidence-levels.md"
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote confidence levels to {output_path}")
        return output_path

    def write_methodology(self, config_used: Dict[str, Any]) -> Path:
        """
        Write the methodology notes document.

        Args:
            config_used: Configuration used for this analysis

        Returns:
            Path to methodology file
        """
        content = f"""---
type: appendix
title: Methodology Notes
generated_at: {datetime.now().isoformat()}
---

# Methodology Notes

## Analysis Approach

This analysis was generated using Claude Opus (the current Opus model),
with adaptive thinking enabled for deeper reasoning.

### Core Principles

1. **Evidence-based claims**: All assertions link to source notes
2. **Acknowledged uncertainty**: Confidence levels explicitly stated
3. **Preserved contradictions**: Tensions noted, not resolved
4. **Honest assessment**: No softening of difficult findings

### Analysis Phases

1. **Core Analysis**: Psychological, emotional, intellectual, ethical, spiritual, philosophical, visual
2. **Pattern Analysis**: Recurring themes, temporal patterns, contradictions, blind spots, obsessions
3. **Relational Analysis**: External perception, communication, relationships, social presentation
4. **Synthesis**: Unified portrait, hidden truths, core tensions, essence
5. **Guidance**: Growth opportunities, shadow work, strengths, warnings, practices

## Configuration Used

```yaml
{yaml.dump(config_used, default_flow_style=False)}
```

## Limitations

This analysis is limited by:
1. Only the content provided was analyzed
2. Temporal gaps in the data affect pattern detection
3. Written content may not fully reflect the person
4. Analysis is interpretation, not objective truth
5. The model has knowledge limitations and biases

## How to Use This Analysis

1. Read with openness, not defensiveness
2. Verify insights against your own experience
3. Treat contradictions as invitations to explore
4. Use guidance as suggestions, not prescriptions
5. Return to this analysis periodically as you grow
"""

        output_path = self.output_folder / "appendices" / "methodology-notes.md"
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote methodology to {output_path}")
        return output_path

    def write_limitations(self) -> Path:
        """
        Write the limitations document.

        Returns:
            Path to limitations file
        """
        content = f"""---
type: appendix
title: Limitations
generated_at: {datetime.now().isoformat()}
---

# What This Analysis Cannot Determine

This document acknowledges the inherent limitations of AI-based personal analysis.

## Data Limitations

- **Incomplete picture**: Only analyzed content that was provided
- **Temporal gaps**: Missing time periods may hide important patterns
- **Format bias**: Written content differs from spoken or behavioral expression
- **Selection bias**: What gets written down is not random

## Methodological Limitations

- **Interpretation, not truth**: All findings are interpretations, not facts
- **Pattern recognition limits**: Some patterns may be noise, others may be missed
- **Temporal causation**: Correlation in timing doesn't prove causation
- **Context loss**: Notes removed from their context may be misinterpreted

## Model Limitations

- **Knowledge cutoff**: The model has a training cutoff date
- **Cultural bias**: Training data reflects certain perspectives more than others
- **Projection risk**: Model may project patterns that aren't there
- **Nuance loss**: Complex human experience may be oversimplified

## What Cannot Be Known

This analysis cannot:
- Diagnose medical or psychological conditions
- Predict future behavior with certainty
- Know what was deliberately not written
- Understand fully private or embodied experience
- Replace professional assessment when needed

## Recommendation

If any findings cause significant concern, consider discussing them with:
- A trusted friend or mentor
- A licensed therapist or counselor
- A relevant professional
"""

        output_path = self.output_folder / "appendices" / "limitations.md"
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote limitations to {output_path}")
        return output_path

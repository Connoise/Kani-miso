"""
Profile generator for condensed analysis output.

Generates Obsidian-compatible markdown files for the person profile.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from .models import PersonalBackground, CategorySummary, ALL_FIELD_SECTIONS

logger = logging.getLogger(__name__)


class ProfileGenerator:
    """
    Generates Obsidian-compatible markdown files for person profile.
    """

    def __init__(self, output_folder: Path):
        """
        Initialize the generator.

        Args:
            output_folder: Path to output folder (e.g., /notes/person-profile/2026-02/)
        """
        self.output_folder = output_folder

    def write_all(
        self,
        background: PersonalBackground,
        summaries: List[CategorySummary],
        source_analysis: Optional[Path] = None,
    ) -> List[Path]:
        """
        Write all profile documents.

        Args:
            background: Verified personal background
            summaries: List of category summaries
            source_analysis: Path to source analysis folder

        Returns:
            List of paths to written files
        """
        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)

        written_files = []
        timestamp = datetime.now().strftime("%Y-%m-%d")

        # Write background document
        bg_path = self._write_background(background, timestamp, source_analysis)
        written_files.append(bg_path)

        # Write each category summary
        for summary in summaries:
            summary_path = self._write_summary(summary, timestamp)
            written_files.append(summary_path)

        # Write manifest
        manifest_path = self._write_manifest(background, summaries, source_analysis)
        written_files.append(manifest_path)

        return written_files

    def _write_background(
        self,
        background: PersonalBackground,
        timestamp: str,
        source_analysis: Optional[Path],
    ) -> Path:
        """
        Write the personal background document.

        Args:
            background: PersonalBackground with verified values
            timestamp: Date string for filename
            source_analysis: Path to source analysis folder

        Returns:
            Path to written file
        """
        filename = f"00-personal-background--{timestamp}.md"
        filepath = self.output_folder / filename

        # Build frontmatter
        frontmatter = {
            "type": "person-profile",
            "category": "background",
            "created_at": background.created_at.isoformat() if background.created_at else datetime.now().isoformat(),
            "last_verified": background.last_verified.isoformat() if background.last_verified else None,
            "verification_status": background.verification_status,
            "source_analysis": str(source_analysis) if source_analysis else None,
        }

        # Build content
        content_parts = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False).strip(),
            "---",
            "",
            "# Personal Background",
            "",
            f"> This document contains factual biographical information verified by the subject.",
            f"> Last verified: {background.last_verified.strftime('%Y-%m-%d %H:%M') if background.last_verified else 'Not verified'}",
            "",
        ]

        # Add each section
        for section_key, (section_name, fields) in ALL_FIELD_SECTIONS.items():
            content_parts.append(f"## {section_name}")
            section_data = background.get_section(section_key)

            for field_def in fields:
                value = section_data.get(field_def.key, "Not provided")
                if value is None:
                    value = "Not provided"

                # Format multiline values
                if field_def.multiline and value != "Not provided" and "\n" in str(value):
                    content_parts.append(f"### {field_def.label}")
                    content_parts.append(str(value))
                else:
                    content_parts.append(f"- **{field_def.label}:** {value}")

            content_parts.append("")  # Blank line between sections

        # Add verification log
        content_parts.extend([
            "---",
            "",
            "## Verification Log",
            "",
            "| Field | Status | Notes |",
            "|-------|--------|-------|",
        ])

        filled, total = background.count_filled_fields()
        content_parts.append(f"| Total Fields | {filled}/{total} filled | |")

        for field_path in background.extracted_fields[:10]:  # Show first 10 extracted
            content_parts.append(f"| {field_path} | Extracted | From analysis |")

        content = "\n".join(content_parts)
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Wrote background to: {filepath}")
        return filepath

    def _write_summary(self, summary: CategorySummary, timestamp: str) -> Path:
        """
        Write a category summary document.

        Args:
            summary: CategorySummary to write
            timestamp: Date string for filename

        Returns:
            Path to written file
        """
        filename = f"{summary.filename}--{timestamp}.md"
        filepath = self.output_folder / filename

        # Build frontmatter
        frontmatter = {
            "type": "person-profile",
            "category": summary.category_id,
            "created_at": summary.generated_at.isoformat() if summary.generated_at else datetime.now().isoformat(),
            "source_analysis": str(summary.source_analysis) if summary.source_analysis else None,
            "source_documents": summary.source_documents,
            "confidence": summary.confidence,
            "word_count": summary.word_count,
        }

        if summary.hub_links:
            frontmatter["hub_links"] = summary.hub_links

        # Build content
        content_parts = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False).strip(),
            "---",
            "",
            summary.content,
        ]

        content = "\n".join(content_parts)
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Wrote summary to: {filepath}")
        return filepath

    def _write_manifest(
        self,
        background: PersonalBackground,
        summaries: List[CategorySummary],
        source_analysis: Optional[Path],
    ) -> Path:
        """
        Write the condensation manifest.

        Args:
            background: Personal background
            summaries: List of category summaries
            source_analysis: Path to source analysis folder

        Returns:
            Path to manifest file
        """
        meta_folder = self.output_folder / "_meta"
        meta_folder.mkdir(exist_ok=True)

        manifest_path = meta_folder / "condensation-manifest.yaml"

        filled, total = background.count_filled_fields()

        manifest = {
            "generated_at": datetime.now().isoformat(),
            "source_analysis": str(source_analysis) if source_analysis else None,
            "background": {
                "verification_status": background.verification_status,
                "fields_filled": filled,
                "fields_total": total,
                "extracted_fields": len(background.extracted_fields),
            },
            "summaries": [
                {
                    "category": s.category_id,
                    "name": s.category_name,
                    "filename": s.filename,
                    "word_count": s.word_count,
                    "confidence": s.confidence,
                    "source_documents": s.source_documents,
                    "hub_links": s.hub_links,
                }
                for s in summaries
            ],
            "statistics": {
                "total_files": 1 + len(summaries),
                "total_words": sum(s.word_count for s in summaries),
                "categories_generated": len(summaries),
            },
        }

        manifest_path.write_text(yaml.dump(manifest, default_flow_style=False), encoding="utf-8")

        logger.info(f"Wrote manifest to: {manifest_path}")
        return manifest_path


def create_latest_symlink(profile_root: Path, target_folder: Path) -> None:
    """
    Create or update the 'latest' symlink.

    Args:
        profile_root: Root person-profile folder
        target_folder: Folder to link to
    """
    latest_link = profile_root / "latest"

    # Remove existing symlink if present
    if latest_link.is_symlink():
        latest_link.unlink()
    elif latest_link.exists():
        logger.warning(f"'latest' exists but is not a symlink: {latest_link}")
        return

    # Create relative symlink
    try:
        relative_target = target_folder.relative_to(profile_root)
        latest_link.symlink_to(relative_target)
        logger.info(f"Created symlink: latest -> {relative_target}")
    except Exception as e:
        logger.error(f"Failed to create latest symlink: {e}")

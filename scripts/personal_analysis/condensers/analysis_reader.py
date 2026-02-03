"""
Analysis reader for condensation.

Reads existing analysis documents from the analysis folder.
"""

import re
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisDocument:
    """Represents a single analysis document."""

    path: Path
    dimension: str
    title: str
    content: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    confidence: str = "medium"
    generated_at: Optional[datetime] = None

    @property
    def word_count(self) -> int:
        """Return word count of content."""
        return len(self.content.split())


class AnalysisReader:
    """Reads and parses existing analysis documents."""

    # Mapping from folder names to dimension prefixes
    FOLDER_MAPPINGS = {
        "core-analysis": {
            "psychological-profile": "psychological",
            "emotional-landscape": "emotional",
            "intellectual-portrait": "intellectual",
            "ethical-framework": "ethical",
            "spiritual-dimensions": "spiritual",
            "philosophical-orientation": "philosophical",
            "visual-patterns": "visual",
        },
        "pattern-analysis": {
            "recurring-themes": "recurring_themes",
            "temporal-patterns": "temporal_patterns",
            "contradiction-map": "contradiction_map",
            "blind-spots": "blind_spots",
            "obsessions-and-avoidances": "obsessions_avoidances",
        },
        "relational-analysis": {
            "external-perception": "external_perception",
            "communication-patterns": "communication_patterns",
            "relationship-dynamics": "relationship_dynamics",
            "social-presentation": "social_presentation",
        },
        "synthesis": {
            "unified-portrait": "unified_portrait",
            "hidden-truths": "hidden_truths",
            "core-tensions": "core_tensions",
            "essence-distillation": "essence_distillation",
        },
        "guidance": {
            "growth-opportunities": "growth_opportunities",
            "shadow-work": "shadow_work",
            "strength-amplification": "strength_amplification",
            "warning-signs": "warning_signs",
            "actionable-practices": "actionable_practices",
        },
    }

    def __init__(self, analysis_folder: Path):
        """
        Initialize the reader.

        Args:
            analysis_folder: Path to a specific analysis run folder (e.g., /analysis/2026-01/)
        """
        self.analysis_folder = analysis_folder

    def read_all(self) -> Dict[str, AnalysisDocument]:
        """
        Read all analysis documents from the folder.

        Returns:
            Dictionary mapping dimension names to AnalysisDocument objects
        """
        documents = {}

        for subfolder, file_mappings in self.FOLDER_MAPPINGS.items():
            folder = self.analysis_folder / subfolder
            if not folder.exists():
                logger.warning(f"Analysis subfolder not found: {folder}")
                continue

            for md_file in folder.glob("*.md"):
                doc = self._parse_document(md_file, file_mappings)
                if doc:
                    documents[doc.dimension] = doc
                    logger.debug(f"Loaded analysis: {doc.dimension}")

        logger.info(f"Loaded {len(documents)} analysis documents")
        return documents

    def read_manifest(self) -> Dict[str, Any]:
        """
        Read the analysis manifest for metadata.

        Returns:
            Dictionary of manifest data, or empty dict if not found
        """
        manifest_path = self.analysis_folder / "manifest.yaml"
        if manifest_path.exists():
            try:
                return yaml.safe_load(manifest_path.read_text())
            except Exception as e:
                logger.error(f"Failed to read manifest: {e}")
        return {}

    def get_analysis_date(self) -> Optional[datetime]:
        """
        Get the date of the analysis from the folder name or manifest.

        Returns:
            datetime or None
        """
        # Try to parse from folder name (YYYY-MM format)
        folder_name = self.analysis_folder.name
        try:
            return datetime.strptime(folder_name, "%Y-%m")
        except ValueError:
            pass

        # Try manifest
        manifest = self.read_manifest()
        if "generated_at" in manifest:
            try:
                return datetime.fromisoformat(manifest["generated_at"])
            except (ValueError, TypeError):
                pass

        return None

    def _parse_document(
        self,
        path: Path,
        file_mappings: Dict[str, str]
    ) -> Optional[AnalysisDocument]:
        """
        Parse a single analysis document.

        Args:
            path: Path to the markdown file
            file_mappings: Mapping from filename stems to dimension names

        Returns:
            AnalysisDocument or None if parsing fails
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
            return None

        # Determine dimension from filename
        stem = path.stem
        dimension = file_mappings.get(stem)
        if not dimension:
            # Try to infer from filename
            dimension = stem.replace("-", "_")
            logger.debug(f"Inferred dimension '{dimension}' from filename '{stem}'")

        # Parse frontmatter and content
        frontmatter, body = self._split_frontmatter(content)

        # Extract title from first heading or filename
        title = self._extract_title(body, stem)

        # Get confidence from frontmatter
        confidence = frontmatter.get("confidence", "medium")

        # Get generated_at
        generated_at = None
        if "generated_at" in frontmatter:
            try:
                generated_at = datetime.fromisoformat(frontmatter["generated_at"])
            except (ValueError, TypeError):
                pass

        return AnalysisDocument(
            path=path,
            dimension=dimension,
            title=title,
            content=body,
            frontmatter=frontmatter,
            confidence=confidence,
            generated_at=generated_at,
        )

    def _split_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Split markdown content into frontmatter and body.

        Args:
            content: Full markdown content

        Returns:
            Tuple of (frontmatter dict, body string)
        """
        if not content.startswith("---"):
            return {}, content

        # Find the closing ---
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            if not isinstance(frontmatter, dict):
                frontmatter = {}
        except yaml.YAMLError:
            frontmatter = {}

        body = parts[2].strip()
        return frontmatter, body

    def _extract_title(self, body: str, fallback: str) -> str:
        """
        Extract title from markdown body.

        Args:
            body: Markdown body content
            fallback: Fallback title if none found

        Returns:
            Title string
        """
        # Look for first H1
        match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Use fallback (convert dashes to spaces and title case)
        return fallback.replace("-", " ").title()


def find_latest_analysis(analysis_root: Path) -> Optional[Path]:
    """
    Find the most recent analysis folder.

    Args:
        analysis_root: Root analysis folder (e.g., /analysis/)

    Returns:
        Path to the most recent analysis folder, or None
    """
    if not analysis_root.exists():
        return None

    # Check for 'latest' symlink first
    latest_link = analysis_root / "latest"
    if latest_link.is_symlink() and latest_link.resolve().exists():
        return latest_link.resolve()

    # Find all YYYY-MM folders
    analysis_folders = []
    for item in analysis_root.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            try:
                # Try to parse as YYYY-MM
                datetime.strptime(item.name, "%Y-%m")
                analysis_folders.append(item)
            except ValueError:
                continue

    if not analysis_folders:
        return None

    # Sort by name (YYYY-MM format sorts chronologically)
    analysis_folders.sort(key=lambda p: p.name, reverse=True)
    return analysis_folders[0]

"""
Main orchestrator for analysis condensation.

Coordinates the full condensation pipeline from reading analyses
through generating compact profile documents.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import anthropic

from .condensers import (
    AnalysisReader,
    BackgroundCondenser,
    CategoryCondenser,
    UserVerifier,
    ProfileGenerator,
    PersonalBackground,
    CategorySummary,
    CondensationResult,
)
from .condensers.analysis_reader import find_latest_analysis
from .condensers.profile_generator import create_latest_symlink
from .collectors import HubCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AnalysisCondenser:
    """
    Main orchestrator for condensing analysis output into profile documents.

    Coordinates:
    1. Reading existing analysis documents
    2. Extracting/verifying personal background
    3. Generating category summaries
    4. Writing output files
    """

    def __init__(
        self,
        notes_root: Path,
        analysis_folder: Optional[Path] = None,
        output_folder: Optional[Path] = None,
    ):
        """
        Initialize the condenser.

        Args:
            notes_root: Root of the Obsidian vault
            analysis_folder: Specific analysis folder to condense (uses latest if None)
            output_folder: Output folder for profile documents (auto-generated if None)
        """
        self.notes_root = notes_root
        self.client = anthropic.Anthropic()

        # Find analysis folder
        if analysis_folder:
            self.analysis_folder = analysis_folder
        else:
            analysis_root = notes_root / "analysis"
            self.analysis_folder = find_latest_analysis(analysis_root)

        # Set up output folder
        if output_folder:
            self.output_folder = output_folder
        else:
            # Create timestamped folder: /notes/person-profile/YYYY-MM/
            profile_root = notes_root / "notes" / "person-profile"
            month_folder = datetime.now().strftime("%Y-%m")
            self.output_folder = profile_root / month_folder

        self.profile_root = notes_root / "notes" / "person-profile"

        # Load hub names for linking
        self.hub_names = self._load_hub_names()

    def run(
        self,
        interactive: bool = True,
        background_only: bool = False,
        categories: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> Optional[CondensationResult]:
        """
        Execute the full condensation pipeline.

        Args:
            interactive: If True, prompt user to verify background info
            background_only: If True, only generate/verify background document
            categories: Specific categories to generate (None = all)
            dry_run: If True, preview without writing files

        Returns:
            CondensationResult or None if cancelled/failed
        """
        run_id = datetime.now().isoformat()

        # Print header
        self._print_header(dry_run)

        # Check if analysis folder exists
        if self.analysis_folder and not self.analysis_folder.exists():
            print(f"\n[X] Analysis folder not found: {self.analysis_folder}")
            print("    Run the personal analysis first, or use --standalone mode.")
            return None

        # Phase 1: Read analyses (if available)
        analyses = {}
        if self.analysis_folder and self.analysis_folder.exists():
            print("\n[1] Reading analysis documents...")
            reader = AnalysisReader(self.analysis_folder)
            analyses = reader.read_all()
            print(f"    Loaded {len(analyses)} analysis documents")
        else:
            print("\n[1] No analysis folder - running in standalone mode")

        # Phase 2: Generate background
        print("\n[2] Generating personal background...")
        background = self._generate_background(analyses)

        # Phase 3: Verify background (if interactive)
        if interactive:
            print("\n[3] Verifying background information...")
            verifier = UserVerifier()
            background = verifier.verify(background)
        else:
            background.verification_status = "unverified"
            print("\n[3] Skipping verification (non-interactive mode)")

        # Phase 4: Generate category summaries (unless background_only)
        summaries = []
        if not background_only and analyses:
            print("\n[4] Generating category summaries...")
            summaries = self._generate_summaries(analyses, categories)
            print(f"    Generated {len(summaries)} category summaries")
        elif background_only:
            print("\n[4] Skipping summaries (background-only mode)")
        else:
            print("\n[4] Skipping summaries (no analysis available)")

        # Phase 5: Write outputs (unless dry run)
        if dry_run:
            print("\n[5] DRY RUN - would write to:")
            print(f"    {self.output_folder}")
            return None

        print("\n[5] Writing output files...")
        result = self._write_outputs(background, summaries, run_id)

        # Create latest symlink
        create_latest_symlink(self.profile_root, self.output_folder)

        self._print_summary(result)
        return result

    def run_standalone(self, interactive: bool = True) -> Optional[CondensationResult]:
        """
        Run in standalone mode (no analysis required).

        Only generates the personal background document.

        Args:
            interactive: If True, prompt user for all information

        Returns:
            CondensationResult or None if cancelled
        """
        run_id = datetime.now().isoformat()

        print("\n" + "=" * 60)
        print("       STANDALONE BACKGROUND GENERATION")
        print("=" * 60)
        print("\nThis will create a personal background document without")
        print("requiring a full analysis. All fields will need to be")
        print("entered manually.\n")

        # Generate empty background
        condenser = BackgroundCondenser(self.client)
        background = condenser.generate_standalone()

        # Verify with user
        if interactive:
            verifier = UserVerifier()
            background = verifier.verify(background)
        else:
            background.verification_status = "unverified"

        # Write output
        result = self._write_outputs(background, [], run_id)

        self._print_summary(result)
        return result

    def _generate_background(self, analyses: dict) -> PersonalBackground:
        """Generate personal background from analyses."""
        condenser = BackgroundCondenser(self.client)

        if analyses:
            return condenser.generate(analyses, self.analysis_folder)
        else:
            return condenser.generate_standalone()

    def _generate_summaries(
        self,
        analyses: dict,
        categories: Optional[List[str]] = None,
    ) -> List[CategorySummary]:
        """Generate category summaries."""
        condenser = CategoryCondenser(self.client, self.hub_names)

        if categories:
            # Generate only specified categories
            summaries = []
            for cat_id in categories:
                summary = condenser.condense_single(cat_id, analyses, self.analysis_folder)
                if summary:
                    summaries.append(summary)
            return summaries
        else:
            # Generate all categories
            return condenser.condense_all(analyses, self.analysis_folder)

    def _write_outputs(
        self,
        background: PersonalBackground,
        summaries: List[CategorySummary],
        run_id: str,
    ) -> CondensationResult:
        """Write all output files."""
        generator = ProfileGenerator(self.output_folder)

        written_files = generator.write_all(
            background,
            summaries,
            self.analysis_folder,
        )

        return CondensationResult(
            output_folder=self.output_folder,
            background=background,
            summaries=summaries,
            run_id=run_id,
            source_analysis=self.analysis_folder,
        )

    def _load_hub_names(self) -> List[str]:
        """Load hub names for linking."""
        hubs_folder = self.notes_root / "hubs"
        if not hubs_folder.exists():
            return []

        try:
            collector = HubCollector(hubs_folder)
            hubs = collector.collect_all()
            return [h.title for h in hubs]
        except Exception as e:
            logger.warning(f"Failed to load hub names: {e}")
            return []

    def _print_header(self, dry_run: bool) -> None:
        """Print the condensation header."""
        print("\n" + "=" * 60)
        print("              ANALYSIS CONDENSATION")
        if dry_run:
            print("                  (DRY RUN)")
        print("=" * 60)

        if self.analysis_folder:
            print(f"\nSource: {self.analysis_folder}")
        else:
            print("\nSource: None (standalone mode)")

        print(f"Output: {self.output_folder}")

    def _print_summary(self, result: CondensationResult) -> None:
        """Print the completion summary."""
        print("\n" + "=" * 60)
        print("              CONDENSATION COMPLETE")
        print("=" * 60)

        print(f"\nOutput folder: {result.output_folder}")
        print(f"\nFiles generated:")
        print(f"  - 00-personal-background (verified: {result.background.verification_status})")

        for summary in result.summaries:
            print(f"  - {summary.filename} ({summary.word_count} words)")

        filled, total = result.background.count_filled_fields()
        print(f"\nBackground: {filled}/{total} fields filled")
        print(f"Total words: {result.total_word_count:,}")
        print(f"Total files: {result.total_files}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Condense personal analysis into shareable profile documents"
    )

    parser.add_argument(
        "--notes-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the Obsidian vault",
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        help="Specific analysis folder to condense (uses latest if not specified)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output folder for profile documents (auto-generated if not specified)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive background verification",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run in standalone mode (no analysis required)",
    )
    parser.add_argument(
        "--background-only",
        action="store_true",
        help="Only generate/verify the background document",
    )
    parser.add_argument(
        "--categories",
        type=str,
        help="Comma-separated list of categories to generate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be generated without writing files",
    )

    args = parser.parse_args()

    # Parse categories if provided
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Create and run condenser
    condenser = AnalysisCondenser(
        notes_root=args.notes_root,
        analysis_folder=args.analysis,
        output_folder=args.output,
    )

    if args.standalone:
        result = condenser.run_standalone(interactive=not args.non_interactive)
    else:
        result = condenser.run(
            interactive=not args.non_interactive,
            background_only=args.background_only,
            categories=categories,
            dry_run=args.dry_run,
        )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

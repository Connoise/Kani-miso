"""
Main orchestrator for personal analysis.

Coordinates the full analysis pipeline from content collection
through synthesis and output generation.
"""

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
import sys

import anthropic

from .config import AnalysisConfig
from .models import CollectedContent, AnalysisResult, FullAnalysisResult, Image
from .cost_estimator import CostEstimator, CostEstimate
from .checkpoint import CheckpointManager, AnalysisPhase
from .collectors import (
    NoteCollector,
    ReflectionCollector,
    TweetCollector,
    ImageCollector,
    HubCollector,
    ContentSampler,
)
from .analyzers import (
    PsychologicalAnalyzer,
    EmotionalAnalyzer,
    IntellectualAnalyzer,
    EthicalAnalyzer,
    SpiritualAnalyzer,
    PhilosophicalAnalyzer,
    VisualAnalyzer,
)
from .analyzers.pattern import PatternAnalyzer
from .analyzers.relational import RelationalAnalyzer
from .analyzers.synthesis import SynthesisAnalyzer
from .generators import ObsidianMarkdownGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PersonalAnalyzer:
    """
    Main orchestrator for comprehensive personal analysis.

    Coordinates content collection, analysis across multiple dimensions,
    synthesis, and output generation.
    """

    def __init__(self, config: AnalysisConfig):
        """
        Initialize the analyzer.

        Args:
            config: Analysis configuration
        """
        self.config = config
        self.client = anthropic.Anthropic()
        self.checkpoint_manager = CheckpointManager(config.checkpoint_dir)
        self.cost_estimator = CostEstimator(config)

        # Analysis results storage
        self.content: Optional[CollectedContent] = None
        self.core_results: Dict[str, AnalysisResult] = {}
        self.pattern_results: Dict[str, AnalysisResult] = {}
        self.relational_results: Dict[str, AnalysisResult] = {}
        self.synthesis_results: Dict[str, AnalysisResult] = {}
        self.guidance_results: Dict[str, AnalysisResult] = {}

    def run(self, resume: bool = False, force_new: bool = False) -> Optional[FullAnalysisResult]:
        """
        Run the full analysis pipeline.

        Args:
            resume: Whether to resume from checkpoint
            force_new: Whether to force a new analysis (ignore checkpoint)

        Returns:
            FullAnalysisResult or None if cancelled/failed
        """
        run_id = datetime.now().isoformat()
        output_folder = self.config.get_output_folder()

        # Check for existing checkpoint
        if not force_new and self.checkpoint_manager.has_checkpoint():
            checkpoint = self.checkpoint_manager.load_checkpoint()
            if checkpoint:
                if resume:
                    return self._resume_from_checkpoint(checkpoint)
                else:
                    choice = self.checkpoint_manager.prompt_resume(checkpoint)
                    if choice == "resume":
                        return self._resume_from_checkpoint(checkpoint)
                    elif choice == "cancel":
                        print("Analysis cancelled.")
                        return None
                    # choice == "new": continue with new analysis

        logger.info("Starting new analysis")

        # Phase 1: Collection
        print("\n📥 Collecting content...")
        self.content = self._collect_content()

        if self.content.total_items == 0:
            print("❌ No content found to analyze.")
            return None

        # Cost estimation and confirmation
        estimate = self.cost_estimator.estimate(self.content)

        if self.config.dry_run:
            print(self.cost_estimator.format_estimate(estimate))
            print("\n🔍 DRY RUN - No API calls will be made.")
            return None

        if self.config.require_cost_confirmation and not self.config.skip_confirmation:
            if not self.cost_estimator.prompt_confirmation(estimate):
                print("Analysis cancelled.")
                return None

        # Apply sampling if needed
        if estimate.requires_sampling:
            print("\n✂️ Sampling content (exceeds context limits)...")
            sampler = ContentSampler(self.config.max_context_tokens)
            result = sampler.sample_if_needed(self.content)
            self.content = result.content

        # Create output folder and save checkpoint
        output_folder.mkdir(parents=True, exist_ok=True)
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.COLLECTION)

        # Phase 2: Core Analysis
        print("\n🧠 Running core analyses...")
        self.core_results = self._run_core_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.CORE_ANALYSIS)

        # Phase 3: Pattern Analysis
        print("\n🔍 Running pattern analyses...")
        self.pattern_results = self._run_pattern_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.PATTERN_ANALYSIS)

        # Phase 4: Relational Analysis
        print("\n👥 Running relational analyses...")
        self.relational_results = self._run_relational_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.RELATIONAL_ANALYSIS)

        # Phase 5: Synthesis
        if self.config.generate_synthesis:
            print("\n🔮 Generating synthesis...")
            self.synthesis_results = self._run_synthesis()
            self._save_checkpoint(run_id, output_folder, AnalysisPhase.SYNTHESIS)

        # Phase 6: Guidance
        if self.config.generate_guidance:
            print("\n💡 Generating guidance...")
            self.guidance_results = self._run_guidance()
            self._save_checkpoint(run_id, output_folder, AnalysisPhase.GUIDANCE)

        # Phase 7: Output
        print("\n📝 Writing output files...")
        full_result = self._generate_outputs(run_id, output_folder)

        # Clean up checkpoint
        self.checkpoint_manager.delete_checkpoint()

        print(f"\n✅ Analysis complete! Output written to: {output_folder}")
        return full_result

    def _collect_content(self) -> CollectedContent:
        """Collect all content from configured sources."""
        content_dirs = self.config.get_content_dirs()

        notes = []
        reflections = []
        tweets = []
        images = []
        hubs = []

        # Collect notes
        if "notes" in content_dirs:
            collector = NoteCollector(content_dirs["notes"])
            notes = collector.collect_all(
                self.config.date_range_start,
                self.config.date_range_end,
            )
            logger.info(f"Collected {len(notes)} notes")

        # Collect reflections
        if "reflections" in content_dirs:
            collector = ReflectionCollector(content_dirs["reflections"])
            reflections = collector.collect_all(
                self.config.date_range_start,
                self.config.date_range_end,
            )
            logger.info(f"Collected {len(reflections)} reflections")

        # Collect tweets
        if "tweets" in content_dirs:
            collector = TweetCollector(content_dirs["tweets"])
            tweets = collector.collect_all(
                self.config.date_range_start,
                self.config.date_range_end,
            )
            logger.info(f"Collected {len(tweets)} tweets")

        # Collect images
        if "images" in content_dirs:
            collector = ImageCollector(content_dirs["images"], self.config.notes_root)
            images = collector.collect_all(
                notes + reflections,
                self.config.date_range_start,
                self.config.date_range_end,
            )
            logger.info(f"Collected {len(images)} images")

        # Collect hub metadata
        if "hubs" in content_dirs:
            collector = HubCollector(content_dirs["hubs"])
            hubs = collector.collect_all()
            logger.info(f"Collected {len(hubs)} hubs")

        return CollectedContent(
            notes=notes,
            reflections=reflections,
            tweets=tweets,
            images=images,
            hubs=hubs,
        )

    def _run_core_analysis(self) -> Dict[str, AnalysisResult]:
        """Run core analysis dimensions in parallel."""
        analyzers = []

        if "psychological" in self.config.core_dimensions:
            analyzers.append(PsychologicalAnalyzer(self.config, self.client))
        if "emotional" in self.config.core_dimensions:
            analyzers.append(EmotionalAnalyzer(self.config, self.client))
        if "intellectual" in self.config.core_dimensions:
            analyzers.append(IntellectualAnalyzer(self.config, self.client))
        if "ethical" in self.config.core_dimensions:
            analyzers.append(EthicalAnalyzer(self.config, self.client))
        if "spiritual" in self.config.core_dimensions:
            analyzers.append(SpiritualAnalyzer(self.config, self.client))
        if "philosophical" in self.config.core_dimensions:
            analyzers.append(PhilosophicalAnalyzer(self.config, self.client))
        if "visual" in self.config.core_dimensions:
            analyzers.append(VisualAnalyzer(self.config, self.client))

        return self._run_parallel_analyses(analyzers)

    def _run_pattern_analysis(self) -> Dict[str, AnalysisResult]:
        """Run pattern analysis dimensions in parallel."""
        analyzers = []

        for pattern_type in self.config.pattern_dimensions:
            analyzers.append(PatternAnalyzer(self.config, self.client, pattern_type))

        return self._run_parallel_analyses(analyzers)

    def _run_relational_analysis(self) -> Dict[str, AnalysisResult]:
        """Run relational analysis dimensions in parallel."""
        analyzers = []

        for relational_type in self.config.relational_dimensions:
            analyzers.append(RelationalAnalyzer(self.config, self.client, relational_type))

        return self._run_parallel_analyses(analyzers)

    def _run_parallel_analyses(self, analyzers: list) -> Dict[str, AnalysisResult]:
        """Run multiple analyzers in parallel using ThreadPoolExecutor."""
        results = {}

        # Prepare images for visual analyzer
        images = self.content.images if self.config.include_images else None

        def run_analyzer(analyzer):
            dim = analyzer.dimension
            print(f"  Running {dim}...")
            if hasattr(analyzer, "_uses_images") and analyzer._uses_images():
                result = analyzer.analyze(self.content, images)
            else:
                result = analyzer.analyze(self.content)
            print(f"  ✓ {dim} complete (confidence: {result.confidence})")
            return dim, result

        # Run in parallel with limited concurrency to avoid rate limits
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_analyzer, a) for a in analyzers]
            for future in futures:
                dim, result = future.result()
                results[dim] = result

        return results

    def _run_synthesis(self) -> Dict[str, AnalysisResult]:
        """Run synthesis analyses sequentially (they depend on previous results)."""
        results = {}
        all_previous = {**self.core_results, **self.pattern_results, **self.relational_results}

        synthesis_types = ["unified_portrait", "hidden_truths", "core_tensions", "essence_distillation"]

        for synthesis_type in synthesis_types:
            print(f"  Running {synthesis_type}...")
            analyzer = SynthesisAnalyzer(self.config, self.client, synthesis_type)
            analyzer.set_previous_analyses(all_previous)
            result = analyzer.analyze(self.content)
            results[synthesis_type] = result
            all_previous[synthesis_type] = result  # Available for next synthesis
            print(f"  ✓ {synthesis_type} complete")

        return results

    def _run_guidance(self) -> Dict[str, AnalysisResult]:
        """Run guidance analyses sequentially."""
        results = {}
        all_previous = {
            **self.core_results,
            **self.pattern_results,
            **self.relational_results,
            **self.synthesis_results,
        }

        guidance_types = ["growth_opportunities", "shadow_work", "strength_amplification", "warning_signs", "actionable_practices"]

        for guidance_type in guidance_types:
            print(f"  Running {guidance_type}...")
            analyzer = SynthesisAnalyzer(self.config, self.client, guidance_type)
            analyzer.set_previous_analyses(all_previous)
            result = analyzer.analyze(self.content)
            results[guidance_type] = result
            print(f"  ✓ {guidance_type} complete")

        return results

    def _generate_outputs(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Generate all output files."""
        generator = ObsidianMarkdownGenerator(output_folder)

        # Calculate totals
        total_input = 0
        total_output = 0

        # Write all analysis files
        all_results = {
            **self.core_results,
            **self.pattern_results,
            **self.relational_results,
            **self.synthesis_results,
            **self.guidance_results,
        }

        for dimension, result in all_results.items():
            generator.write_analysis(result)
            total_input += result.input_tokens
            total_output += result.output_tokens

        # Create full result
        full_result = FullAnalysisResult(
            run_id=run_id,
            output_folder=output_folder,
            config_used=self._config_to_dict(),
            core_analyses=self.core_results,
            pattern_analyses=self.pattern_results,
            relational_analyses=self.relational_results,
            synthesis_results=self.synthesis_results,
            guidance_results=self.guidance_results,
            completed_at=datetime.now(),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            content_summary={
                "notes": len(self.content.notes),
                "reflections": len(self.content.reflections),
                "tweets": len(self.content.tweets),
                "images": len(self.content.images),
            },
            was_sampled=self.content.was_sampled,
        )

        # Estimate cost
        from .config import estimate_cost
        min_cost, max_cost = estimate_cost(total_input, total_output)
        full_result.total_cost = (min_cost + max_cost) / 2

        # Write supporting files
        generator.write_manifest(self.content, full_result)
        generator.write_evidence_citations(full_result)
        generator.write_confidence_levels(full_result)
        generator.write_methodology(full_result.config_used)
        generator.write_limitations()

        # Write sampling report if sampled
        if self.content.was_sampled:
            sampler = ContentSampler()
            from .collectors.sampler import SamplingResult
            sampling_result = SamplingResult(
                content=self.content,
                was_sampled=True,
                sampling_ratio=self.content.sampling_ratio,
                details=self.content.sampling_details,
            )
            report = sampler.generate_sampling_report(sampling_result)
            sampling_path = output_folder / "appendices" / "sampling-details.md"
            sampling_path.write_text(f"---\ntype: appendix\ntitle: Sampling Details\n---\n\n{report}")

        return full_result

    def _save_checkpoint(self, run_id: str, output_folder: Path, phase: str) -> None:
        """Save a checkpoint for the current phase."""
        if not self.config.enable_checkpoints:
            return

        completed = []
        pending = []

        # Determine completed and pending based on phase
        all_dims = self.config.active_dimensions

        if phase == AnalysisPhase.COLLECTION:
            pending = all_dims
        elif phase == AnalysisPhase.CORE_ANALYSIS:
            completed = list(self.core_results.keys())
            pending = [d for d in all_dims if d not in completed]
        elif phase == AnalysisPhase.PATTERN_ANALYSIS:
            completed = list(self.core_results.keys()) + list(self.pattern_results.keys())
            pending = [d for d in all_dims if d not in completed]
        elif phase == AnalysisPhase.RELATIONAL_ANALYSIS:
            completed = (
                list(self.core_results.keys())
                + list(self.pattern_results.keys())
                + list(self.relational_results.keys())
            )
            pending = []
        # Synthesis and guidance don't need detailed tracking

        self.checkpoint_manager.save_checkpoint(
            run_id=run_id,
            output_folder=output_folder,
            phase=phase,
            completed_analyses=completed,
            pending_analyses=pending,
            content_hash=self.content.content_hash if self.content else "",
        )

    def _resume_from_checkpoint(self, checkpoint: Dict) -> Optional[FullAnalysisResult]:
        """Resume analysis from a checkpoint."""
        logger.info(f"Resuming from checkpoint: {checkpoint.get('phase')}")

        run_id = checkpoint["run_id"]
        output_folder = Path(checkpoint["output_folder"])
        phase = checkpoint["phase"]

        # Re-collect content
        print("\n📥 Re-collecting content...")
        self.content = self._collect_content()

        # Validate content hash
        if not self.checkpoint_manager.validate_checkpoint(checkpoint, self.content):
            print("⚠️ Content has changed since checkpoint. Starting fresh.")
            self.checkpoint_manager.delete_checkpoint()
            return self.run(force_new=True)

        # Load any saved results
        results_dir = self.config.checkpoint_dir / "results"
        saved_results = self.checkpoint_manager.load_analysis_results(results_dir)

        # Restore results to appropriate categories
        for dim, result in saved_results.items():
            if dim in self.config.core_dimensions:
                self.core_results[dim] = result
            elif dim in self.config.pattern_dimensions:
                self.pattern_results[dim] = result
            elif dim in self.config.relational_dimensions:
                self.relational_results[dim] = result

        # Resume from the appropriate phase
        if phase == AnalysisPhase.COLLECTION:
            # Start from core analysis
            return self._continue_from_core(run_id, output_folder)
        elif phase == AnalysisPhase.CORE_ANALYSIS:
            return self._continue_from_pattern(run_id, output_folder)
        elif phase == AnalysisPhase.PATTERN_ANALYSIS:
            return self._continue_from_relational(run_id, output_folder)
        elif phase == AnalysisPhase.RELATIONAL_ANALYSIS:
            return self._continue_from_synthesis(run_id, output_folder)
        elif phase == AnalysisPhase.SYNTHESIS:
            return self._continue_from_guidance(run_id, output_folder)
        elif phase == AnalysisPhase.GUIDANCE:
            return self._continue_from_output(run_id, output_folder)

        return None

    def _continue_from_core(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from core analysis phase."""
        print("\n🧠 Running core analyses...")
        self.core_results = self._run_core_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.CORE_ANALYSIS)
        return self._continue_from_pattern(run_id, output_folder)

    def _continue_from_pattern(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from pattern analysis phase."""
        print("\n🔍 Running pattern analyses...")
        self.pattern_results = self._run_pattern_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.PATTERN_ANALYSIS)
        return self._continue_from_relational(run_id, output_folder)

    def _continue_from_relational(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from relational analysis phase."""
        print("\n👥 Running relational analyses...")
        self.relational_results = self._run_relational_analysis()
        self._save_checkpoint(run_id, output_folder, AnalysisPhase.RELATIONAL_ANALYSIS)
        return self._continue_from_synthesis(run_id, output_folder)

    def _continue_from_synthesis(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from synthesis phase."""
        if self.config.generate_synthesis:
            print("\n🔮 Generating synthesis...")
            self.synthesis_results = self._run_synthesis()
            self._save_checkpoint(run_id, output_folder, AnalysisPhase.SYNTHESIS)
        return self._continue_from_guidance(run_id, output_folder)

    def _continue_from_guidance(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from guidance phase."""
        if self.config.generate_guidance:
            print("\n💡 Generating guidance...")
            self.guidance_results = self._run_guidance()
            self._save_checkpoint(run_id, output_folder, AnalysisPhase.GUIDANCE)
        return self._continue_from_output(run_id, output_folder)

    def _continue_from_output(self, run_id: str, output_folder: Path) -> FullAnalysisResult:
        """Continue from output phase."""
        print("\n📝 Writing output files...")
        full_result = self._generate_outputs(run_id, output_folder)
        self.checkpoint_manager.delete_checkpoint()
        print(f"\n✅ Analysis complete! Output written to: {output_folder}")
        return full_result

    def _config_to_dict(self) -> Dict:
        """Convert config to dictionary for storage."""
        return {
            "notes_root": str(self.config.notes_root),
            "output_root": str(self.config.output_root),
            "include_notes": self.config.include_notes,
            "include_reflections": self.config.include_reflections,
            "include_tweets": self.config.include_tweets,
            "include_images": self.config.include_images,
            "model": self.config.model,
            "dimensions": self.config.active_dimensions,
            "generate_synthesis": self.config.generate_synthesis,
            "generate_guidance": self.config.generate_guidance,
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Personal Analysis - Deep character analysis using Claude Opus 4.5"
    )

    parser.add_argument(
        "--notes-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the Obsidian vault",
    )
    parser.add_argument(
        "--dimensions",
        type=str,
        help="Comma-separated list of dimensions to analyze",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Start date for analysis (ISO format)",
    )
    parser.add_argument(
        "--until",
        type=str,
        help="End date for analysis (ISO format)",
    )
    parser.add_argument(
        "--no-tweets",
        action="store_true",
        help="Exclude tweets from analysis",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Exclude images from analysis",
    )
    parser.add_argument(
        "--no-reflections",
        action="store_true",
        help="Exclude reflections from analysis",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview content and cost without running analysis",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip cost confirmation prompt",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        help="Maximum budget in USD",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint if available",
    )
    parser.add_argument(
        "--force-new",
        action="store_true",
        help="Force new analysis, ignoring any checkpoint",
    )

    args = parser.parse_args()

    # Build config
    config = AnalysisConfig(
        notes_root=args.notes_root,
        include_tweets=not args.no_tweets,
        include_images=not args.no_images,
        include_reflections=not args.no_reflections,
        dry_run=args.dry_run,
        skip_confirmation=args.yes,
        max_budget=args.max_budget,
    )

    if args.dimensions:
        config.dimensions = args.dimensions.split(",")

    if args.since:
        config.date_range_start = datetime.fromisoformat(args.since)

    if args.until:
        config.date_range_end = datetime.fromisoformat(args.until)

    # Run analysis
    analyzer = PersonalAnalyzer(config)
    result = analyzer.run(resume=args.resume, force_new=args.force_new)

    if result:
        print(f"\nTotal cost: ${result.total_cost:.2f}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Checkpoint management for personal analysis.

Enables saving and resuming interrupted analysis runs.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .models import AnalysisResult, CollectedContent

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage checkpoints for resuming interrupted analysis runs."""

    CHECKPOINT_FILE = "checkpoint.json"

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize the checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    @property
    def checkpoint_path(self) -> Path:
        """Get the path to the checkpoint file."""
        return self.checkpoint_dir / self.CHECKPOINT_FILE

    def has_checkpoint(self) -> bool:
        """Check if a checkpoint exists."""
        return self.checkpoint_path.exists()

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load an existing checkpoint.

        Returns:
            Checkpoint data dict or None if no checkpoint exists
        """
        if not self.has_checkpoint():
            return None

        try:
            with open(self.checkpoint_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def save_checkpoint(
        self,
        run_id: str,
        output_folder: Path,
        phase: str,
        completed_analyses: List[str],
        pending_analyses: List[str],
        content_hash: str,
        partial_results: Dict[str, Any] = None,
    ) -> None:
        """
        Save a checkpoint.

        Args:
            run_id: Unique identifier for this run
            output_folder: Path to output folder
            phase: Current phase name
            completed_analyses: List of completed analysis names
            pending_analyses: List of pending analysis names
            content_hash: Hash of collected content for validation
            partial_results: Optional dict of partial results to preserve
        """
        checkpoint = {
            "run_id": run_id,
            "output_folder": str(output_folder),
            "phase": phase,
            "completed_analyses": completed_analyses,
            "pending_analyses": pending_analyses,
            "content_hash": content_hash,
            "partial_results": partial_results or {},
            "saved_at": datetime.now().isoformat(),
        }

        try:
            with open(self.checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2, default=str)
            logger.info(f"Checkpoint saved: phase={phase}, completed={len(completed_analyses)}")
        except IOError as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def delete_checkpoint(self) -> None:
        """Delete the checkpoint file (called on successful completion)."""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            logger.info("Checkpoint deleted (run complete)")

    def validate_checkpoint(self, checkpoint: Dict[str, Any], content: CollectedContent) -> bool:
        """
        Validate that a checkpoint matches the current content.

        Args:
            checkpoint: Loaded checkpoint data
            content: Current collected content

        Returns:
            True if checkpoint is valid for this content
        """
        stored_hash = checkpoint.get("content_hash", "")
        current_hash = content.content_hash

        if stored_hash != current_hash:
            logger.warning(f"Content hash mismatch: stored={stored_hash}, current={current_hash}")
            return False

        return True

    def get_resume_info(self, checkpoint: Dict[str, Any]) -> str:
        """
        Get human-readable resume information.

        Args:
            checkpoint: Loaded checkpoint data

        Returns:
            Formatted string describing the checkpoint
        """
        completed = len(checkpoint.get("completed_analyses", []))
        pending = len(checkpoint.get("pending_analyses", []))
        total = completed + pending
        phase = checkpoint.get("phase", "unknown")
        saved_at = checkpoint.get("saved_at", "unknown")

        return f"""Found incomplete analysis from {saved_at}
  • Phase: {phase} ({completed}/{total} complete)
  • Output folder: {checkpoint.get('output_folder', 'unknown')}"""

    def prompt_resume(self, checkpoint: Dict[str, Any]) -> str:
        """
        Prompt user for resume action.

        Args:
            checkpoint: Loaded checkpoint data

        Returns:
            User's choice: 'resume', 'new', or 'cancel'
        """
        print(self.get_resume_info(checkpoint))
        print("\nOptions:")
        print("  [r] Resume from checkpoint")
        print("  [n] Start new analysis (discards partial results)")
        print("  [c] Cancel")

        try:
            choice = input("\nChoice: ").strip().lower()
            if choice in ("r", "resume"):
                return "resume"
            elif choice in ("n", "new"):
                return "new"
            else:
                return "cancel"
        except (EOFError, KeyboardInterrupt):
            return "cancel"

    def save_analysis_result(self, result: AnalysisResult, results_dir: Path) -> None:
        """
        Save an individual analysis result to disk.

        This allows partial results to be preserved even if the run is interrupted.

        Args:
            result: Analysis result to save
            results_dir: Directory to save results
        """
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{result.dimension}.json"
        try:
            data = {
                "dimension": result.dimension,
                "title": result.title,
                "content": result.content,
                "confidence": result.confidence,
                "generated_at": result.generated_at.isoformat(),
                "model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "thinking_tokens": result.thinking_tokens,
                "cited_notes": result.cited_notes,
                "key_insights": result.key_insights,
                "error": result.error,
                "is_partial": result.is_partial,
            }
            with open(result_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save analysis result {result.dimension}: {e}")

    def load_analysis_results(self, results_dir: Path) -> Dict[str, AnalysisResult]:
        """
        Load saved analysis results from disk.

        Args:
            results_dir: Directory containing saved results

        Returns:
            Dict mapping dimension name to AnalysisResult
        """
        results = {}

        if not results_dir.exists():
            return results

        for result_file in results_dir.glob("*.json"):
            try:
                with open(result_file, "r") as f:
                    data = json.load(f)

                result = AnalysisResult(
                    dimension=data["dimension"],
                    title=data["title"],
                    content=data["content"],
                    confidence=data["confidence"],
                    generated_at=datetime.fromisoformat(data["generated_at"]),
                    model=data.get("model", ""),
                    input_tokens=data.get("input_tokens", 0),
                    output_tokens=data.get("output_tokens", 0),
                    thinking_tokens=data.get("thinking_tokens", 0),
                    cited_notes=data.get("cited_notes", []),
                    key_insights=data.get("key_insights", []),
                    error=data.get("error"),
                    is_partial=data.get("is_partial", False),
                )
                results[result.dimension] = result
            except (json.JSONDecodeError, KeyError, IOError) as e:
                logger.error(f"Failed to load result from {result_file}: {e}")

        return results


class AnalysisPhase:
    """Constants for analysis phases."""

    COLLECTION = "collection_complete"
    CORE_ANALYSIS = "core_analysis_complete"
    PATTERN_ANALYSIS = "pattern_analysis_complete"
    RELATIONAL_ANALYSIS = "relational_analysis_complete"
    SYNTHESIS = "synthesis_complete"
    GUIDANCE = "guidance_complete"

    @classmethod
    def all_phases(cls) -> List[str]:
        """Return all phases in order."""
        return [
            cls.COLLECTION,
            cls.CORE_ANALYSIS,
            cls.PATTERN_ANALYSIS,
            cls.RELATIONAL_ANALYSIS,
            cls.SYNTHESIS,
            cls.GUIDANCE,
        ]

    @classmethod
    def get_next_phase(cls, current: str) -> Optional[str]:
        """Get the phase after the current one."""
        phases = cls.all_phases()
        try:
            idx = phases.index(current)
            if idx < len(phases) - 1:
                return phases[idx + 1]
        except ValueError:
            pass
        return None

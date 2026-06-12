"""
Git Manager for Kani-miso
Handles Git operations (add, commit, push) safely.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import git
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GitManager:
    """Manages Git operations for the archive."""

    def __init__(self, repo_path: Path, auto_push: bool = False):
        """
        Initialize Git manager.

        Args:
            repo_path: Path to Git repository
            auto_push: Whether to automatically push after commit
        """
        self.repo_path = Path(repo_path)
        self.auto_push = auto_push

        try:
            self.repo = git.Repo(self.repo_path)
            logger.info(f"Initialized Git manager for {self.repo_path}")
        except git.InvalidGitRepositoryError:
            raise ValueError(f"{self.repo_path} is not a valid Git repository")

    def check_repo_state(self) -> Dict[str, Any]:
        """
        Check the current state of the repository.

        Returns:
            Dictionary with repo state information
        """
        state = {
            'clean': not self.repo.is_dirty(),
            'branch': self.repo.active_branch.name,
            'untracked': len(self.repo.untracked_files),
            'modified': len([item.a_path for item in self.repo.index.diff(None)]),
            'staged': len([item.a_path for item in self.repo.index.diff('HEAD')]),
        }

        logger.debug(f"Repo state: {state}")
        return state

    def add_files(self, file_paths: List[Path]):
        """
        Stage files for commit.

        Args:
            file_paths: List of file paths to stage
        """
        for file_path in file_paths:
            relative_path = file_path.relative_to(self.repo_path)
            self.repo.index.add([str(relative_path)])
            logger.debug(f"Staged: {relative_path}")

        logger.info(f"Staged {len(file_paths)} files")

    def create_commit(
        self,
        message: str,
        file_paths: List[Path],
        prefix: str = "process",
    ) -> Optional[str]:
        """
        Create a Git commit.

        Args:
            message: Commit message
            file_paths: Files to include in commit
            prefix: Message prefix

        Returns:
            Commit SHA if successful, None otherwise
        """
        if not file_paths:
            logger.warning("No files to commit")
            return None

        try:
            # Stage files
            self.add_files(file_paths)

            # Create commit message
            full_message = f"{prefix}: {message}"

            # Commit
            commit = self.repo.index.commit(full_message)
            logger.info(f"Created commit: {commit.hexsha[:8]} - {full_message}")

            return commit.hexsha

        except Exception as e:
            logger.error(f"Failed to create commit: {e}")
            return None

    def create_batch_commit(
        self,
        file_paths: List[Path],
        note_types: Dict[str, int],
    ) -> Optional[str]:
        """
        Create a commit for a batch of processed captures.

        Args:
            file_paths: List of created files
            note_types: Dictionary of note type counts

        Returns:
            Commit SHA if successful
        """
        # Build commit message
        date_str = datetime.now().strftime("%Y-%m-%d")
        total = len(file_paths)

        summary = f"batch {date_str} ({total} items)"

        # Build details
        details = []
        for note_type, count in sorted(note_types.items()):
            details.append(f"- {count} {note_type.lower()}{'s' if count > 1 else ''}")

        message_parts = [summary, ""] + details
        full_message = "\n".join(message_parts)

        # Create commit
        return self.create_commit(
            full_message,
            file_paths,
            prefix="process",
        )

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """
        Push commits to remote.

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)

        Returns:
            True if successful
        """
        try:
            if branch is None:
                branch = self.repo.active_branch.name

            logger.info(f"Pushing to {remote}/{branch}...")

            # Push
            push_info = self.repo.remote(remote).push(branch)[0]

            if push_info.flags & git.PushInfo.ERROR:
                logger.error(f"Push failed: {push_info.summary}")
                return False

            logger.info(f"Successfully pushed to {remote}/{branch}")
            return True

        except Exception as e:
            logger.error(f"Failed to push: {e}")
            return False

    def get_commit_summary(self, commit_sha: str) -> str:
        """
        Get a summary of files in a commit.

        Args:
            commit_sha: Commit SHA

        Returns:
            Summary string
        """
        try:
            commit = self.repo.commit(commit_sha)
            files = list(commit.stats.files.keys())

            summary_lines = [
                f"Commit: {commit_sha[:8]}",
                f"Message: {commit.message.strip()}",
                f"Files ({len(files)}):",
            ]

            for file in files[:10]:  # Show first 10
                summary_lines.append(f"  - {file}")

            if len(files) > 10:
                summary_lines.append(f"  ... and {len(files) - 10} more")

            return "\n".join(summary_lines)

        except Exception as e:
            return f"Error getting commit summary: {e}"

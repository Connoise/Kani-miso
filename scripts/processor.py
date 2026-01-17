"""
Main Processor for Second Brain
Orchestrates the processing of queued captures.

Based on specs:
- 20-processing-pipeline.md
- 19-error-handling.md
- 24-webpage-archival.md
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from queue_manager import QueueManager
from processors.claude_client import ClaudeClient
from processors.file_writer import FileWriter
from processors.git_manager import GitManager
from processors.web_archiver import WebArchiver
from utils.logger import setup_logger
from models.data_models import CertaintyLevel, NoteStatus, validate_url

# Load environment variables
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class Processor:
    """Main processing orchestrator."""

    def __init__(self, config_path: Path = None):
        """
        Initialize processor with configuration.

        Args:
            config_path: Path to config.yaml file
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize repo root
        self.repo_root = Path(__file__).parent.parent

        # Setup logger with config
        global logger
        logger = setup_logger(
            __name__,
            log_file=self.repo_root / self.config['logging']['file'],
            level=self.config['logging']['level'],
            console=self.config['logging']['console'],
        )

        logger.info("=" * 60)
        logger.info("Second Brain Processor Starting")
        logger.info("=" * 60)

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all processing components."""
        # Queue manager
        queue_db_path = self.repo_root / self.config['paths']['queue_db']
        self.queue = QueueManager(queue_db_path)

        # Reset any stuck 'processing' items
        self.queue.reset_processing()

        # Claude client
        self.claude = ClaudeClient(
            model=self.config['claude']['model'],
            max_tokens=self.config['claude']['max_tokens'],
            temperature=self.config['claude']['temperature'],
        )

        # File writer
        self.file_writer = FileWriter(
            self.repo_root,
            self.config['folders'],
        )

        # Git manager (only if auto_commit enabled)
        if self.config['processing']['auto_commit']:
            self.git = GitManager(
                self.repo_root,
                auto_push=self.config['processing']['auto_push'],
            )
        else:
            self.git = None

        # Web archiver (from 24-webpage-archival.md)
        self.web_archiver = WebArchiver(self.repo_root)

        logger.info("All components initialized")

    # =========================================================================
    # URL Detection and Processing (from 24-webpage-archival.md)
    # =========================================================================

    def _is_url_capture(self, capture: Dict[str, Any]) -> bool:
        """
        Detect if a capture is primarily a URL to archive.

        From 24-webpage-archival.md:
        - User sends URL -> Archive full content
        """
        body = capture.get('body', '').strip()

        # Check if body is primarily a URL
        # URL pattern at start of message
        url_match = re.match(r'^(https?://\S+)', body)
        if url_match:
            url = url_match.group(1)
            # If body is just the URL or URL followed by short comment
            remaining = body[len(url):].strip()
            if len(remaining) < 100:  # Short comment is OK
                return validate_url(url)

        return False

    def _extract_url_from_capture(self, capture: Dict[str, Any]) -> tuple:
        """
        Extract URL and optional comment from capture.

        Returns:
            (url, comment) tuple
        """
        body = capture.get('body', '').strip()
        url_match = re.match(r'^(https?://\S+)\s*(.*)', body, re.DOTALL)

        if url_match:
            url = url_match.group(1)
            comment = url_match.group(2).strip()
            return url, comment if comment else None

        return None, None

    def _process_url_capture(self, capture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a URL capture by archiving the webpage.

        From 24-webpage-archival.md:
        - Fetch page content
        - Extract main content
        - Convert to markdown
        - Store in /sources/

        Returns:
            Dict with success status and file path or error
        """
        url, comment = self._extract_url_from_capture(capture)

        if not url:
            return {'success': False, 'error': 'No URL found in capture'}

        logger.info(f"Archiving URL: {url}")

        # Archive the URL
        result = self.web_archiver.archive_url(url, user_summary=comment)

        if result['success']:
            logger.info(f"  Archived: {result['file_path'].name} ({result['word_count']} words)")
            if result.get('warnings'):
                for w in result['warnings']:
                    logger.warning(f"  Warning: {w}")
        else:
            logger.error(f"  Archive failed: {result['error']}")

        return result

    # =========================================================================
    # Context Encoding (from 20-processing-pipeline.md)
    # =========================================================================

    def _encode_context(self, capture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 2: Context Encoding

        From 20-processing-pipeline.md:
        - Infer missing fields
        - Add certainty level (if detectable)
        - Detect emotional context (if explicit)
        """
        enriched = capture.copy()

        # Infer captured_from if missing
        if not enriched.get('captured_from') or enriched.get('captured_from') == 'unknown':
            if enriched.get('telegram_message_id'):
                enriched['captured_from'] = 'telegram'

        # Add processing timestamp
        enriched['processed_at'] = datetime.now().isoformat()

        # Detect certainty level from text
        body = enriched.get('body', '')
        certainty = self._detect_certainty(body)
        if certainty and not enriched.get('confidence'):
            enriched['confidence'] = certainty

        # Detect emotional context (if explicit)
        emotional_context = self._detect_emotional_context(body)
        if emotional_context and not enriched.get('mood'):
            enriched['emotional_context'] = emotional_context

        return enriched

    def _detect_certainty(self, text: str) -> Optional[str]:
        """
        Detect certainty level from uncertainty markers in text.

        From 20-processing-pipeline.md: Check for "maybe", "possibly", "not sure"
        """
        text_lower = text.lower()

        # High uncertainty markers
        uncertainty_markers = [
            'maybe', 'possibly', 'not sure', "i don't know",
            'uncertain', 'might be', 'could be', 'perhaps',
            'i think', 'i guess', 'probably not', 'hard to say'
        ]

        # High certainty markers
        certainty_markers = [
            'definitely', 'certainly', 'absolutely', 'clearly',
            'obviously', "i'm sure", 'without doubt', 'for certain'
        ]

        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in text_lower)
        certainty_count = sum(1 for marker in certainty_markers if marker in text_lower)

        if uncertainty_count > certainty_count and uncertainty_count >= 1:
            return CertaintyLevel.LOW.value
        elif certainty_count > uncertainty_count and certainty_count >= 1:
            return CertaintyLevel.HIGH.value

        return None

    def _detect_emotional_context(self, text: str) -> Optional[str]:
        """
        Detect emotional context if explicitly stated.

        From 20-processing-pipeline.md: Check for "I'm feeling", "I feel"
        """
        text_lower = text.lower()

        # Explicit emotion patterns
        patterns = [
            r"i(?:'m| am) feeling (\w+)",
            r"i feel (\w+)",
            r"feeling (\w+) (?:today|right now|lately)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                emotion = match.group(1)
                # Filter out non-emotional words
                non_emotions = ['like', 'that', 'this', 'it', 'so']
                if emotion not in non_emotions:
                    return emotion

        return None

    def process_batch(self, limit: int = None) -> Dict[str, Any]:
        """
        Process a batch of pending captures.

        Args:
            limit: Maximum number of captures to process

        Returns:
            Summary dictionary with results
        """
        # Get batch size from config if not specified
        if limit is None:
            limit = self.config['processing']['batch_size']

        # Get pending captures
        captures = self.queue.get_pending(limit=limit)

        if not captures:
            logger.info("No pending captures to process")
            return {'processed': 0, 'failed': 0, 'files': []}

        logger.info(f"Processing {len(captures)} captures...")

        # Process each capture
        processed_files = []
        note_type_counts = defaultdict(int)
        failed_count = 0

        specs_dir = self.repo_root / self.config['paths']['specs_dir']

        for capture in captures:
            try:
                # Mark as processing
                self.queue.mark_processing(capture['id'])

                # Check if this is a URL capture (from 24-webpage-archival.md)
                if self._is_url_capture(capture):
                    logger.info(f"Processing URL capture {capture['id']}")
                    result = self._process_url_capture(capture)

                    if result['success']:
                        file_path = result['file_path']
                        processed_files.append(file_path)
                        note_type_counts['Source'] += 1
                        relative_path = str(file_path.relative_to(self.repo_root))
                        self.queue.mark_completed(capture['id'], relative_path)
                    else:
                        raise Exception(result['error'])

                    continue

                # Stage 2: Context Encoding (from 20-processing-pipeline.md)
                enriched_capture = self._encode_context(capture)

                # Process with Claude (Stage 3: Interpretation)
                logger.info(f"Processing capture {capture['id']} ({capture['type']})")
                if enriched_capture.get('confidence'):
                    logger.info(f"  Detected certainty: {enriched_capture['confidence']}")
                if enriched_capture.get('emotional_context'):
                    logger.info(f"  Detected emotional context: {enriched_capture['emotional_context']}")

                markdown = self.claude.process_telegram_capture(enriched_capture, specs_dir)

                # Write to file
                file_path = self.file_writer.write_note(markdown, capture)
                processed_files.append(file_path)

                # Track note type
                note_type_counts[capture['type']] += 1

                # Mark as completed
                relative_path = self.file_writer.get_relative_path(file_path)
                self.queue.mark_completed(capture['id'], relative_path)

            except Exception as e:
                logger.error(f"Failed to process capture {capture['id']}: {e}")
                self.queue.mark_failed(capture['id'], str(e))
                failed_count += 1

        # Create Git commit if enabled
        commit_sha = None
        if self.git and processed_files:
            commit_sha = self.git.create_batch_commit(processed_files, dict(note_type_counts))

            if commit_sha:
                # Show commit summary
                summary = self.git.get_commit_summary(commit_sha)
                logger.info("\n" + summary)

                # Handle push
                if self.config['processing']['auto_push']:
                    logger.warning("Auto-push is enabled but configured for manual review")
                    logger.info("Run 'git push' manually to push commits after review")

        # Summary
        summary = {
            'processed': len(processed_files),
            'failed': failed_count,
            'files': [self.file_writer.get_relative_path(f) for f in processed_files],
            'commit_sha': commit_sha,
            'note_types': dict(note_type_counts),
        }

        logger.info("=" * 60)
        logger.info(f"Batch complete: {summary['processed']} processed, {summary['failed']} failed")
        if commit_sha:
            logger.info(f"Commit: {commit_sha[:8]}")
        logger.info("=" * 60)

        return summary

    def show_stats(self):
        """Display queue statistics."""
        stats = self.queue.get_stats()

        logger.info("=" * 60)
        logger.info("Queue Statistics")
        logger.info("=" * 60)

        for status, count in stats.items():
            logger.info(f"{status.capitalize()}: {count}")

        total = sum(stats.values())
        logger.info(f"Total: {total}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Second Brain Processor")
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Number of captures to process (default: from config)',
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show queue statistics only',
    )

    args = parser.parse_args()

    try:
        processor = Processor()

        if args.stats:
            processor.show_stats()
        else:
            processor.process_batch(limit=args.batch_size)

    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

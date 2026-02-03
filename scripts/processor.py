"""
Main Processor for Second Brain
Orchestrates the processing of queued captures.
Supports both text-only and image+text captures.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from queue_manager import QueueManager
from processors.claude_client import ClaudeClient
from processors.file_writer import FileWriter
from processors.git_manager import GitManager
from processors.web_fetcher import WebFetcher
from processors.pdf_processor import PDFProcessor
from utils.logger import setup_logger

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

        # Initialize notes root (can be different from repo root)
        notes_root_config = self.config.get('notes_root', '.')
        if notes_root_config == '.' or not notes_root_config:
            self.notes_root = self.repo_root
        else:
            self.notes_root = Path(notes_root_config)
            # Create notes root if it doesn't exist
            self.notes_root.mkdir(parents=True, exist_ok=True)

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

        # File writer (notes go to notes_root, which may differ from repo_root)
        self.file_writer = FileWriter(
            self.repo_root,
            self.config['folders'],
            notes_root=self.notes_root,
        )

        # Git manager (only if auto_commit enabled and notes are in repo)
        if self.config['processing']['auto_commit']:
            if self.notes_root != self.repo_root:
                logger.warning("Git auto-commit disabled: notes are stored outside the repository")
                logger.info("To enable git tracking, initialize a git repo in your notes directory")
                self.git = None
            else:
                self.git = GitManager(
                    self.repo_root,
                    auto_push=self.config['processing']['auto_push'],
                )
        else:
            self.git = None

        # Web fetcher for source captures
        self.web_fetcher = WebFetcher()

        # PDF processor for document captures
        self.pdf_processor = PDFProcessor()

        logger.info("All components initialized")
        if self.notes_root != self.repo_root:
            logger.info(f"Notes storage: {self.notes_root}")

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

                # Check if capture has documents (PDFs)
                document_paths = []
                if capture.get('document_paths'):
                    try:
                        document_paths = json.loads(capture['document_paths'])
                    except (json.JSONDecodeError, TypeError):
                        document_paths = []

                # Check if capture has images
                image_paths = []
                if capture.get('image_paths'):
                    try:
                        image_paths = json.loads(capture['image_paths'])
                    except (json.JSONDecodeError, TypeError):
                        image_paths = []

                # Log what we found for this capture
                logger.debug(f"Capture {capture['id']}: document_paths={document_paths}, image_paths={image_paths}, type={capture['type']}")

                # Process with Claude based on capture type
                if document_paths:
                    # Document captures (PDFs) - extract text and process
                    logger.info(f"Processing capture {capture['id']} as PDF document: {document_paths}")
                    markdown = self._process_document_capture(capture, document_paths, specs_dir)
                elif image_paths:
                    logger.info(f"Processing capture {capture['id']} ({capture['type']}) with {len(image_paths)} images")
                    markdown = self.claude.process_capture_with_images(
                        capture,
                        image_paths,
                        specs_dir,
                        self.notes_root,
                    )
                elif capture['type'] == 'Source':
                    # Source captures - check for URL and fetch webpage
                    markdown = self._process_source_capture(capture, specs_dir)
                else:
                    logger.info(f"Processing capture {capture['id']} ({capture['type']})")
                    markdown = self.claude.process_telegram_capture(capture, specs_dir)

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

    def _process_source_capture(self, capture: Dict[str, Any], specs_dir: Path) -> str:
        """
        Process a source capture, fetching webpage content if URL is present.

        Args:
            capture: Capture dictionary from queue
            specs_dir: Path to specs directory

        Returns:
            Processed markdown content
        """
        body = capture.get('body', '')

        # Try to extract URL from the capture body
        url = self.web_fetcher.extract_url_from_text(body)

        if url:
            logger.info(f"Processing source capture {capture['id']} with URL: {url}")

            # Fetch and convert the webpage
            web_content = self.web_fetcher.fetch_and_convert(url)

            if web_content['success']:
                logger.info(f"Successfully fetched webpage: {web_content['metadata'].get('title', 'Unknown')}")
                # Process with source-specific prompt
                return self.claude.process_source_capture(capture, web_content, specs_dir)
            else:
                # Webpage fetch failed - log error and fall back to basic processing
                logger.warning(f"Failed to fetch webpage: {web_content['error']}")
                logger.info("Falling back to basic source processing without webpage content")

                # Create minimal web_content for processing
                web_content = {
                    'success': False,
                    'url': url,
                    'metadata': {'title': 'Unknown', 'domain': url},
                    'markdown_content': f"[Webpage content could not be fetched: {web_content['error']}]",
                    'error': web_content['error'],
                }
                return self.claude.process_source_capture(capture, web_content, specs_dir)
        else:
            # No URL found - process as regular source without web content
            logger.info(f"Processing source capture {capture['id']} (no URL detected)")

            # Create a minimal web_content structure for non-URL sources
            web_content = {
                'success': False,
                'url': '',
                'metadata': {},
                'markdown_content': '',
                'error': 'No URL provided',
            }
            # Fall back to telegram processing for non-URL sources
            return self.claude.process_telegram_capture(capture, specs_dir)

    def _process_document_capture(
        self,
        capture: Dict[str, Any],
        document_paths: List[str],
        specs_dir: Path,
    ) -> str:
        """
        Process a document capture (PDF), extracting text and processing with Claude.

        Args:
            capture: Capture dictionary from queue
            document_paths: List of document file paths
            specs_dir: Path to specs directory

        Returns:
            Processed markdown content
        """
        # Currently we only process the first document
        # (future: could combine multiple PDFs)
        if not document_paths:
            logger.warning(f"No document paths found for capture {capture['id']}")
            return self.claude.process_telegram_capture(capture, specs_dir)

        doc_path = Path(document_paths[0])
        logger.info(f"Processing document capture {capture['id']}: {doc_path.name}")

        # Check if it's a PDF
        if doc_path.suffix.lower() != '.pdf':
            logger.warning(f"Non-PDF document: {doc_path.suffix}. Falling back to text processing.")
            return self.claude.process_telegram_capture(capture, specs_dir)

        # Extract text from PDF
        pdf_content = self.pdf_processor.extract_text(doc_path)

        if pdf_content['success']:
            logger.info(
                f"Successfully extracted text from PDF: {pdf_content['page_count']} pages, "
                f"{len(pdf_content['text'])} characters"
            )
            # Process with PDF-specific prompt
            return self.claude.process_pdf_capture(capture, pdf_content, specs_dir)
        else:
            # PDF extraction failed - log error and try basic processing
            logger.warning(f"Failed to extract PDF text: {pdf_content['error']}")
            logger.info("Falling back to basic processing without PDF content")

            # Create minimal pdf_content for processing
            pdf_content = {
                'success': False,
                'text': f"[PDF text could not be extracted: {pdf_content['error']}]",
                'metadata': {},
                'page_count': 0,
                'pages_processed': 0,
                'file_path': str(doc_path),
                'file_name': doc_path.name,
                'error': pdf_content['error'],
            }
            return self.claude.process_pdf_capture(capture, pdf_content, specs_dir)

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

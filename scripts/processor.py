"""
Main Processor for Kani-miso
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
from processors.llm_client import build_llm_client
from processors.output_validator import validate_markdown_output
from processors.file_writer import FileWriter
from processors.git_manager import GitManager
from processors.web_fetcher import WebFetcher
from processors.pdf_processor import PDFProcessor
from processors.snapshotter import Snapshotter, head_by_words
from utils.slugify import create_slug
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
        logger.info("Kani-miso Processor Starting")
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

        # LLM client (Claude, Ollama, or hybrid — selected via config['llm'])
        self.llm = build_llm_client(self.config)

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

        # Page snapshotter for link captures (preservation artifacts)
        self.snapshotter = Snapshotter(
            self.notes_root, self.config.get('link_capture'),
        )

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

        # Get pending captures, plus any notes a previous run wrote to the
        # vault but never committed (crash between write and commit)
        captures = self.queue.get_pending(limit=limit)
        recovered = self._recover_written_items()

        if not captures and not recovered:
            logger.info("No pending captures to process")
            return {'processed': 0, 'failed': 0, 'files': []}

        if captures:
            logger.info(f"Processing {len(captures)} captures...")

        # Process each capture
        processed_files = []
        written_ids = []
        note_type_counts = defaultdict(int)
        failed_count = 0

        for item in recovered:
            note_type_counts[item['type']] += 1

        validation_mode = self.config.get('processing', {}).get('output_validation', 'strict')
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

                # Process with Claude based on capture type
                if document_paths:
                    # Document captures (PDFs) - extract text and process
                    capture_kind = 'pdf'
                    markdown = self._process_document_capture(capture, document_paths, specs_dir)
                elif image_paths:
                    logger.info(f"Processing capture {capture['id']} ({capture['type']}) with {len(image_paths)} images")
                    capture_kind = 'image'
                    markdown = self.llm.process_capture_with_images(
                        capture,
                        image_paths,
                        specs_dir,
                        self.notes_root,
                    )
                elif capture['type'] == 'Source':
                    # Source captures - check for URL and fetch webpage
                    capture_kind = 'source'
                    markdown = self._process_source_capture(capture, specs_dir)
                else:
                    logger.info(f"Processing capture {capture['id']} ({capture['type']})")
                    capture_kind = 'telegram'
                    markdown = self.llm.process_telegram_capture(capture, specs_dir)

                # Validate before anything reaches the vault: frontmatter,
                # corruption artifacts, verbatim raw-capture preservation
                # (specs/02-capture.md). Failure marks the capture failed and
                # leaves it requeueable; no file is written.
                validation = validate_markdown_output(
                    markdown, capture, mode=validation_mode, capture_kind=capture_kind,
                )
                if not validation.ok:
                    raise ValueError(f"output validation failed: {validation.reason}")
                markdown = validation.cleaned_markdown

                # Write to file
                file_path = self.file_writer.write_note(markdown, capture)
                processed_files.append(file_path)

                # Track note type
                note_type_counts[capture['type']] += 1

                relative_path = self.file_writer.get_relative_path(file_path)
                if self.git:
                    # Atomic unit of work: 'done' only after the commit lands.
                    self.queue.mark_written(capture['id'], relative_path)
                    written_ids.append(capture['id'])
                else:
                    self.queue.mark_completed(capture['id'], relative_path)

            except Exception as e:
                logger.error(f"Failed to process capture {capture['id']}: {e}")
                self.queue.mark_failed(capture['id'], str(e))
                failed_count += 1

        # Create Git commit if enabled
        commit_sha = None
        files_to_commit = [item['path'] for item in recovered] + processed_files
        ids_to_complete = [item['id'] for item in recovered] + written_ids
        if self.git and files_to_commit:
            commit_sha = self.git.create_batch_commit(files_to_commit, dict(note_type_counts))

            if commit_sha:
                # The unit of work is complete only now
                for capture_id in ids_to_complete:
                    self.queue.mark_completed(capture_id)

                # Show commit summary
                summary = self.git.get_commit_summary(commit_sha)
                logger.info("\n" + summary)

                # Handle push
                if self.config['processing']['auto_push']:
                    logger.warning("Auto-push is enabled but configured for manual review")
                    logger.info("Run 'git push' manually to push commits after review")
            else:
                logger.error(
                    f"Commit failed: {len(ids_to_complete)} notes remain status "
                    f"'written' and will be committed by the next run"
                )

        # Summary
        summary = {
            'processed': len(processed_files),
            'failed': failed_count,
            'recovered': len(recovered),
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

    def _recover_written_items(self) -> List[Dict[str, Any]]:
        """
        Find notes a previous run wrote to the vault but never committed
        (status 'written': the run died between file write and git commit).

        Items whose file still exists are returned as
        {'id', 'type', 'path'} for inclusion in this batch's commit; items
        whose file vanished are reset to pending for reprocessing.
        """
        items = []
        for row in self.queue.get_by_status('written'):
            output_file = row.get('output_file')
            path = (self.notes_root / output_file) if output_file else None
            if path and path.exists():
                items.append({'id': row['id'], 'type': row['type'], 'path': path})
            else:
                self.queue.reset_to_pending(row['id'])

        if items:
            logger.warning(
                f"Recovered {len(items)} written-but-uncommitted note(s) from a "
                f"previous run; including them in this batch's commit"
            )
        return items

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
                return self._build_link_note(capture, web_content, specs_dir)
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
                return self.llm.process_source_capture(capture, web_content, specs_dir)
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
            return self.llm.process_telegram_capture(capture, specs_dir)

    def _build_link_note(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        """
        Build a link-capture note: preserve the page (raw HTML + full text
        extraction + optional offline snapshot), then assemble the catalog
        note with a pipeline-injected Page Content head. The LLM produces only
        the frontmatter/summary/themes shell — it never transcribes the page
        (specs/02-capture.md, link-capture design).
        """
        final_url = web_content.get('final_url') or web_content.get('url', '')
        extracted = web_content.get('markdown_content', '') or ''
        raw_html = web_content.get('html', '') or ''
        metadata = web_content.get('metadata', {})

        # Filename stem the note will get, so the snapshot folder matches it
        title = metadata.get('title') or final_url
        stem = f"{capture.get('captured_at', '')[:10]}--{create_slug(title, max_length=50)}"

        # Layer A: preservation artifacts (never fails the capture)
        try:
            snapshot = self.snapshotter.snapshot(final_url, raw_html, extracted, stem)
        except Exception as e:
            logger.warning(f"Snapshot failed for {final_url}: {e}")
            snapshot = {"folder": None, "raw_html": None,
                        "extracted": None, "offline_html": None}

        # The LLM writes only the shell (summary/themes); pass it the extracted
        # text as context but instruct it not to reproduce the body.
        shell = self.llm.process_source_capture(capture, web_content, specs_dir)

        # Layer B: inject the preserved Page Content deterministically
        word_cap = int(self.config.get('link_capture', {}).get('note_content_word_cap', 2000))
        head, truncated = head_by_words(extracted, word_cap) if extracted else ("", False)
        section = self._render_page_content_section(snapshot, head, truncated)

        return self._insert_section_before_end(shell, section)

    @staticmethod
    def _render_page_content_section(
        snapshot: Dict[str, Any], head: str, truncated: bool,
    ) -> str:
        """Render the injected '## Page Content' + snapshot links."""
        lines = ["## Page Content", ""]
        if snapshot.get("folder"):
            links = [f"- Saved snapshot: `{snapshot['folder']}/`"]
            if snapshot.get("offline_html"):
                links.append(f"- Offline copy: [[{snapshot['offline_html']}]]")
            if snapshot.get("extracted"):
                links.append(f"- Full extracted text: [[{snapshot['extracted']}]]")
            lines += links + [""]
        if head:
            lines.append(head)
            if truncated and snapshot.get("extracted"):
                lines += ["", f"*Truncated — full text in [[{snapshot['extracted']}]].*"]
        elif not snapshot.get("folder"):
            lines.append("*Page content could not be preserved.*")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _insert_section_before_end(note: str, section: str) -> str:
        """
        Insert `section` near the end of the note. If the note ends with a
        trailing '---' horizontal rule (the source template does), insert
        before it; otherwise append.
        """
        stripped = note.rstrip()
        lines = stripped.split("\n")
        if lines and lines[-1].strip() == "---":
            body = "\n".join(lines[:-1]).rstrip()
            return f"{body}\n\n{section}\n---\n"
        return f"{stripped}\n\n{section}"

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
            return self.llm.process_telegram_capture(capture, specs_dir)

        doc_path = Path(document_paths[0])
        logger.info(f"Processing document capture {capture['id']}: {doc_path.name}")

        # Check if it's a PDF
        if doc_path.suffix.lower() != '.pdf':
            logger.warning(f"Non-PDF document: {doc_path.suffix}. Falling back to text processing.")
            return self.llm.process_telegram_capture(capture, specs_dir)

        # Extract text from PDF
        pdf_content = self.pdf_processor.extract_text(doc_path)

        if pdf_content['success']:
            logger.info(
                f"Successfully extracted text from PDF: {pdf_content['page_count']} pages, "
                f"{len(pdf_content['text'])} characters"
            )
            # Process with PDF-specific prompt
            return self.llm.process_pdf_capture(capture, pdf_content, specs_dir)
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
            return self.llm.process_pdf_capture(capture, pdf_content, specs_dir)

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

    parser = argparse.ArgumentParser(description="Kani-miso Processor")
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

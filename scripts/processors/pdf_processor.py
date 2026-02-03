"""
PDF Processor for Second Brain
Handles extracting text and metadata from PDF files.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import PDF libraries
# Try PyPDF2 first as it has fewer dependencies
HAS_PYPDF2 = False
HAS_PYPDF = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")

# Only try pypdf if PyPDF2 is not available (pypdf has more dependencies)
if not HAS_PYPDF2:
    try:
        from pypdf import PdfReader
        HAS_PYPDF = True
    except Exception as e:
        logger.warning(f"pypdf not available: {e}. Install with: pip install pypdf")


class PDFProcessor:
    """Extracts text and metadata from PDF files."""

    # Maximum pages to process (to avoid very large PDFs)
    MAX_PAGES = 100

    # Maximum characters to extract
    MAX_CHARS = 100000

    def __init__(self, max_pages: int = MAX_PAGES, max_chars: int = MAX_CHARS):
        """
        Initialize PDF processor.

        Args:
            max_pages: Maximum number of pages to process
            max_chars: Maximum characters to extract
        """
        self.max_pages = max_pages
        self.max_chars = max_chars

        if not HAS_PYPDF and not HAS_PYPDF2:
            logger.error("No PDF library available. Install pypdf or PyPDF2.")

    def extract_text(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract text content from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with:
                - success: bool
                - text: extracted text
                - metadata: PDF metadata
                - page_count: number of pages
                - pages_processed: pages actually processed
                - error: error message if failed
        """
        result = {
            'success': False,
            'text': '',
            'metadata': {},
            'page_count': 0,
            'pages_processed': 0,
            'error': None,
            'file_path': str(pdf_path),
            'file_name': pdf_path.name if pdf_path else 'Unknown',
        }

        if not pdf_path or not Path(pdf_path).exists():
            result['error'] = f"PDF file not found: {pdf_path}"
            return result

        # Try PyPDF2 first (more compatible, fewer dependencies)
        # Then fall back to pypdf if available
        if HAS_PYPDF2:
            return self._extract_with_pypdf2(pdf_path, result)
        elif HAS_PYPDF:
            return self._extract_with_pypdf(pdf_path, result)
        else:
            result['error'] = "No PDF library available. Install PyPDF2 or pypdf."
            return result

    def _extract_with_pypdf(self, pdf_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract using pypdf library."""
        try:
            reader = PdfReader(str(pdf_path))

            # Get metadata
            result['metadata'] = self._extract_metadata_pypdf(reader)
            result['page_count'] = len(reader.pages)

            # Extract text from pages
            text_parts = []
            pages_to_process = min(len(reader.pages), self.max_pages)
            total_chars = 0

            for i in range(pages_to_process):
                try:
                    page_text = reader.pages[i].extract_text() or ''
                    text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                    total_chars += len(page_text)
                    result['pages_processed'] = i + 1

                    if total_chars >= self.max_chars:
                        text_parts.append(f"\n[Content truncated at {self.max_chars} characters]")
                        break
                except Exception as e:
                    logger.warning(f"Error extracting page {i + 1}: {e}")
                    text_parts.append(f"--- Page {i + 1} ---\n[Error extracting page: {e}]")

            result['text'] = '\n\n'.join(text_parts)
            result['success'] = True

            if result['pages_processed'] < result['page_count']:
                logger.info(f"Processed {result['pages_processed']} of {result['page_count']} pages")

            logger.info(f"Successfully extracted {len(result['text'])} characters from {pdf_path.name}")
            return result

        except Exception as e:
            result['error'] = f"Error reading PDF: {str(e)}"
            logger.error(result['error'], exc_info=True)
            return result

    def _extract_with_pypdf2(self, pdf_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract using PyPDF2 library (fallback)."""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                # Get metadata
                result['metadata'] = self._extract_metadata_pypdf2(reader)
                result['page_count'] = len(reader.pages)

                # Extract text from pages
                text_parts = []
                pages_to_process = min(len(reader.pages), self.max_pages)
                total_chars = 0

                for i in range(pages_to_process):
                    try:
                        page_text = reader.pages[i].extract_text() or ''
                        text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
                        total_chars += len(page_text)
                        result['pages_processed'] = i + 1

                        if total_chars >= self.max_chars:
                            text_parts.append(f"\n[Content truncated at {self.max_chars} characters]")
                            break
                    except Exception as e:
                        logger.warning(f"Error extracting page {i + 1}: {e}")
                        text_parts.append(f"--- Page {i + 1} ---\n[Error extracting page: {e}]")

                result['text'] = '\n\n'.join(text_parts)
                result['success'] = True

                logger.info(f"Successfully extracted {len(result['text'])} characters from {pdf_path.name}")
                return result

        except Exception as e:
            result['error'] = f"Error reading PDF: {str(e)}"
            logger.error(result['error'], exc_info=True)
            return result

    def _extract_metadata_pypdf(self, reader: 'PdfReader') -> Dict[str, Any]:
        """Extract metadata using pypdf."""
        metadata = {}
        try:
            if reader.metadata:
                meta = reader.metadata
                metadata['title'] = meta.get('/Title', '') or ''
                metadata['author'] = meta.get('/Author', '') or ''
                metadata['subject'] = meta.get('/Subject', '') or ''
                metadata['creator'] = meta.get('/Creator', '') or ''
                metadata['producer'] = meta.get('/Producer', '') or ''

                # Handle creation date
                creation_date = meta.get('/CreationDate', '')
                if creation_date:
                    metadata['creation_date'] = self._parse_pdf_date(str(creation_date))
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def _extract_metadata_pypdf2(self, reader: 'PyPDF2.PdfReader') -> Dict[str, Any]:
        """Extract metadata using PyPDF2."""
        metadata = {}
        try:
            if reader.metadata:
                meta = reader.metadata
                metadata['title'] = meta.get('/Title', '') or ''
                metadata['author'] = meta.get('/Author', '') or ''
                metadata['subject'] = meta.get('/Subject', '') or ''
                metadata['creator'] = meta.get('/Creator', '') or ''
                metadata['producer'] = meta.get('/Producer', '') or ''

                creation_date = meta.get('/CreationDate', '')
                if creation_date:
                    metadata['creation_date'] = self._parse_pdf_date(str(creation_date))
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def _parse_pdf_date(self, date_str: str) -> Optional[str]:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO format.

        Args:
            date_str: PDF date string

        Returns:
            ISO date string or None
        """
        if not date_str:
            return None

        # PDF dates are like: D:20240115120000+00'00'
        try:
            # Remove D: prefix if present
            if date_str.startswith('D:'):
                date_str = date_str[2:]

            # Extract just the date/time part (first 14 chars)
            date_part = date_str[:14]
            if len(date_part) >= 8:
                year = date_part[0:4]
                month = date_part[4:6] if len(date_part) > 4 else '01'
                day = date_part[6:8] if len(date_part) > 6 else '01'
                hour = date_part[8:10] if len(date_part) > 8 else '00'
                minute = date_part[10:12] if len(date_part) > 10 else '00'
                second = date_part[12:14] if len(date_part) > 12 else '00'

                return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
        except Exception:
            pass

        return None

    def get_summary_info(self, pdf_result: Dict[str, Any]) -> str:
        """
        Generate a summary info string for the PDF.

        Args:
            pdf_result: Result from extract_text()

        Returns:
            Formatted summary string
        """
        metadata = pdf_result.get('metadata', {})
        lines = []

        if metadata.get('title'):
            lines.append(f"Title: {metadata['title']}")
        if metadata.get('author'):
            lines.append(f"Author: {metadata['author']}")
        if metadata.get('subject'):
            lines.append(f"Subject: {metadata['subject']}")

        lines.append(f"Pages: {pdf_result.get('page_count', 'Unknown')}")

        if pdf_result.get('pages_processed', 0) < pdf_result.get('page_count', 0):
            lines.append(f"Pages processed: {pdf_result['pages_processed']}")

        if metadata.get('creation_date'):
            lines.append(f"Created: {metadata['creation_date']}")

        return '\n'.join(lines)


def check_dependencies() -> Dict[str, bool]:
    """
    Check if PDF dependencies are installed.

    Returns:
        Dictionary with dependency status
    """
    return {
        'pypdf': HAS_PYPDF,
        'PyPDF2': HAS_PYPDF2,
    }


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from PDF files")
    parser.add_argument('pdf_path', nargs='?', help='Path to PDF file')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--max-pages', type=int, default=100, help='Max pages to process')
    args = parser.parse_args()

    if args.check_deps:
        deps = check_dependencies()
        print("Dependencies:")
        for dep, installed in deps.items():
            status = "✓ installed" if installed else "✗ not installed"
            print(f"  {dep}: {status}")
        sys.exit(0)

    if not args.pdf_path:
        parser.print_help()
        sys.exit(1)

    processor = PDFProcessor(max_pages=args.max_pages)
    result = processor.extract_text(Path(args.pdf_path))

    if result['success']:
        print(f"\n{processor.get_summary_info(result)}")
        print(f"\n{'=' * 60}\n")
        # Show first 2000 chars
        text = result['text']
        if len(text) > 2000:
            print(text[:2000] + "\n\n[... truncated for display ...]")
        else:
            print(text)
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)

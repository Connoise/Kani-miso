"""
Web Archiver for Second Brain
Handles capturing and archiving web content.

Based on specs/24-webpage-archival.md

Core Principle: URLs are references; content is meaning.
External material that prompted thought must remain accessible decades later.
"""

import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
import html

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger
from models.data_models import (
    SourceType,
    ArchiveMethod,
    ExtractionConfidence,
    SourceFrontmatter,
    SOURCE_MIN_WORD_COUNT,
    SOURCE_FETCH_TIMEOUT,
    SOURCE_MAX_RETRIES,
    SOURCE_RETRY_DELAYS,
    SOURCE_SLUG_MAX_LENGTH,
    validate_url,
    extract_domain_from_url,
    generate_source_slug,
    infer_source_type_from_url,
)

logger = setup_logger(__name__)


# =============================================================================
# Content Extraction Result
# =============================================================================

@dataclass
class ExtractionResult:
    """Result of content extraction from a webpage."""
    success: bool
    content: str = ""
    title: str = ""
    author: Optional[str] = None
    published_at: Optional[str] = None
    word_count: int = 0
    confidence: ExtractionConfidence = ExtractionConfidence.HIGH
    method: str = "auto"
    error: Optional[str] = None
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# =============================================================================
# Web Archiver Class
# =============================================================================

class WebArchiver:
    """
    Handles fetching and archiving web content.

    From 24-webpage-archival.md:
    - Full content preservation
    - Clean markdown conversion
    - Metadata extraction
    - Graceful degradation on failures
    """

    def __init__(self, repo_root: Path = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = repo_root
        self.sources_dir = repo_root / "sources"
        self.sources_dir.mkdir(exist_ok=True)

        # Try to import content extraction libraries
        self._trafilatura_available = False
        self._requests_available = False

        try:
            import trafilatura
            self._trafilatura_available = True
        except ImportError:
            logger.warning("trafilatura not installed - using basic extraction")

        try:
            import requests
            self._requests_available = True
        except ImportError:
            logger.warning("requests not installed - web archival disabled")

    def archive_url(self, url: str, user_summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Archive a URL to the sources directory.

        Args:
            url: The URL to archive
            user_summary: Optional user-provided summary if extraction fails

        Returns:
            Dict with:
                - success: bool
                - file_path: Path to created file (if successful)
                - title: Extracted or inferred title
                - word_count: Number of words in content
                - confidence: Extraction confidence level
                - error: Error message (if failed)
        """
        if not validate_url(url):
            return {
                'success': False,
                'error': f"Invalid URL format: {url}"
            }

        if not self._requests_available:
            return {
                'success': False,
                'error': "requests library not installed"
            }

        # Fetch and extract content
        extraction = self._fetch_and_extract(url)

        if not extraction.success and user_summary:
            # Fall back to user-provided summary
            extraction = ExtractionResult(
                success=True,
                content=user_summary,
                title=self._extract_title_from_url(url),
                word_count=len(user_summary.split()),
                confidence=ExtractionConfidence.LOW,
                method="manual",
                warnings=["Content extraction failed, using user-provided summary"]
            )

        if not extraction.success:
            return {
                'success': False,
                'error': extraction.error or "Content extraction failed"
            }

        # Generate file
        file_path = self._write_source_file(url, extraction)

        return {
            'success': True,
            'file_path': file_path,
            'title': extraction.title,
            'word_count': extraction.word_count,
            'confidence': extraction.confidence.value,
            'warnings': extraction.warnings
        }

    def _fetch_and_extract(self, url: str) -> ExtractionResult:
        """
        Fetch URL and extract main content.

        Implements retry logic from 24-webpage-archival.md:
        - Retry with exponential backoff (2s, 4s, 8s)
        """
        import requests

        # Fetch with retries
        html_content = None
        last_error = None

        for attempt, delay in enumerate(SOURCE_RETRY_DELAYS):
            try:
                response = requests.get(
                    url,
                    timeout=SOURCE_FETCH_TIMEOUT,
                    headers={
                        'User-Agent': 'SecondBrain/1.0 (Personal Archive)'
                    }
                )

                if response.status_code == 200:
                    html_content = response.text
                    break
                elif response.status_code in (401, 403):
                    return ExtractionResult(
                        success=False,
                        error=f"Access denied ({response.status_code}): Page requires authentication"
                    )
                elif response.status_code == 404:
                    return ExtractionResult(
                        success=False,
                        error="Page not found (404)"
                    )
                else:
                    last_error = f"HTTP {response.status_code}"

            except requests.Timeout:
                last_error = "Request timeout"
            except requests.RequestException as e:
                last_error = str(e)

            if attempt < len(SOURCE_RETRY_DELAYS) - 1:
                logger.info(f"Retry {attempt + 1} in {delay}s: {last_error}")
                time.sleep(delay)

        if html_content is None:
            return ExtractionResult(
                success=False,
                error=f"Failed to fetch after {len(SOURCE_RETRY_DELAYS)} attempts: {last_error}"
            )

        # Extract content
        return self._extract_content(html_content, url)

    def _extract_content(self, html_content: str, url: str) -> ExtractionResult:
        """
        Extract main content from HTML.

        Uses trafilatura if available, falls back to basic extraction.
        """
        warnings = []

        if self._trafilatura_available:
            import trafilatura

            # Extract with trafilatura
            content = trafilatura.extract(
                html_content,
                include_links=True,
                include_formatting=True,
                include_images=True,
                output_format='markdown',
                favor_recall=True
            )

            metadata = trafilatura.extract_metadata(html_content)

            if content and len(content.split()) >= SOURCE_MIN_WORD_COUNT:
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=metadata.title if metadata else self._extract_title_from_html(html_content),
                    author=metadata.author if metadata else None,
                    published_at=metadata.date if metadata else None,
                    word_count=len(content.split()),
                    confidence=ExtractionConfidence.HIGH,
                    method="trafilatura"
                )
            else:
                warnings.append("trafilatura extraction returned insufficient content")

        # Fall back to basic extraction
        content, title = self._basic_html_extraction(html_content)

        if content:
            word_count = len(content.split())
            confidence = ExtractionConfidence.MEDIUM if word_count >= SOURCE_MIN_WORD_COUNT else ExtractionConfidence.LOW

            if word_count < SOURCE_MIN_WORD_COUNT:
                warnings.append(f"Low word count ({word_count}), content may be incomplete")

            return ExtractionResult(
                success=True,
                content=content,
                title=title or self._extract_title_from_url(url),
                word_count=word_count,
                confidence=confidence,
                method="basic",
                warnings=warnings
            )

        return ExtractionResult(
            success=False,
            error="Could not extract meaningful content from page",
            warnings=warnings
        )

    def _basic_html_extraction(self, html_content: str) -> Tuple[str, Optional[str]]:
        """
        Basic HTML to markdown conversion.

        Used when trafilatura is not available or fails.
        """
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        title = html.unescape(title_match.group(1).strip()) if title_match else None

        # Remove scripts, styles, nav, footer, header
        content = html_content
        for pattern in [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<header[^>]*>.*?</header>',
            r'<aside[^>]*>.*?</aside>',
            r'<!--.*?-->',
        ]:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)

        # Find main content area
        main_match = re.search(r'<(?:main|article)[^>]*>(.*?)</(?:main|article)>', content, re.DOTALL | re.IGNORECASE)
        if main_match:
            content = main_match.group(1)

        # Convert HTML to markdown-ish text
        # Headers
        content = re.sub(r'<h1[^>]*>([^<]+)</h1>', r'# \1\n\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<h2[^>]*>([^<]+)</h2>', r'## \1\n\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<h3[^>]*>([^<]+)</h3>', r'### \1\n\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<h[4-6][^>]*>([^<]+)</h[4-6]>', r'#### \1\n\n', content, flags=re.IGNORECASE)

        # Paragraphs and line breaks
        content = re.sub(r'<p[^>]*>', '\n\n', content, flags=re.IGNORECASE)
        content = re.sub(r'</p>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)

        # Lists
        content = re.sub(r'<li[^>]*>', '\n- ', content, flags=re.IGNORECASE)
        content = re.sub(r'</li>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</?[uo]l[^>]*>', '\n', content, flags=re.IGNORECASE)

        # Links
        content = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', r'[\2](\1)', content, flags=re.IGNORECASE)

        # Emphasis
        content = re.sub(r'<(?:strong|b)[^>]*>([^<]+)</(?:strong|b)>', r'**\1**', content, flags=re.IGNORECASE)
        content = re.sub(r'<(?:em|i)[^>]*>([^<]+)</(?:em|i)>', r'*\1*', content, flags=re.IGNORECASE)

        # Code
        content = re.sub(r'<code[^>]*>([^<]+)</code>', r'`\1`', content, flags=re.IGNORECASE)
        content = re.sub(r'<pre[^>]*>([^<]+)</pre>', r'```\n\1\n```', content, flags=re.IGNORECASE)

        # Blockquotes
        content = re.sub(r'<blockquote[^>]*>([^<]+)</blockquote>', r'> \1\n', content, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)

        # Decode HTML entities
        content = html.unescape(content)

        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = content.strip()

        return content, title

    def _extract_title_from_html(self, html_content: str) -> str:
        """Extract title from HTML."""
        # Try <title> tag
        match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())

        # Try <h1> tag
        match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())

        # Try og:title
        match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if match:
            return html.unescape(match.group(1).strip())

        return "Untitled"

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a title from URL path."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if path:
            # Get last path segment
            segment = path.split('/')[-1]
            # Remove extension
            segment = re.sub(r'\.[^.]+$', '', segment)
            # Convert to title case
            title = segment.replace('-', ' ').replace('_', ' ').title()
            return title

        return parsed.netloc

    def _write_source_file(self, url: str, extraction: ExtractionResult) -> Path:
        """
        Write extracted content to source file.

        From 24-webpage-archival.md - File structure.
        """
        domain = extract_domain_from_url(url)
        source_type = infer_source_type_from_url(url)
        slug = generate_source_slug(extraction.title)
        date_str = datetime.now().strftime('%Y-%m-%d')

        filename = f"{date_str}--{slug}.md"
        file_path = self.sources_dir / filename

        # Handle duplicates
        counter = 2
        while file_path.exists():
            filename = f"{date_str}--{slug}-{counter}.md"
            file_path = self.sources_dir / filename
            counter += 1

        # Build frontmatter
        frontmatter_lines = [
            "---",
            "type: source",
            f"source_type: {source_type.value}",
            f"url: {url}",
            f"captured_at: {datetime.now().isoformat()}",
            f"title: {extraction.title}",
            f"domain: {domain}",
        ]

        if extraction.author:
            frontmatter_lines.append(f"author: {extraction.author}")
        if extraction.published_at:
            frontmatter_lines.append(f"published_at: {extraction.published_at}")

        frontmatter_lines.extend([
            f"word_count: {extraction.word_count}",
            f"archive_method: {extraction.method}",
            f"extraction_confidence: {extraction.confidence.value}",
            "---",
        ])

        frontmatter = "\n".join(frontmatter_lines)

        # Build content
        content = f"""{frontmatter}

# {extraction.title}

*Archived from: [{domain}]({url})*
*Captured: {date_str}*
{f"*Author: {extraction.author}*" if extraction.author else ""}

---

{extraction.content}

---

## Archive Notes

- Archive method: {extraction.method}
- Extraction confidence: {extraction.confidence.value}
{chr(10).join(f"- Warning: {w}" for w in extraction.warnings) if extraction.warnings else ""}
"""

        file_path.write_text(content.strip(), encoding='utf-8')
        logger.info(f"Archived source: {file_path.name} ({extraction.word_count} words)")

        return file_path

    def audit_sources(self) -> Dict[str, Any]:
        """
        Audit existing sources for quality issues.

        From 24-webpage-archival.md - Archive Maintenance.

        Returns summary of:
        - Sources with only URLs (no content)
        - Sources with low word counts
        - Sources with low confidence
        """
        url_only = []
        low_word_count = []
        low_confidence = []

        for source_file in self.sources_dir.glob("*.md"):
            try:
                content = source_file.read_text(encoding='utf-8')

                # Parse frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        import yaml
                        fm = yaml.safe_load(parts[1])
                        body = parts[2]

                        # Check for URL-only
                        word_count = fm.get('word_count', 0)
                        if word_count == 0:
                            # Check if body has content
                            body_words = len(body.split())
                            if body_words < SOURCE_MIN_WORD_COUNT:
                                url_only.append({
                                    'file': source_file.name,
                                    'url': fm.get('url', ''),
                                    'word_count': body_words
                                })

                        # Check low word count
                        if 0 < word_count < SOURCE_MIN_WORD_COUNT:
                            low_word_count.append({
                                'file': source_file.name,
                                'word_count': word_count
                            })

                        # Check low confidence
                        if fm.get('extraction_confidence') == 'low':
                            low_confidence.append({
                                'file': source_file.name,
                                'url': fm.get('url', '')
                            })

            except Exception as e:
                logger.warning(f"Error auditing {source_file.name}: {e}")

        return {
            'total_sources': len(list(self.sources_dir.glob("*.md"))),
            'url_only': url_only,
            'low_word_count': low_word_count,
            'low_confidence': low_confidence,
            'needs_attention': len(url_only) + len(low_word_count) + len(low_confidence)
        }

    def rearchive_source(self, source_file: Path) -> Dict[str, Any]:
        """
        Attempt to re-archive a source that has incomplete content.

        From 24-webpage-archival.md - Legacy Migration.
        """
        try:
            content = source_file.read_text(encoding='utf-8')

            # Extract URL from frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    fm = yaml.safe_load(parts[1])
                    url = fm.get('url')

                    if url:
                        # Archive the URL again
                        result = self.archive_url(url)

                        if result['success']:
                            # Remove old file
                            source_file.unlink()
                            logger.info(f"Re-archived {source_file.name} -> {result['file_path'].name}")
                            return {
                                'success': True,
                                'old_file': source_file.name,
                                'new_file': result['file_path'].name,
                                'word_count': result['word_count']
                            }

                        return {
                            'success': False,
                            'file': source_file.name,
                            'error': result.get('error', 'Re-archival failed')
                        }

            return {
                'success': False,
                'file': source_file.name,
                'error': 'No URL found in source file'
            }

        except Exception as e:
            return {
                'success': False,
                'file': source_file.name,
                'error': str(e)
            }


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI for web archiver."""
    import argparse

    parser = argparse.ArgumentParser(description="Web Archiver for Second Brain")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # archive command
    archive_parser = subparsers.add_parser('archive', help='Archive a URL')
    archive_parser.add_argument('url', help='URL to archive')
    archive_parser.add_argument('--summary', '-s', help='User-provided summary if extraction fails')

    # audit command
    subparsers.add_parser('audit', help='Audit existing sources')

    # rearchive command
    rearchive_parser = subparsers.add_parser('rearchive', help='Re-archive a source file')
    rearchive_parser.add_argument('file', help='Source file to re-archive')

    args = parser.parse_args()

    archiver = WebArchiver()

    if args.command == 'archive':
        print(f"Archiving: {args.url}")
        result = archiver.archive_url(args.url, args.summary)

        if result['success']:
            print(f"\nArchived successfully!")
            print(f"  File: {result['file_path'].name}")
            print(f"  Title: {result['title']}")
            print(f"  Words: {result['word_count']}")
            print(f"  Confidence: {result['confidence']}")
            if result.get('warnings'):
                print(f"  Warnings:")
                for w in result['warnings']:
                    print(f"    - {w}")
        else:
            print(f"\nArchival failed: {result['error']}")

    elif args.command == 'audit':
        print("Auditing sources...")
        result = archiver.audit_sources()

        print(f"\n{'=' * 50}")
        print(f"Source Audit Report")
        print(f"{'=' * 50}")
        print(f"Total sources: {result['total_sources']}")
        print(f"Needs attention: {result['needs_attention']}")

        if result['url_only']:
            print(f"\nURL-only sources ({len(result['url_only'])}):")
            for item in result['url_only'][:10]:
                print(f"  - {item['file']} ({item['word_count']} words)")

        if result['low_word_count']:
            print(f"\nLow word count ({len(result['low_word_count'])}):")
            for item in result['low_word_count'][:10]:
                print(f"  - {item['file']} ({item['word_count']} words)")

        if result['low_confidence']:
            print(f"\nLow confidence ({len(result['low_confidence'])}):")
            for item in result['low_confidence'][:10]:
                print(f"  - {item['file']}")

    elif args.command == 'rearchive':
        source_file = Path(args.file)
        if not source_file.exists():
            source_file = archiver.sources_dir / args.file

        if not source_file.exists():
            print(f"File not found: {args.file}")
            return

        print(f"Re-archiving: {source_file.name}")
        result = archiver.rearchive_source(source_file)

        if result['success']:
            print(f"Re-archived successfully!")
            print(f"  Old: {result['old_file']}")
            print(f"  New: {result['new_file']}")
            print(f"  Words: {result['word_count']}")
        else:
            print(f"Re-archival failed: {result['error']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

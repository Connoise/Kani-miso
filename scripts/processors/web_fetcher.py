"""
Web Fetcher for Kani-miso
Handles fetching webpages and converting HTML to markdown.
"""

import re
import html
import ipaddress
import socket
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
import requests

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import optional dependencies
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")

try:
    import html2text
    HAS_HTML2TEXT = True
except ImportError:
    HAS_HTML2TEXT = False
    logger.warning("html2text not installed. Install with: pip install html2text")


class WebFetcher:
    """Fetches webpages and converts them to markdown."""

    # Common user agent to avoid being blocked
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Timeout for requests
    DEFAULT_TIMEOUT = 30

    # Maximum content size (10MB)
    MAX_CONTENT_SIZE = 10 * 1024 * 1024

    # Redirect hops before giving up; each hop is re-validated against the
    # private-address blocklist (SSRF guard)
    MAX_REDIRECTS = 5

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize web fetcher.

        Args:
            user_agent: Custom user agent string
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

        # Configure html2text if available
        if HAS_HTML2TEXT:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.ignore_images = False
            self.h2t.ignore_emphasis = False
            self.h2t.body_width = 0  # Don't wrap lines
            self.h2t.unicode_snob = True
            self.h2t.skip_internal_links = True
            self.h2t.inline_links = True
            self.h2t.protect_links = True
        else:
            self.h2t = None

    def is_valid_url(self, url: str) -> bool:
        """
        Check if a string is a valid URL.

        Args:
            url: String to check

        Returns:
            True if valid URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

    def _validate_target(self, url: str) -> None:
        """
        SSRF guard: refuse to fetch hosts that resolve to private, loopback,
        link-local, or otherwise non-public addresses (cloud metadata, LAN
        services, localhost). Called for the initial URL and for every
        redirect hop.

        Note: the address is re-resolved by requests when connecting, so a
        DNS-rebinding attacker with a sub-second TTL could still flip the
        record between check and use. Accepted residual risk for a
        single-user local tool; pinning the resolved IP would require a
        custom transport adapter.

        Raises:
            ValueError: If the URL is invalid or resolves to a blocked range.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise ValueError(f"Invalid or unsupported URL: {url}")

        hostname = parsed.hostname
        try:
            addr_info = socket.getaddrinfo(hostname, parsed.port or 0,
                                           proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise ValueError(f"Could not resolve host {hostname!r}: {e}")

        for family, _type, _proto, _canon, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
                raise ValueError(
                    f"Refusing to fetch {hostname!r}: resolves to "
                    f"non-public address {ip} (SSRF guard)"
                )

    def extract_url_from_text(self, text: str) -> Optional[str]:
        """
        Extract the first URL from a text string.

        Args:
            text: Text that may contain URLs

        Returns:
            First URL found, or None
        """
        # URL pattern that matches http/https URLs
        # This pattern handles most URLs including those with parentheses (Wikipedia)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, text)
        if match:
            url = match.group(0)

            # Balance parentheses for URLs like Wikipedia
            # Count open and close parens in the URL
            open_parens = url.count('(')
            close_parens = url.count(')')

            # If we have more open than close, and the next char after match is ')',
            # extend the URL to include balancing parens
            if open_parens > close_parens:
                end_pos = match.end()
                remaining = text[end_pos:]
                parens_needed = open_parens - close_parens
                for i, char in enumerate(remaining):
                    if char == ')' and parens_needed > 0:
                        url += char
                        parens_needed -= 1
                    elif char in ' \t\n<>"':
                        break
                    else:
                        break

            # Clean up trailing punctuation that might be captured
            # But preserve balanced parentheses
            while url and url[-1] in '.,;:!?\'"':
                url = url[:-1]

            # Final cleanup: remove trailing ) only if unbalanced
            while url.count(')') > url.count('(') and url.endswith(')'):
                url = url[:-1]

            return url
        return None

    def fetch_url(self, url: str) -> Tuple[str, Dict[str, str]]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (html_content, response_headers)

        Raises:
            requests.RequestException: On network errors
            ValueError: On content too large or invalid content type
        """
        logger.info(f"Fetching URL: {url}")

        # Follow redirects manually so every hop passes the SSRF guard and
        # the chain length is bounded.
        current_url = url
        response = None
        for _hop in range(self.MAX_REDIRECTS + 1):
            self._validate_target(current_url)

            response = self.session.get(
                current_url,
                timeout=self.timeout,
                allow_redirects=False,
                stream=True,
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get('Location')
                response.close()
                if not location:
                    raise ValueError("Redirect response without Location header")
                current_url = urljoin(current_url, location)
                logger.info(f"Following redirect to: {current_url}")
                continue
            break
        else:
            raise ValueError(f"Too many redirects (more than {self.MAX_REDIRECTS})")

        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        if not any(ct in content_type for ct in ['text/html', 'application/xhtml+xml']):
            raise ValueError(f"Unsupported content type: {content_type}")

        # Check content size
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > self.MAX_CONTENT_SIZE:
            raise ValueError(f"Content too large: {content_length} bytes")

        # Read content with size limit
        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > self.MAX_CONTENT_SIZE:
                raise ValueError("Content exceeded maximum size during download")

        # Detect encoding
        encoding = response.encoding or 'utf-8'
        try:
            html_content = content.decode(encoding)
        except UnicodeDecodeError:
            html_content = content.decode('utf-8', errors='replace')

        logger.info(f"Fetched {len(content)} bytes from {current_url}")
        headers = dict(response.headers)
        headers['x-kanimiso-final-url'] = current_url
        return html_content, headers

    def extract_metadata(self, soup: 'BeautifulSoup', url: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML using BeautifulSoup.

        Args:
            soup: BeautifulSoup object
            url: Original URL (for domain info)

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'title': None,
            'author': None,
            'date': None,
            'description': None,
            'site_name': None,
            'url': url,
            'domain': urlparse(url).netloc,
        }

        # Extract title
        # Priority: og:title > twitter:title > <title>
        og_title = soup.find('meta', property='og:title')
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        title_tag = soup.find('title')

        if og_title and og_title.get('content'):
            metadata['title'] = og_title['content'].strip()
        elif twitter_title and twitter_title.get('content'):
            metadata['title'] = twitter_title['content'].strip()
        elif title_tag and title_tag.string:
            metadata['title'] = title_tag.string.strip()

        # Extract author
        # Check various meta tags
        author_selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'twitter:creator'}),
            ('meta', {'property': 'og:article:author'}),
        ]
        for tag, attrs in author_selectors:
            elem = soup.find(tag, attrs)
            if elem and elem.get('content'):
                metadata['author'] = elem['content'].strip()
                break

        # Also check for author in JSON-LD
        ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if 'author' in data:
                        author = data['author']
                        if isinstance(author, dict):
                            metadata['author'] = author.get('name', str(author))
                        elif isinstance(author, str):
                            metadata['author'] = author
                        break
            except (json.JSONDecodeError, TypeError):
                continue

        # Extract publication date
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'date'}),
            ('meta', {'name': 'publish-date'}),
            ('meta', {'property': 'og:article:published_time'}),
            ('time', {'datetime': True}),
        ]
        for tag, attrs in date_selectors:
            if tag == 'time':
                elem = soup.find(tag, datetime=True)
                if elem:
                    metadata['date'] = elem.get('datetime', '').strip()
                    break
            else:
                elem = soup.find(tag, attrs)
                if elem and elem.get('content'):
                    metadata['date'] = elem['content'].strip()
                    break

        # Extract description
        desc_selectors = [
            ('meta', {'property': 'og:description'}),
            ('meta', {'name': 'description'}),
            ('meta', {'name': 'twitter:description'}),
        ]
        for tag, attrs in desc_selectors:
            elem = soup.find(tag, attrs)
            if elem and elem.get('content'):
                metadata['description'] = elem['content'].strip()
                break

        # Extract site name
        site_selectors = [
            ('meta', {'property': 'og:site_name'}),
            ('meta', {'name': 'application-name'}),
        ]
        for tag, attrs in site_selectors:
            elem = soup.find(tag, attrs)
            if elem and elem.get('content'):
                metadata['site_name'] = elem['content'].strip()
                break

        return metadata

    def extract_main_content(self, soup: 'BeautifulSoup') -> str:
        """
        Extract the main content from HTML, removing navigation, ads, etc.

        Args:
            soup: BeautifulSoup object

        Returns:
            HTML string of main content
        """
        # Create a copy to avoid modifying the original
        soup = BeautifulSoup(str(soup), 'html.parser')

        # Remove unwanted elements
        unwanted_selectors = [
            'script', 'style', 'nav', 'header', 'footer',
            'aside', 'noscript', 'iframe', 'form',
            '[role="navigation"]', '[role="banner"]',
            '[role="complementary"]', '[role="contentinfo"]',
            '.navigation', '.nav', '.menu', '.sidebar',
            '.header', '.footer', '.advertisement', '.ad',
            '.social-share', '.comments', '.related-posts',
            '#comments', '#sidebar', '#navigation',
        ]

        for selector in unwanted_selectors:
            for elem in soup.select(selector):
                elem.decompose()

        # Try to find main content container
        # Priority: article > main > [role="main"] > .content > body
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.post-content',
            '.article-content',
            '.entry-content',
            '.content',
            '.post',
            '#content',
            '#main',
        ]

        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if main_content:
            return str(main_content)
        else:
            # Fall back to body
            body = soup.find('body')
            return str(body) if body else str(soup)

    def html_to_markdown(self, html_content: str, base_url: str = '') -> str:
        """
        Convert HTML to markdown.

        Args:
            html_content: HTML string
            base_url: Base URL for resolving relative links

        Returns:
            Markdown string
        """
        if HAS_HTML2TEXT and self.h2t:
            if base_url:
                self.h2t.baseurl = base_url
            markdown = self.h2t.handle(html_content)
        else:
            # Fallback: basic HTML stripping
            markdown = self._basic_html_to_text(html_content)

        # Clean up the markdown
        markdown = self._clean_markdown(markdown)
        return markdown

    def _basic_html_to_text(self, html_content: str) -> str:
        """
        Basic HTML to text conversion without external dependencies.

        Args:
            html_content: HTML string

        Returns:
            Plain text with basic formatting
        """
        if HAS_BS4:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Convert some tags to markdown-style
            for tag in soup.find_all('strong'):
                tag.replace_with(f"**{tag.get_text()}**")
            for tag in soup.find_all('b'):
                tag.replace_with(f"**{tag.get_text()}**")
            for tag in soup.find_all('em'):
                tag.replace_with(f"*{tag.get_text()}*")
            for tag in soup.find_all('i'):
                tag.replace_with(f"*{tag.get_text()}*")
            for tag in soup.find_all('a'):
                href = tag.get('href', '')
                text = tag.get_text()
                tag.replace_with(f"[{text}]({href})")

            # Get text
            text = soup.get_text(separator='\n')
        else:
            # Very basic: just strip tags
            text = re.sub(r'<[^>]+>', '', html_content)
            text = html.unescape(text)

        return text

    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up generated markdown.

        Args:
            markdown: Raw markdown string

        Returns:
            Cleaned markdown
        """
        # Remove excessive blank lines (more than 2)
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in markdown.split('\n')]
        markdown = '\n'.join(lines)

        # Remove leading/trailing whitespace
        markdown = markdown.strip()

        return markdown

    def fetch_and_convert(self, url: str) -> Dict[str, Any]:
        """
        Fetch a URL and convert to markdown with metadata.

        This is the main entry point for processing URLs.

        Args:
            url: URL to fetch and convert

        Returns:
            Dictionary with:
                - success: bool
                - url: original URL
                - metadata: extracted metadata dict
                - markdown_content: converted content
                - error: error message if failed
        """
        result = {
            'success': False,
            'url': url,
            'final_url': url,
            'metadata': {},
            'markdown_content': '',
            'html': '',
            'error': None,
        }

        if not HAS_BS4:
            result['error'] = "beautifulsoup4 is required. Install with: pip install beautifulsoup4"
            return result

        try:
            # Validate URL
            if not self.is_valid_url(url):
                result['error'] = f"Invalid URL: {url}"
                return result

            # Fetch the page (raw HTML is kept for the preservation layer)
            html_content, headers = self.fetch_url(url)
            final_url = headers.get('x-kanimiso-final-url', url)
            result['html'] = html_content
            result['final_url'] = final_url

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract metadata (relative links resolve against the final URL)
            result['metadata'] = self.extract_metadata(soup, final_url)

            # Extract main content
            main_content = self.extract_main_content(soup)

            # Convert to markdown
            result['markdown_content'] = self.html_to_markdown(main_content, final_url)

            result['success'] = True
            logger.info(f"Successfully processed URL: {url}")

        except requests.Timeout:
            result['error'] = f"Request timed out after {self.timeout} seconds"
            logger.error(result['error'])

        except requests.RequestException as e:
            result['error'] = f"Failed to fetch URL: {str(e)}"
            logger.error(result['error'])

        except ValueError as e:
            result['error'] = str(e)
            logger.error(result['error'])

        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            logger.error(result['error'], exc_info=True)

        return result


def check_dependencies() -> Dict[str, bool]:
    """
    Check if optional dependencies are installed.

    Returns:
        Dictionary with dependency status
    """
    return {
        'beautifulsoup4': HAS_BS4,
        'html2text': HAS_HTML2TEXT,
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Fetch and convert webpage to markdown")
    parser.add_argument('url', nargs='?', help='URL to fetch')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    args = parser.parse_args()

    if args.check_deps:
        deps = check_dependencies()
        print("Dependencies:")
        for dep, installed in deps.items():
            status = "✓ installed" if installed else "✗ not installed"
            print(f"  {dep}: {status}")
        sys.exit(0)

    if not args.url:
        parser.print_help()
        sys.exit(1)

    fetcher = WebFetcher()
    result = fetcher.fetch_and_convert(args.url)

    if result['success']:
        print(f"Title: {result['metadata'].get('title', 'N/A')}")
        print(f"Author: {result['metadata'].get('author', 'N/A')}")
        print(f"Date: {result['metadata'].get('date', 'N/A')}")
        print(f"Description: {result['metadata'].get('description', 'N/A')[:100]}...")
        print("\n--- Content ---\n")
        print(result['markdown_content'][:2000] + "..." if len(result['markdown_content']) > 2000 else result['markdown_content'])
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)

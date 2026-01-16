"""
Filename slugification utility.
Converts titles to safe, readable filenames.
"""

import re
from slugify import slugify as _slugify


def create_slug(text: str, max_length: int = 50) -> str:
    """
    Convert text to a URL-safe slug suitable for filenames.

    Args:
        text: The text to slugify
        max_length: Maximum length of slug

    Returns:
        Slugified string (lowercase, hyphens, no special chars)

    Examples:
        >>> create_slug("Testing Claude")
        'testing-claude'
        >>> create_slug("Is this note taking process currently working?")
        'is-this-note-taking-process-currently-working'
    """
    # Use python-slugify library for robust conversion
    slug = _slugify(text, max_length=max_length, word_boundary=True, separator='-')

    # Fallback if slugify returns empty (e.g., all non-ASCII)
    if not slug:
        # Simple ASCII fallback
        slug = re.sub(r'[^a-z0-9]+', '-', text.lower())
        slug = slug.strip('-')[:max_length]

    # Ensure not empty
    if not slug:
        slug = "untitled"

    return slug


def generate_filename(date_str: str, title: str, extension: str = "md") -> str:
    """
    Generate a filename following the convention: YYYY-MM-DD--slug.ext

    Args:
        date_str: Date string in YYYY-MM-DD format
        title: Title to slugify
        extension: File extension (default: md)

    Returns:
        Formatted filename

    Examples:
        >>> generate_filename("2026-01-09", "Testing Claude")
        '2026-01-09--testing-claude.md'
    """
    slug = create_slug(title)
    return f"{date_str}--{slug}.{extension}"

"""
Markdown and wikilink parser for Kani-miso viewer.
Handles frontmatter, wikilink extraction, and markdown rendering.
"""

import re
import yaml
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from datetime import datetime
import markdown2


@dataclass
class Link:
    """Represents a wikilink in note content."""
    target: str      # The linked note/hub name
    section: Optional[str]  # Section anchor (or None)
    alias: Optional[str]    # Display text (or None)


# Regex pattern for wikilinks: [[target]], [[target#section]], [[target|alias]], [[target#section|alias]]
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]')

# Regex pattern for Obsidian image embeds: ![[image.jpg]], ![[path/to/image.png]]
IMAGE_EMBED_PATTERN = re.compile(r'!\[\[([^\]]+)\]\]')

# Common image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter from markdown content.

    Returns:
        tuple of (frontmatter_dict, remaining_content)
    """
    if not content.startswith('---'):
        return {}, content

    # Find the closing ---
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        if frontmatter is None:
            frontmatter = {}
        return frontmatter, parts[2].strip()
    except yaml.YAMLError:
        # Malformed YAML - return empty frontmatter but preserve content
        return {}, content


def extract_links(content: str) -> list[Link]:
    """
    Extract all wikilinks from content.

    Args:
        content: Markdown content

    Returns:
        List of Link objects
    """
    links = []
    for match in WIKILINK_PATTERN.finditer(content):
        target = match.group(1).strip()
        section = match.group(2).strip() if match.group(2) else None
        alias = match.group(3).strip() if match.group(3) else None
        links.append(Link(target=target, section=section, alias=alias))
    return links


def slugify_heading(heading: str) -> str:
    """
    Convert markdown heading to URL-safe anchor.

    Args:
        heading: Heading text

    Returns:
        URL-safe slug

    Examples:
        "What This Hub Is" -> "what-this-hub-is"
        "AI & Machine Learning" -> "ai-machine-learning"
    """
    # Convert to lowercase
    slug = heading.lower()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove punctuation except hyphens and underscores
    slug = re.sub(r'[^\w\-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def generate_heading_anchors(content: str) -> dict[str, int]:
    """
    Generate anchor IDs for all headings in markdown content.
    Tracks duplicates and adds numeric suffixes.

    Args:
        content: Markdown content

    Returns:
        Dict mapping heading text to occurrence count
    """
    heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
    heading_counts = {}

    for match in heading_pattern.finditer(content):
        heading_text = match.group(1).strip()
        slug = slugify_heading(heading_text)
        heading_counts[slug] = heading_counts.get(slug, 0) + 1

    return heading_counts


def is_image_path(path: str) -> bool:
    """
    Check if a path refers to an image file.

    Args:
        path: File path to check

    Returns:
        True if path has an image extension
    """
    ext = Path(path).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def render_markdown(content: str, vault_path: Path, note_path: Path, known_files: set[str]) -> str:
    """
    Render markdown to HTML with wikilink and image embed conversion.

    Args:
        content: Markdown content
        vault_path: Path to vault root
        note_path: Path to the current note file
        known_files: Set of known filenames (lowercase) in vault

    Returns:
        Rendered HTML
    """
    # First, replace Obsidian image embeds with HTML img tags
    def replace_image_embed(match):
        image_path = match.group(1).strip()

        # Normalize path separators
        image_path_normalized = image_path.replace("\\", "/")

        # Build the src URL (will be served by /vault-image/ route)
        src = f"/vault-image/{image_path_normalized}"

        # Get just the filename for alt text
        alt_text = Path(image_path).name

        return f'<img src="{src}" alt="{alt_text}" class="vault-image" loading="lazy">'

    # Replace image embeds first (before wikilinks to avoid conflicts)
    content_with_images = IMAGE_EMBED_PATTERN.sub(replace_image_embed, content)

    # Then, replace wikilinks with proper HTML links
    def replace_wikilink(match):
        target = match.group(1).strip()
        section = match.group(2).strip() if match.group(2) else None
        alias = match.group(3).strip() if match.group(3) else target

        # Check if this is an image (shouldn't happen after image embed replacement, but just in case)
        if is_image_path(target):
            src = f"/vault-image/{target.replace(chr(92), '/')}"
            return f'<img src="{src}" alt="{Path(target).name}" class="vault-image" loading="lazy">'

        # Check if target exists (case-insensitive)
        target_lower = target.lower()
        is_dead = target_lower not in known_files

        # Build href
        if section:
            href = f"/note/{target}#{slugify_heading(section)}"
        else:
            href = f"/note/{target}"

        # Build HTML
        if is_dead:
            return f'<a class="dead-link" title="Target not found">{alias}</a>'
        else:
            return f'<a href="{href}">{alias}</a>'

    content_with_links = WIKILINK_PATTERN.sub(replace_wikilink, content_with_images)

    # Render markdown to HTML
    html = markdown2.markdown(
        content_with_links,
        extras=[
            'fenced-code-blocks',
            'tables',
            'header-ids',
            'code-friendly',
            'cuddled-lists',
            'metadata',
            'task_list'
        ]
    )

    return html


def parse_note(file_path: Path) -> dict:
    """
    Parse a note file and extract all metadata.

    Args:
        file_path: Path to note file

    Returns:
        Dict with parsed note data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = extract_frontmatter(content)
    links = extract_links(body)

    # Extract first paragraph for preview
    lines = body.split('\n')
    preview_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            preview_lines.append(line)
            if len(' '.join(preview_lines)) >= 150:
                break

    preview = ' '.join(preview_lines)[:150]

    return {
        'path': str(file_path),
        'filename': file_path.name,
        'frontmatter': frontmatter,
        'body': body,
        'links': links,
        'preview': preview,
        'title': frontmatter.get('title') or file_path.stem
    }

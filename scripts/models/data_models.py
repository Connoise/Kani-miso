"""
Formal Data Models for Second Brain.
Based on specs/13-formal-data-model.md and specs/24-webpage-archival.md

This module defines all entity types, status values, and validation rules
as specified in the formal data model specification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
import re


# =============================================================================
# Status Enums (from 06-tagging-ontology.md and 13-formal-data-model.md)
# =============================================================================

class NoteStatus(Enum):
    """Valid status values for notes."""
    RAW = "raw"
    PROCESSED = "processed"
    EVOLVING = "evolving"
    EVERGREEN = "evergreen"
    DORMANT = "dormant"
    OBSOLETE = "obsolete"


class HubStatus(Enum):
    """Valid status values for hubs."""
    EMPTY = "empty"
    ACTIVE = "active"
    DORMANT = "dormant"
    OBSOLETE = "obsolete"


class ProjectStatus(Enum):
    """Valid status values for projects."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class CertaintyLevel(Enum):
    """Certainty levels for notes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CaptureMode(Enum):
    """Capture modes for notes."""
    QUICK = "quick"
    EXTENDED = "extended"
    VOICE = "voice"
    IMAGE = "image"


class CaptureSurface(Enum):
    """Valid capture surfaces."""
    MOBILE = "mobile"
    DESKTOP_WORK = "desktop-work"
    DESKTOP_HOME = "desktop-home"
    TELEGRAM = "telegram"
    UNKNOWN = "unknown"


class SourceType(Enum):
    """Valid source types (from 24-webpage-archival.md)."""
    ARTICLE = "article"
    BLOG = "blog"
    PDF = "pdf"
    BOOK = "book"
    VIDEO = "video"
    CONVERSATION = "conversation"
    WIKIPEDIA = "wikipedia"
    ACADEMIC = "academic"
    DOCUMENTATION = "documentation"
    SOCIAL_MEDIA = "social_media"


class ArchiveMethod(Enum):
    """How the source was archived (from 24-webpage-archival.md)."""
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


class ExtractionConfidence(Enum):
    """Confidence level of content extraction (from 24-webpage-archival.md)."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EntityType(Enum):
    """Valid entity types."""
    NOTE = "note"
    REFLECTION = "reflection"
    HUB = "hub"
    SOURCE = "source"
    PROJECT = "project"


# =============================================================================
# Validation Patterns
# =============================================================================

# Filename patterns
NOTE_FILENAME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}--[\w-]+\.md$')
HUB_FILENAME_PATTERN = re.compile(r'^[^0-9].*\.md$')  # Must NOT start with digit
SOURCE_FILENAME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}--.*\.md$')

# Link patterns
INTERNAL_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NoteFrontmatter:
    """Frontmatter structure for notes (from 13-formal-data-model.md)."""
    type: str  # note | reflection
    created_at: str  # ISO-8601 datetime
    status: str = "raw"
    processed_at: Optional[str] = None
    captured_from: str = "unknown"
    capture_mode: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    hubs: List[str] = field(default_factory=list)
    emotional_context: Optional[str] = None
    certainty: Optional[str] = None


@dataclass
class HubFrontmatter:
    """Frontmatter structure for hubs (from 13-formal-data-model.md)."""
    type: str = "hub"
    status: str = "empty"
    created_at: str = ""
    last_updated: str = ""
    note_count: Optional[int] = None


@dataclass
class SourceFrontmatter:
    """
    Frontmatter structure for sources.
    Based on specs/13-formal-data-model.md and specs/24-webpage-archival.md.

    Full content preservation is required - URLs are references, content is meaning.
    """
    type: str = "source"
    source_type: str = "article"  # article | blog | wikipedia | academic | documentation | social_media | pdf | book | video
    url: Optional[str] = None
    captured_at: str = ""
    title: Optional[str] = None  # Page title (from 24-webpage-archival.md)
    domain: Optional[str] = None  # Domain extracted from URL (from 24-webpage-archival.md)
    author: Optional[str] = None
    published_at: Optional[str] = None  # Publication date if available (from 24-webpage-archival.md)
    word_count: Optional[int] = None  # For quality validation (from 24-webpage-archival.md)
    archive_method: Optional[str] = None  # auto | manual | hybrid (from 24-webpage-archival.md)
    extraction_confidence: Optional[str] = None  # high | medium | low (from 24-webpage-archival.md)
    tags: List[str] = field(default_factory=list)
    wikipedia_revision: Optional[str] = None  # For Wikipedia pages (from 24-webpage-archival.md)


@dataclass
class ProjectFrontmatter:
    """Frontmatter structure for projects (from 13-formal-data-model.md)."""
    type: str = "project"
    status: str = "active"
    created_at: str = ""
    completed_at: Optional[str] = None
    related_hubs: List[str] = field(default_factory=list)


# =============================================================================
# Validation Functions
# =============================================================================

def validate_note_status(status: str) -> bool:
    """Check if status is valid for notes."""
    try:
        NoteStatus(status)
        return True
    except ValueError:
        return False


def validate_hub_status(status: str) -> bool:
    """Check if status is valid for hubs."""
    try:
        HubStatus(status)
        return True
    except ValueError:
        return False


def validate_certainty(certainty: str) -> bool:
    """Check if certainty level is valid."""
    try:
        CertaintyLevel(certainty)
        return True
    except ValueError:
        return False


def validate_capture_surface(surface: str) -> bool:
    """Check if capture surface is valid."""
    try:
        CaptureSurface(surface)
        return True
    except ValueError:
        return False


def validate_note_filename(filename: str) -> bool:
    """Validate note filename follows YYYY-MM-DD--slug.md pattern."""
    return bool(NOTE_FILENAME_PATTERN.match(filename))


def validate_hub_filename(filename: str) -> bool:
    """Validate hub filename (must NOT have date prefix)."""
    return bool(HUB_FILENAME_PATTERN.match(filename)) and not NOTE_FILENAME_PATTERN.match(filename)


def extract_links(content: str) -> List[str]:
    """Extract all internal [[links]] from content."""
    return INTERNAL_LINK_PATTERN.findall(content)


def infer_entity_type_from_folder(folder: str) -> Optional[EntityType]:
    """Infer entity type from folder name."""
    folder_map = {
        'notes': EntityType.NOTE,
        'reflections': EntityType.REFLECTION,
        'hubs': EntityType.HUB,
        'sources': EntityType.SOURCE,
        'projects': EntityType.PROJECT,
    }
    return folder_map.get(folder.lower())


def infer_created_at_from_filename(filename: str) -> Optional[str]:
    """Attempt to infer created_at from filename date."""
    match = re.match(r'^(\d{4}-\d{2}-\d{2})--', filename)
    if match:
        date_str = match.group(1)
        return f"{date_str}T00:00:00Z"
    return None


# =============================================================================
# Constants for Required Sections
# =============================================================================

# Required sections for notes (from 13-formal-data-model.md)
NOTE_REQUIRED_SECTIONS = [
    "Raw Capture"
]

# Required sections for hubs (from 13-formal-data-model.md)
HUB_REQUIRED_SECTIONS = [
    "What This Hub Is",
    "What This Hub Is Not",
    "Open Questions",
    "Linked Notes"
]


# =============================================================================
# Dormancy Thresholds (from 20-processing-pipeline.md)
# =============================================================================

DORMANCY_THRESHOLD_DAYS = 365  # 12+ months without reference
HUB_SPLIT_THRESHOLD = 50  # Consider split at 50+ backlinks
HUB_LARGE_THRESHOLD = 100  # Flag as large at 100+ backlinks
HUB_MERGE_SIMILARITY_THRESHOLD = 0.8  # 80%+ overlap suggests merge


# =============================================================================
# Hub Promotion Criteria (from hub-promotion-criteria.md)
# =============================================================================

HUB_PROMOTION_MIN_CRITERIA = 2  # "Multiple" = at least 2 criteria
HUB_PROMOTION_TAG_THRESHOLD = 5  # Tag appears in 5+ notes
HUB_PROMOTION_DISCUSSION_THRESHOLD = 3  # Concept discussed in 3+ notes
HUB_PROMOTION_MONTH_SPAN = 3  # Appears across 3+ months


# =============================================================================
# Web Archival Constants (from 24-webpage-archival.md)
# =============================================================================

# Quality thresholds
SOURCE_MIN_WORD_COUNT = 100  # Minimum word count sanity check
SOURCE_FETCH_TIMEOUT = 30  # Max seconds to wait for page fetch
SOURCE_MAX_RETRIES = 3  # Retry count for network failures
SOURCE_RETRY_DELAYS = [2, 4, 8]  # Exponential backoff delays (seconds)

# Filename constraints
SOURCE_SLUG_MAX_LENGTH = 60  # Maximum characters for source slug

# Validation patterns
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


# =============================================================================
# Additional Validation Functions (from 24-webpage-archival.md)
# =============================================================================

def validate_source_type(source_type: str) -> bool:
    """Check if source type is valid."""
    try:
        SourceType(source_type)
        return True
    except ValueError:
        return False


def validate_archive_method(method: str) -> bool:
    """Check if archive method is valid."""
    try:
        ArchiveMethod(method)
        return True
    except ValueError:
        return False


def validate_extraction_confidence(confidence: str) -> bool:
    """Check if extraction confidence level is valid."""
    try:
        ExtractionConfidence(confidence)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Validate URL format."""
    return bool(URL_PATTERN.match(url))


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL."""
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if match:
        return match.group(1)
    return None


def generate_source_slug(title: str, max_length: int = SOURCE_SLUG_MAX_LENGTH) -> str:
    """
    Generate a slug for source filename from title.

    Rules from 24-webpage-archival.md:
    - Lowercase, hyphen-separated
    - No special characters
    - Maximum 60 characters
    """
    # Convert to lowercase
    slug = title.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    return slug or 'untitled'


def infer_source_type_from_url(url: str) -> SourceType:
    """
    Attempt to infer source type from URL.

    From 24-webpage-archival.md.
    """
    url_lower = url.lower()

    if 'wikipedia.org' in url_lower:
        return SourceType.WIKIPEDIA
    elif 'arxiv.org' in url_lower or 'doi.org' in url_lower or 'scholar.google' in url_lower:
        return SourceType.ACADEMIC
    elif 'medium.com' in url_lower or 'substack.com' in url_lower or 'ghost.io' in url_lower:
        return SourceType.BLOG
    elif 'twitter.com' in url_lower or 'x.com' in url_lower or 'reddit.com' in url_lower:
        return SourceType.SOCIAL_MEDIA
    elif 'youtube.com' in url_lower or 'vimeo.com' in url_lower:
        return SourceType.VIDEO
    elif 'docs.' in url_lower or 'documentation' in url_lower or 'readthedocs' in url_lower:
        return SourceType.DOCUMENTATION
    elif url_lower.endswith('.pdf'):
        return SourceType.PDF
    else:
        return SourceType.ARTICLE

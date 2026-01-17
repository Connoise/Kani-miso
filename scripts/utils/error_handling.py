"""
Error Handling for Second Brain.
Based on specs/19-error-handling.md and specs/24-webpage-archival.md

Core principle: Preserve over perfect.
- Keep malformed content rather than deleting
- Flag errors rather than fixing automatically
- Warn rather than block
- Degrade gracefully
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import yaml
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Error Severity Levels (from 19-error-handling.md)
# =============================================================================

class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Blocks operation, data loss risk
    ERROR = "error"        # Requires attention, recoverable
    WARNING = "warning"    # Should fix eventually
    INFO = "info"          # FYI only


class ErrorCategory(Enum):
    """Error categories."""
    PARSE_ERROR = "parse_error"
    MISSING_FIELD = "missing_field"
    INVALID_VALUE = "invalid_value"
    FILENAME_VIOLATION = "filename_violation"
    BROKEN_LINK = "broken_link"
    CIRCULAR_REFERENCE = "circular_reference"  # Not an error, just tracked
    CONFLICT = "conflict"
    STORAGE = "storage"
    DUPLICATE_SLUG = "duplicate_slug"
    ENCODING = "encoding"
    # Web capture categories (from 24-webpage-archival.md)
    FETCH_FAILURE = "fetch_failure"
    EXTRACTION_FAILURE = "extraction_failure"
    LOW_CONFIDENCE = "low_confidence"
    URL_ONLY = "url_only"  # Source has URL but no content


# =============================================================================
# Error Data Classes
# =============================================================================

@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    file_path: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None

    def __str__(self) -> str:
        loc = f":{self.line_number}" if self.line_number else ""
        return f"{self.file_path}{loc}: [{self.severity.value}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'suggestion': self.suggestion,
            'line_number': self.line_number,
        }


@dataclass
class ValidationResult:
    """Result of validating a file or set of files."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info: List[ValidationError]

    @property
    def has_critical(self) -> bool:
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def all_issues(self) -> List[ValidationError]:
        return self.errors + self.warnings + self.info


# =============================================================================
# Validation Functions
# =============================================================================

def validate_frontmatter(content: str, file_path: str) -> List[ValidationError]:
    """
    Validate frontmatter structure and required fields.

    Based on 19-error-handling.md:
    - NEVER delete the file
    - Flag file with parse error
    - Continue processing other files
    """
    errors = []

    # Check for frontmatter delimiters
    if not content.startswith('---'):
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.PARSE_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Missing frontmatter opening delimiter '---'",
            suggestion="Add '---' at the start of the file"
        ))
        return errors

    # Find closing delimiter
    parts = content.split('---', 2)
    if len(parts) < 3:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.PARSE_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Missing frontmatter closing delimiter '---'",
            suggestion="Add closing '---' after frontmatter"
        ))
        return errors

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(parts[1])
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.PARSE_ERROR,
            severity=ErrorSeverity.ERROR,
            message=f"Invalid YAML in frontmatter: {e}",
            suggestion="Fix YAML syntax errors"
        ))
        return errors

    # Check required fields
    if 'type' not in frontmatter:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.MISSING_FIELD,
            severity=ErrorSeverity.ERROR,
            message="Missing required field 'type'",
            suggestion="Add 'type: note' or appropriate type to frontmatter"
        ))

    if 'created_at' not in frontmatter:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.MISSING_FIELD,
            severity=ErrorSeverity.WARNING,
            message="Missing required field 'created_at'",
            suggestion="Add 'created_at: <ISO-8601 date>' to frontmatter"
        ))

    return errors


def validate_note_status(status: str, file_path: str) -> Optional[ValidationError]:
    """Validate note status value against ontology."""
    from models.data_models import validate_note_status as check_status

    if not check_status(status):
        return ValidationError(
            file_path=file_path,
            category=ErrorCategory.INVALID_VALUE,
            severity=ErrorSeverity.WARNING,
            message=f"Non-standard status value '{status}' not in ontology",
            suggestion="Use: raw, processed, evolving, evergreen, dormant, or obsolete"
        )
    return None


def validate_hub_status(status: str, file_path: str) -> Optional[ValidationError]:
    """Validate hub status value against ontology."""
    from models.data_models import validate_hub_status as check_status

    if not check_status(status):
        return ValidationError(
            file_path=file_path,
            category=ErrorCategory.INVALID_VALUE,
            severity=ErrorSeverity.WARNING,
            message=f"Non-standard hub status value '{status}' not in ontology",
            suggestion="Use: empty, active, dormant, or obsolete"
        )
    return None


def validate_filename_convention(file_path: Path, entity_type: str) -> Optional[ValidationError]:
    """
    Validate filename follows convention:
    - Notes/Reflections: YYYY-MM-DD--slug.md
    - Hubs: No date prefix
    """
    from models.data_models import validate_note_filename, validate_hub_filename

    filename = file_path.name

    if entity_type in ('note', 'reflection', 'source'):
        if not validate_note_filename(filename):
            return ValidationError(
                file_path=str(file_path),
                category=ErrorCategory.FILENAME_VIOLATION,
                severity=ErrorSeverity.WARNING,
                message=f"Filename '{filename}' doesn't match YYYY-MM-DD--slug.md pattern",
                suggestion="Rename to follow date--slug.md convention"
            )

    elif entity_type == 'hub':
        if not validate_hub_filename(filename):
            return ValidationError(
                file_path=str(file_path),
                category=ErrorCategory.FILENAME_VIOLATION,
                severity=ErrorSeverity.WARNING,
                message=f"Hub filename '{filename}' should not have date prefix",
                suggestion="Rename to remove date prefix"
            )

    return None


def validate_links(content: str, file_path: str, existing_files: set) -> List[ValidationError]:
    """
    Validate internal links resolve to existing files.

    Note: Broken links are warnings, not errors.
    Note: Circular references are ALLOWED.
    """
    from models.data_models import extract_links

    errors = []
    links = extract_links(content)

    for link in links:
        # Check if link target exists
        possible_paths = [
            f"hubs/{link}.md",
            f"notes/{link}.md",
            f"reflections/{link}.md",
            f"sources/{link}.md",
        ]

        found = any(p in existing_files for p in possible_paths)

        if not found:
            errors.append(ValidationError(
                file_path=file_path,
                category=ErrorCategory.BROKEN_LINK,
                severity=ErrorSeverity.WARNING,
                message=f"Broken link to [[{link}]]",
                suggestion=f"Create the target file or fix the link"
            ))

    return errors


def validate_required_sections(content: str, file_path: str, entity_type: str) -> List[ValidationError]:
    """Validate file has required sections for its type."""
    from models.data_models import NOTE_REQUIRED_SECTIONS, HUB_REQUIRED_SECTIONS

    errors = []

    if entity_type in ('note', 'reflection'):
        for section in NOTE_REQUIRED_SECTIONS:
            if f"## {section}" not in content:
                errors.append(ValidationError(
                    file_path=file_path,
                    category=ErrorCategory.MISSING_FIELD,
                    severity=ErrorSeverity.WARNING,
                    message=f"Missing required section '## {section}'",
                    suggestion=f"Add '## {section}' section"
                ))

    elif entity_type == 'hub':
        for section in HUB_REQUIRED_SECTIONS:
            if f"## {section}" not in content:
                errors.append(ValidationError(
                    file_path=file_path,
                    category=ErrorCategory.MISSING_FIELD,
                    severity=ErrorSeverity.WARNING,
                    message=f"Missing required hub section '## {section}'",
                    suggestion=f"Add '## {section}' section"
                ))

    return errors


# =============================================================================
# Graceful Degradation (from 19-error-handling.md)
# =============================================================================

def try_parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Attempt to parse frontmatter with graceful fallback.

    Full Success -> Parse complete frontmatter
    Partial Success -> Extract what's parseable
    Minimal Success -> Return empty dict, flag for review
    """
    if not content.startswith('---'):
        logger.warning("No frontmatter found, treating as raw capture")
        return {}

    try:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter if frontmatter else {}
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error, extracting best effort: {e}")
        # Try to extract key-value pairs manually
        return _extract_frontmatter_best_effort(content)

    return {}


def _extract_frontmatter_best_effort(content: str) -> Dict[str, Any]:
    """Extract frontmatter fields even from malformed YAML."""
    result = {}

    # Find the frontmatter section
    if not content.startswith('---'):
        return result

    parts = content.split('---', 2)
    if len(parts) < 2:
        return result

    # Try to extract simple key: value pairs
    for line in parts[1].split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if key and value:
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                result[key] = value

    return result


def try_infer_metadata(file_path: Path, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to infer missing metadata from context.

    Based on 19-error-handling.md:
    - type from folder
    - created_at from filename or git history
    - captured_from from folder or git commit message
    """
    from models.data_models import infer_entity_type_from_folder, infer_created_at_from_filename

    result = frontmatter.copy()
    inferred = []

    # Infer type from folder
    if 'type' not in result:
        folder = file_path.parent.name
        entity_type = infer_entity_type_from_folder(folder)
        if entity_type:
            result['type'] = entity_type.value
            inferred.append(f"type={entity_type.value}")

    # Infer created_at from filename
    if 'created_at' not in result:
        created_at = infer_created_at_from_filename(file_path.name)
        if created_at:
            result['created_at'] = created_at
            inferred.append(f"created_at={created_at}")

    if inferred:
        logger.info(f"Inferred metadata for {file_path.name}: {', '.join(inferred)}")

    return result


# =============================================================================
# Error Reporting
# =============================================================================

# =============================================================================
# Source Validation (from 24-webpage-archival.md)
# =============================================================================

def validate_source_content(content: str, file_path: str) -> List[ValidationError]:
    """
    Validate source file has proper content.

    From 24-webpage-archival.md:
    - Full content preservation required
    - URL-only sources are flagged
    - Low word count is a warning
    """
    from models.data_models import SOURCE_MIN_WORD_COUNT

    errors = []

    # Parse frontmatter
    if not content.startswith('---'):
        return errors

    parts = content.split('---', 2)
    if len(parts) < 3:
        return errors

    try:
        fm = yaml.safe_load(parts[1])
        body = parts[2]
    except yaml.YAMLError:
        return errors

    if not fm or fm.get('type') != 'source':
        return errors

    # Check word count
    word_count = fm.get('word_count', 0)
    body_words = len(body.split())

    if word_count == 0 and body_words < SOURCE_MIN_WORD_COUNT:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.URL_ONLY,
            severity=ErrorSeverity.WARNING,
            message=f"Source has only {body_words} words - content may not be fully archived",
            suggestion="Re-archive source or add manual summary"
        ))

    if 0 < word_count < SOURCE_MIN_WORD_COUNT:
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.LOW_CONFIDENCE,
            severity=ErrorSeverity.INFO,
            message=f"Low word count ({word_count}) - verify content is complete",
            suggestion="Review source file for extraction issues"
        ))

    # Check extraction confidence
    if fm.get('extraction_confidence') == 'low':
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.LOW_CONFIDENCE,
            severity=ErrorSeverity.WARNING,
            message="Source was archived with low confidence",
            suggestion="Review and manually verify content quality"
        ))

    # Check required metadata
    if not fm.get('url'):
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.MISSING_FIELD,
            severity=ErrorSeverity.WARNING,
            message="Source missing original URL",
            suggestion="Add url field to frontmatter"
        ))

    if not fm.get('title'):
        errors.append(ValidationError(
            file_path=file_path,
            category=ErrorCategory.MISSING_FIELD,
            severity=ErrorSeverity.INFO,
            message="Source missing title",
            suggestion="Add title field to frontmatter"
        ))

    return errors


def generate_lint_report(errors: List[ValidationError]) -> str:
    """Generate a human-readable lint report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Archive Lint Report")
    lines.append("=" * 60)
    lines.append("")

    # Group by severity
    critical = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
    error_list = [e for e in errors if e.severity == ErrorSeverity.ERROR]
    warnings = [e for e in errors if e.severity == ErrorSeverity.WARNING]
    info = [e for e in errors if e.severity == ErrorSeverity.INFO]

    # Summary
    if critical:
        lines.append(f"CRITICAL: {len(critical)}")
    if error_list:
        lines.append(f"Errors: {len(error_list)}")
    if warnings:
        lines.append(f"Warnings: {len(warnings)}")
    if info:
        lines.append(f"Info: {len(info)}")

    if not errors:
        lines.append("No issues found!")
        return "\n".join(lines)

    lines.append("")

    # Critical issues first
    if critical:
        lines.append("-" * 40)
        lines.append("CRITICAL ISSUES (must fix):")
        for e in critical:
            lines.append(f"  {e}")
            if e.suggestion:
                lines.append(f"    Suggestion: {e.suggestion}")

    # Errors
    if error_list:
        lines.append("-" * 40)
        lines.append("Errors (should fix):")
        for e in error_list:
            lines.append(f"  {e}")
            if e.suggestion:
                lines.append(f"    Suggestion: {e.suggestion}")

    # Warnings
    if warnings:
        lines.append("-" * 40)
        lines.append("Warnings (optional fix):")
        for e in warnings[:20]:  # Limit to first 20
            lines.append(f"  {e}")
        if len(warnings) > 20:
            lines.append(f"  ... and {len(warnings) - 20} more warnings")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)

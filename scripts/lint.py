"""
Archive Linter for Second Brain
Validates archive integrity based on specs/19-error-handling.md and specs/24-webpage-archival.md

Usage:
    python lint.py                  # Run all checks
    python lint.py --hubs           # Check hubs only
    python lint.py --notes          # Check notes only
    python lint.py --sources        # Check sources only
    python lint.py --links          # Check links only
    python lint.py --verbose        # Show all issues including info
"""

import sys
from pathlib import Path
from typing import List, Set, Dict, Any
from collections import defaultdict
import yaml
import argparse

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger
from utils.error_handling import (
    ValidationError,
    ValidationResult,
    ErrorSeverity,
    ErrorCategory,
    validate_frontmatter,
    validate_note_status,
    validate_hub_status,
    validate_filename_convention,
    validate_links,
    validate_required_sections,
    validate_source_content,
    generate_lint_report,
)
from models.data_models import (
    validate_note_filename,
    validate_hub_filename,
    extract_links,
    EntityType,
)

logger = setup_logger(__name__)


class ArchiveLinter:
    """Validates archive integrity."""

    def __init__(self, repo_root: Path = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent
        self.repo_root = repo_root

        # Load config
        config_path = self.repo_root / "config" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        self.folders = self.config.get('folders', {
            'notes': 'notes',
            'reflections': 'reflections',
            'hubs': 'hubs',
            'sources': 'sources',
            'inbox': 'inbox',
        })

    def _get_all_files(self) -> Set[str]:
        """Get set of all markdown files for link validation."""
        all_files = set()
        for folder in self.folders.values():
            folder_path = self.repo_root / folder
            if folder_path.exists():
                for f in folder_path.glob("*.md"):
                    all_files.add(str(f.relative_to(self.repo_root)))
        return all_files

    def lint_file(self, file_path: Path, all_files: Set[str]) -> List[ValidationError]:
        """Lint a single file."""
        errors = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                category=ErrorCategory.ENCODING,
                severity=ErrorSeverity.ERROR,
                message=f"Encoding error: {e}",
                suggestion="Ensure file is valid UTF-8"
            ))
            return errors
        except Exception as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                category=ErrorCategory.STORAGE,
                severity=ErrorSeverity.CRITICAL,
                message=f"Cannot read file: {e}",
            ))
            return errors

        relative_path = str(file_path.relative_to(self.repo_root))

        # Validate frontmatter
        frontmatter_errors = validate_frontmatter(content, relative_path)
        errors.extend(frontmatter_errors)

        # If frontmatter is valid, do more validation
        if not any(e.category == ErrorCategory.PARSE_ERROR for e in frontmatter_errors):
            # Parse frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}

                    entity_type = fm.get('type', '')

                    # Validate status
                    status = fm.get('status', '')
                    if status:
                        if entity_type == 'hub':
                            status_error = validate_hub_status(status, relative_path)
                        else:
                            status_error = validate_note_status(status, relative_path)
                        if status_error:
                            errors.append(status_error)

                    # Validate filename convention
                    filename_error = validate_filename_convention(file_path, entity_type)
                    if filename_error:
                        errors.append(filename_error)

                    # Validate required sections
                    section_errors = validate_required_sections(content, relative_path, entity_type)
                    errors.extend(section_errors)

                    # Validate source content (from 24-webpage-archival.md)
                    if entity_type == 'source':
                        source_errors = validate_source_content(content, relative_path)
                        errors.extend(source_errors)

                except yaml.YAMLError:
                    pass  # Already caught in validate_frontmatter

        # Validate links
        link_errors = validate_links(content, relative_path, all_files)
        errors.extend(link_errors)

        return errors

    def lint_folder(self, folder_name: str, all_files: Set[str]) -> List[ValidationError]:
        """Lint all files in a folder."""
        errors = []
        folder_path = self.repo_root / self.folders.get(folder_name, folder_name)

        if not folder_path.exists():
            return errors

        for file_path in folder_path.glob("*.md"):
            file_errors = self.lint_file(file_path, all_files)
            errors.extend(file_errors)

        return errors

    def lint_all(self) -> ValidationResult:
        """Lint the entire archive."""
        all_errors: List[ValidationError] = []
        all_files = self._get_all_files()

        # Lint each folder
        for folder_name in ['notes', 'reflections', 'hubs', 'sources', 'inbox']:
            if folder_name in self.folders:
                folder_errors = self.lint_folder(folder_name, all_files)
                all_errors.extend(folder_errors)

        # Separate by severity
        critical_and_errors = [e for e in all_errors if e.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR)]
        warnings = [e for e in all_errors if e.severity == ErrorSeverity.WARNING]
        info = [e for e in all_errors if e.severity == ErrorSeverity.INFO]

        valid = len(critical_and_errors) == 0

        return ValidationResult(
            valid=valid,
            errors=critical_and_errors,
            warnings=warnings,
            info=info,
        )

    def lint_hubs(self) -> ValidationResult:
        """Lint only hub files."""
        all_errors: List[ValidationError] = []
        all_files = self._get_all_files()
        folder_errors = self.lint_folder('hubs', all_files)
        all_errors.extend(folder_errors)

        critical_and_errors = [e for e in all_errors if e.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR)]
        warnings = [e for e in all_errors if e.severity == ErrorSeverity.WARNING]
        info = [e for e in all_errors if e.severity == ErrorSeverity.INFO]

        return ValidationResult(
            valid=len(critical_and_errors) == 0,
            errors=critical_and_errors,
            warnings=warnings,
            info=info,
        )

    def lint_notes(self) -> ValidationResult:
        """Lint only note and reflection files."""
        all_errors: List[ValidationError] = []
        all_files = self._get_all_files()

        for folder_name in ['notes', 'reflections']:
            folder_errors = self.lint_folder(folder_name, all_files)
            all_errors.extend(folder_errors)

        critical_and_errors = [e for e in all_errors if e.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR)]
        warnings = [e for e in all_errors if e.severity == ErrorSeverity.WARNING]
        info = [e for e in all_errors if e.severity == ErrorSeverity.INFO]

        return ValidationResult(
            valid=len(critical_and_errors) == 0,
            errors=critical_and_errors,
            warnings=warnings,
            info=info,
        )

    def lint_sources(self) -> ValidationResult:
        """
        Lint only source files.

        From 24-webpage-archival.md:
        - Validate full content preservation
        - Check for URL-only sources
        - Validate metadata
        """
        all_errors: List[ValidationError] = []
        all_files = self._get_all_files()

        folder_errors = self.lint_folder('sources', all_files)
        all_errors.extend(folder_errors)

        critical_and_errors = [e for e in all_errors if e.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR)]
        warnings = [e for e in all_errors if e.severity == ErrorSeverity.WARNING]
        info = [e for e in all_errors if e.severity == ErrorSeverity.INFO]

        return ValidationResult(
            valid=len(critical_and_errors) == 0,
            errors=critical_and_errors,
            warnings=warnings,
            info=info,
        )

    def check_broken_links(self) -> List[ValidationError]:
        """Check all files for broken links."""
        all_errors: List[ValidationError] = []
        all_files = self._get_all_files()

        for folder_name in self.folders:
            folder_path = self.repo_root / self.folders[folder_name]
            if not folder_path.exists():
                continue

            for file_path in folder_path.glob("*.md"):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    relative_path = str(file_path.relative_to(self.repo_root))
                    link_errors = validate_links(content, relative_path, all_files)
                    all_errors.extend(link_errors)
                except Exception:
                    pass

        return all_errors


def main():
    parser = argparse.ArgumentParser(description="Archive Linter")
    parser.add_argument('--hubs', action='store_true', help='Check hubs only')
    parser.add_argument('--notes', action='store_true', help='Check notes only')
    parser.add_argument('--sources', action='store_true', help='Check sources only')
    parser.add_argument('--links', action='store_true', help='Check links only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all issues')
    args = parser.parse_args()

    linter = ArchiveLinter()

    if args.links:
        errors = linter.check_broken_links()
        print("\n" + "=" * 60)
        print("Broken Links Check")
        print("=" * 60)
        if not errors:
            print("\nNo broken links found!")
        else:
            print(f"\nFound {len(errors)} broken links:")
            for e in errors:
                print(f"  {e}")
    elif args.hubs:
        result = linter.lint_hubs()
        all_issues = result.errors + result.warnings
        if args.verbose:
            all_issues += result.info
        print(generate_lint_report(all_issues))
    elif args.notes:
        result = linter.lint_notes()
        all_issues = result.errors + result.warnings
        if args.verbose:
            all_issues += result.info
        print(generate_lint_report(all_issues))
    elif args.sources:
        result = linter.lint_sources()
        all_issues = result.errors + result.warnings
        if args.verbose:
            all_issues += result.info
        print(generate_lint_report(all_issues))
    else:
        result = linter.lint_all()
        all_issues = result.errors + result.warnings
        if args.verbose:
            all_issues += result.info
        print(generate_lint_report(all_issues))

        # Exit with error code if there are critical/error issues
        if not result.valid:
            sys.exit(1)


if __name__ == "__main__":
    main()

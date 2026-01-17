#!/usr/bin/env python3
"""
Second Brain CLI

Unified command-line interface for Second Brain operations.

Based on specs:
- 20-processing-pipeline.md (CLI commands)
- 24-webpage-archival.md (link capture)
- 21-hub-maintenance-operations.md (hub commands)

Usage:
    brain process [--all] [--batch-size N]
    brain capture-link <url> [--summary TEXT]
    brain audit-sources
    brain suggest-hubs
    brain detect-dormant
    brain lint [--hubs] [--notes] [--links]
    brain stats
"""

import sys
import argparse
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def cmd_process(args):
    """Process pending captures."""
    from processor import Processor

    processor = Processor()
    result = processor.process_batch(limit=args.batch_size)

    print(f"\nProcessed: {result['processed']}")
    print(f"Failed: {result['failed']}")
    if result.get('commit_sha'):
        print(f"Commit: {result['commit_sha'][:8]}")


def cmd_capture_link(args):
    """Archive a URL to sources."""
    from processors.web_archiver import WebArchiver

    archiver = WebArchiver()
    print(f"Archiving: {args.url}")

    result = archiver.archive_url(args.url, user_summary=args.summary)

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
        print(f"\nFailed: {result['error']}")
        sys.exit(1)


def cmd_audit_sources(args):
    """Audit sources for quality issues."""
    from processors.web_archiver import WebArchiver

    archiver = WebArchiver()
    print("Auditing sources...")

    result = archiver.audit_sources()

    print(f"\n{'=' * 50}")
    print("Source Audit Report")
    print(f"{'=' * 50}")
    print(f"Total sources: {result['total_sources']}")
    print(f"Needs attention: {result['needs_attention']}")

    if result['url_only']:
        print(f"\nURL-only sources ({len(result['url_only'])}):")
        for item in result['url_only'][:10]:
            print(f"  - {item['file']} ({item['word_count']} words)")
        if len(result['url_only']) > 10:
            print(f"  ... and {len(result['url_only']) - 10} more")

    if result['low_word_count']:
        print(f"\nLow word count ({len(result['low_word_count'])}):")
        for item in result['low_word_count'][:10]:
            print(f"  - {item['file']} ({item['word_count']} words)")

    if result['low_confidence']:
        print(f"\nLow confidence ({len(result['low_confidence'])}):")
        for item in result['low_confidence'][:10]:
            print(f"  - {item['file']}")


def cmd_suggest_hubs(args):
    """Suggest hubs based on note analysis."""
    from hub_analyzer import HubAnalyzer

    analyzer = HubAnalyzer()
    result = analyzer.analyze_and_suggest_hubs(limit_notes=args.limit)

    print(f"\n{'=' * 50}")
    print("Hub Suggestions")
    print(f"{'=' * 50}")

    if result.get('error'):
        print(f"Error: {result['error']}")
        sys.exit(1)

    suggestions = result.get('suggestions', [])
    if not suggestions:
        print("No hub suggestions found.")
        return

    print(f"Analyzed {result.get('notes_analyzed', 0)} notes")
    print(f"Found {len(suggestions)} potential hubs:\n")

    for s in suggestions:
        print(f"  [[{s['name']}]]")
        print(f"   Reason: {s.get('reason', 'N/A')}")
        print(f"   Notes: {s.get('note_count', len(s.get('notes', [])))}")
        print(f"   Confidence: {s.get('confidence', 'unknown')}")
        print()


def cmd_detect_dormant(args):
    """Detect dormant notes and hubs."""
    from hub_analyzer import HubAnalyzer

    analyzer = HubAnalyzer()
    dormant = analyzer.detect_dormant_hubs()

    print(f"\n{'=' * 50}")
    print("Potentially Dormant Hubs")
    print(f"{'=' * 50}")

    if not dormant:
        print("\nNo dormant hubs detected.")
        return

    for d in dormant:
        print(f"\n  [[{d['hub']}]]")
        print(f"   Last linked: {d.get('last_linked', 'Never')}")
        print(f"   Total backlinks: {d['total_backlinks']}")
        print(f"   Reason: {d['reason']}")


def cmd_lint(args):
    """Lint archive for issues."""
    from lint import ArchiveLinter, generate_lint_report

    linter = ArchiveLinter()

    if args.links:
        errors = linter.check_broken_links()
        print(f"\n{'=' * 50}")
        print("Broken Links Check")
        print(f"{'=' * 50}")
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
    else:
        result = linter.lint_all()
        all_issues = result.errors + result.warnings
        if args.verbose:
            all_issues += result.info
        print(generate_lint_report(all_issues))

        if not result.valid:
            sys.exit(1)


def cmd_stats(args):
    """Show queue and archive statistics."""
    from processor import Processor

    processor = Processor()
    processor.show_stats()


def cmd_hub_health(args):
    """Show hub health report."""
    from hub_analyzer import HubAnalyzer

    analyzer = HubAnalyzer()
    report = analyzer.get_hub_health_report()

    print(f"\n{'=' * 50}")
    print("Hub Health Report")
    print(f"{'=' * 50}")
    print(f"\nTotal Hubs: {report['total_hubs']}")

    print("\nBy Status:")
    for status, count in report['by_status'].items():
        print(f"  - {status.capitalize()}: {count}")

    print("\nBy Size:")
    print(f"  - Small (1-10 backlinks): {report['by_size']['small']}")
    print(f"  - Medium (11-50 backlinks): {report['by_size']['medium']}")
    print(f"  - Large (51-100 backlinks): {report['by_size']['large']}")
    print(f"  - Very Large (100+ backlinks): {report['by_size']['very_large']}")

    if report['needs_attention']:
        print("\nNeeds Attention:")
        for item in report['needs_attention']:
            print(f"  - [{item['hub']}] {item['issue']}")

    print(f"\nRecent Activity (30 days):")
    print(f"  - Hubs with new backlinks: {report['recent_activity']['hubs_with_new_backlinks']}")
    print(f"  - New hubs created: {report['recent_activity']['new_hubs_created']}")


def main():
    parser = argparse.ArgumentParser(
        description="Second Brain CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  brain process                    Process all pending captures
  brain capture-link https://...   Archive a webpage
  brain audit-sources              Check source quality
  brain suggest-hubs               Suggest new hubs
  brain lint                       Validate archive
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # process command
    process_parser = subparsers.add_parser('process', help='Process pending captures')
    process_parser.add_argument('--batch-size', '-n', type=int, help='Max captures to process')
    process_parser.add_argument('--all', '-a', action='store_true', help='Process all pending')

    # capture-link command
    link_parser = subparsers.add_parser('capture-link', help='Archive a URL')
    link_parser.add_argument('url', help='URL to archive')
    link_parser.add_argument('--summary', '-s', help='User summary if extraction fails')

    # audit-sources command
    subparsers.add_parser('audit-sources', help='Audit source quality')

    # suggest-hubs command
    hubs_parser = subparsers.add_parser('suggest-hubs', help='Suggest new hubs')
    hubs_parser.add_argument('--limit', '-l', type=int, default=50, help='Max notes to analyze')

    # detect-dormant command
    subparsers.add_parser('detect-dormant', help='Detect dormant hubs')

    # lint command
    lint_parser = subparsers.add_parser('lint', help='Validate archive')
    lint_parser.add_argument('--hubs', action='store_true', help='Check hubs only')
    lint_parser.add_argument('--notes', action='store_true', help='Check notes only')
    lint_parser.add_argument('--links', action='store_true', help='Check links only')
    lint_parser.add_argument('--verbose', '-v', action='store_true', help='Show all issues')

    # stats command
    subparsers.add_parser('stats', help='Show queue statistics')

    # hub-health command
    subparsers.add_parser('hub-health', help='Show hub health report')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Dispatch to command handler
    commands = {
        'process': cmd_process,
        'capture-link': cmd_capture_link,
        'audit-sources': cmd_audit_sources,
        'suggest-hubs': cmd_suggest_hubs,
        'detect-dormant': cmd_detect_dormant,
        'lint': cmd_lint,
        'stats': cmd_stats,
        'hub-health': cmd_hub_health,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

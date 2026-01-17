"""
Hub Analyzer for Second Brain
Analyzes notes and suggests hubs for creation using Claude.

Based on specs:
- 21-hub-maintenance-operations.md
- 13-formal-data-model.md
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
from itertools import combinations
import yaml
from dotenv import load_dotenv
import anthropic

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger
from models.data_models import (
    HubStatus,
    DORMANCY_THRESHOLD_DAYS,
    HUB_SPLIT_THRESHOLD,
    HUB_LARGE_THRESHOLD,
    HUB_MERGE_SIMILARITY_THRESHOLD,
    HUB_PROMOTION_TAG_THRESHOLD,
    HUB_PROMOTION_DISCUSSION_THRESHOLD,
    HUB_PROMOTION_MONTH_SPAN,
    extract_links,
)

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class HubAnalyzer:
    """Analyzes notes and suggests/creates hubs."""

    def __init__(self):
        """Initialize the hub analyzer."""
        self.repo_root = Path(__file__).parent.parent

        # Load config
        config_path = self.repo_root / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = self.config['claude']['model']

        # Note folders to analyze
        self.note_folders = ['notes', 'reflections', 'sources']

        # Load existing hubs
        self.existing_hubs = self._load_existing_hubs()

        logger.info(f"Hub Analyzer initialized with {len(self.existing_hubs)} existing hubs")

    def _load_existing_hubs(self) -> List[str]:
        """Load list of existing hub names."""
        hubs_dir = self.repo_root / "hubs"
        if not hubs_dir.exists():
            return []

        hubs = []
        for file in hubs_dir.glob("*.md"):
            hub_name = file.stem
            hubs.append(hub_name)

        return hubs

    def _load_all_notes(self) -> List[Dict[str, Any]]:
        """Load all notes from note folders."""
        notes = []

        for folder_name in self.note_folders:
            folder = self.repo_root / folder_name
            if not folder.exists():
                continue

            for file in folder.glob("*.md"):
                try:
                    content = file.read_text(encoding='utf-8')
                    notes.append({
                        'path': str(file.relative_to(self.repo_root)),
                        'filename': file.name,
                        'folder': folder_name,
                        'content': content,
                        'title': self._extract_title(content),
                    })
                except Exception as e:
                    logger.warning(f"Failed to read {file}: {e}")

        return notes

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled"

    def _extract_existing_hub_links(self, content: str) -> List[str]:
        """Extract existing [[Hub]] links from content."""
        matches = re.findall(r'\[\[([^\]]+)\]\]', content)
        return matches

    def analyze_and_suggest_hubs(self, limit_notes: int = 50) -> Dict[str, Any]:
        """
        Analyze notes and suggest hubs for creation.

        Args:
            limit_notes: Maximum notes to analyze (for cost control)

        Returns:
            Dictionary with suggestions and analysis
        """
        logger.info("Loading notes for analysis...")
        notes = self._load_all_notes()

        if not notes:
            return {'suggestions': [], 'error': 'No notes found'}

        # Limit notes if needed
        if len(notes) > limit_notes:
            logger.info(f"Limiting to {limit_notes} most recent notes")
            notes = sorted(notes, key=lambda x: x['filename'], reverse=True)[:limit_notes]

        logger.info(f"Analyzing {len(notes)} notes...")

        # Build summary of notes for Claude
        notes_summary = self._build_notes_summary(notes)

        # Ask Claude to analyze and suggest hubs
        suggestions = self._get_hub_suggestions(notes_summary, notes)

        return suggestions

    def _build_notes_summary(self, notes: List[Dict[str, Any]]) -> str:
        """Build a summary of notes for Claude analysis."""
        summaries = []

        for note in notes:
            # Extract key parts of each note
            content = note['content']

            # Get themes section if present
            themes_match = re.search(r'## Themes\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
            themes = themes_match.group(1).strip() if themes_match else ""

            # Get raw capture/reflection section
            raw_match = re.search(r'## Raw (?:Capture|Reflection)\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
            raw = raw_match.group(1).strip()[:500] if raw_match else ""

            # Get existing hub suggestions
            hub_match = re.search(r'## Related Hub Notes.*?\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
            suggested_hubs = hub_match.group(1).strip() if hub_match else ""

            summaries.append(f"""
Note: {note['path']}
Title: {note['title']}
Folder: {note['folder']}
Themes: {themes}
Content snippet: {raw[:300]}...
Existing hub suggestions: {suggested_hubs}
---""")

        return "\n".join(summaries)

    def _get_hub_suggestions(self, notes_summary: str, notes: List[Dict]) -> Dict[str, Any]:
        """Get hub suggestions from Claude."""

        system_prompt = """You are analyzing a personal knowledge archive to suggest hub notes.

Hubs are long-lived conceptual gathering places that:
- Represent recurring themes across multiple notes
- Are named as broad noun phrases (e.g., "Technology and Emotion", "Identity Formation")
- Should NOT be single-use ideas or phrased interpretations
- Should NOT resolve ambiguity or assert conclusions

Your task:
1. Identify concepts that recur across multiple notes
2. Suggest hub names that follow the naming rules
3. Explain WHY each hub should exist
4. List which notes would connect to each hub

Be conservative - only suggest hubs where there's clear recurrence (3+ notes minimum)."""

        user_message = f"""Analyze these notes and suggest hubs for creation.

EXISTING HUBS (do not suggest these):
{', '.join(self.existing_hubs)}

NOTES TO ANALYZE:
{notes_summary}

Respond in this exact format:

SUGGESTED_HUBS:
---
HUB: [Hub Name]
REASON: [Why this hub should exist - what recurring theme does it capture?]
NOTE_COUNT: [Number of notes that would link to this hub]
NOTES: [Comma-separated list of note paths that would link]
CONFIDENCE: [high/medium/low]
---

Only suggest hubs with 3+ related notes. Be conservative."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            response_text = response.content[0].text
            suggestions = self._parse_suggestions(response_text, notes)

            logger.info(f"Claude suggested {len(suggestions)} hubs")
            logger.info(f"Tokens used: {response.usage.input_tokens} in, {response.usage.output_tokens} out")

            return {
                'suggestions': suggestions,
                'notes_analyzed': len(notes),
                'existing_hubs': self.existing_hubs,
            }

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return {'suggestions': [], 'error': str(e)}

    def _parse_suggestions(self, response_text: str, notes: List[Dict]) -> List[Dict]:
        """Parse Claude's suggestion response."""
        suggestions = []

        # Split by --- delimiter
        blocks = response_text.split('---')

        for block in blocks:
            if 'HUB:' not in block:
                continue

            suggestion = {}

            # Extract fields
            hub_match = re.search(r'HUB:\s*(.+)', block)
            if hub_match:
                suggestion['name'] = hub_match.group(1).strip()

            reason_match = re.search(r'REASON:\s*(.+?)(?=\n[A-Z_]+:|$)', block, re.DOTALL)
            if reason_match:
                suggestion['reason'] = reason_match.group(1).strip()

            count_match = re.search(r'NOTE_COUNT:\s*(\d+)', block)
            if count_match:
                suggestion['note_count'] = int(count_match.group(1))

            notes_match = re.search(r'NOTES:\s*(.+?)(?=\n[A-Z_]+:|$)', block, re.DOTALL)
            if notes_match:
                note_paths = [n.strip() for n in notes_match.group(1).split(',')]
                suggestion['notes'] = note_paths

            confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', block)
            if confidence_match:
                suggestion['confidence'] = confidence_match.group(1).strip().lower()

            if suggestion.get('name') and suggestion.get('notes'):
                suggestions.append(suggestion)

        return suggestions

    def create_hub(self, hub_name: str) -> Path:
        """
        Create a hub stub following the spec (13-formal-data-model.md).

        Hub status values: empty, active, dormant, obsolete
        """
        hubs_dir = self.repo_root / "hubs"
        hubs_dir.mkdir(exist_ok=True)

        hub_path = hubs_dir / f"{hub_name}.md"
        now = datetime.now().isoformat()

        content = f"""---
type: hub
status: {HubStatus.EMPTY.value}
created_at: {now}
last_updated: {now}
---

# {hub_name}

## What This Hub Is
A conceptual gathering place for notes that touch on this concept.

This hub does not assert a single definition or viewpoint.

## What This Hub Is Not
- Not a summary
- Not a conclusion
- Not authoritative

## Open Questions
- (leave empty)

## Linked Notes
- (leave empty)
"""

        hub_path.write_text(content, encoding='utf-8')
        logger.info(f"Created hub: {hub_path}")

        # Update existing hubs list
        self.existing_hubs.append(hub_name)

        return hub_path

    def link_notes_to_hub(self, hub_name: str, note_paths: List[str]) -> List[str]:
        """
        Add hub links to specified notes.

        Args:
            hub_name: Name of the hub to link
            note_paths: List of note paths to update

        Returns:
            List of successfully updated note paths
        """
        updated = []

        for note_path in note_paths:
            full_path = self.repo_root / note_path

            if not full_path.exists():
                logger.warning(f"Note not found: {note_path}")
                continue

            try:
                content = full_path.read_text(encoding='utf-8')

                # Check if hub link already exists
                if f"[[{hub_name}]]" in content:
                    logger.info(f"Hub link already exists in: {note_path}")
                    continue

                # Find Related Hub Notes section and add link
                hub_section_pattern = r'(## Related Hub Notes.*?\n)(.*?)(\n##|\Z)'
                match = re.search(hub_section_pattern, content, re.DOTALL)

                if match:
                    # Add link to existing section
                    section_header = match.group(1)
                    existing_links = match.group(2)
                    rest = match.group(3)

                    new_link = f"- [[{hub_name}]]\n"

                    # Check if it's empty placeholder
                    if "(No hub suggestions" in existing_links or existing_links.strip() == "":
                        new_content = content[:match.start()] + section_header + new_link + rest
                    else:
                        new_content = content[:match.start()] + section_header + existing_links.rstrip() + "\n" + new_link + rest
                else:
                    # Add section at end if it doesn't exist
                    new_content = content.rstrip() + f"\n\n## Related Hub Notes\n- [[{hub_name}]]\n"

                full_path.write_text(new_content, encoding='utf-8')
                updated.append(note_path)
                logger.info(f"Added [[{hub_name}]] to: {note_path}")

            except Exception as e:
                logger.error(f"Failed to update {note_path}: {e}")

        return updated

    def interactive_hub_creation(self):
        """Interactive mode for reviewing and creating suggested hubs."""
        print("\n" + "=" * 60)
        print("Hub Analyzer - Interactive Mode")
        print("=" * 60 + "\n")

        # Analyze notes
        print("Analyzing notes with Claude Opus 4.5...")
        result = self.analyze_and_suggest_hubs()

        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
            return

        suggestions = result['suggestions']

        if not suggestions:
            print("\n📭 No hub suggestions - your notes may already be well-organized!")
            return

        print(f"\n📊 Analyzed {result['notes_analyzed']} notes")
        print(f"📁 Existing hubs: {len(result['existing_hubs'])}")
        print(f"💡 Suggested new hubs: {len(suggestions)}")

        created_hubs = []
        linked_notes = []

        for i, suggestion in enumerate(suggestions, 1):
            print("\n" + "-" * 60)
            print(f"\n🏷️  SUGGESTED HUB {i}/{len(suggestions)}: {suggestion['name']}")
            print(f"   Confidence: {suggestion.get('confidence', 'unknown')}")
            print(f"   Would connect: {suggestion.get('note_count', len(suggestion['notes']))} notes")
            print(f"\n   REASON: {suggestion.get('reason', 'No reason provided')}")
            print(f"\n   NOTES:")
            for note in suggestion.get('notes', [])[:10]:  # Show first 10
                print(f"      - {note}")
            if len(suggestion.get('notes', [])) > 10:
                print(f"      ... and {len(suggestion['notes']) - 10} more")

            # Ask for approval
            print("\n   Options:")
            print("   [y] Create hub and link notes")
            print("   [n] Skip this hub")
            print("   [q] Quit")

            choice = input("\n   Your choice: ").strip().lower()

            if choice == 'q':
                print("\n   Exiting...")
                break
            elif choice == 'y':
                # Create hub
                hub_path = self.create_hub(suggestion['name'])
                created_hubs.append(suggestion['name'])
                print(f"   ✅ Created hub: {hub_path}")

                # Link notes
                updated = self.link_notes_to_hub(suggestion['name'], suggestion.get('notes', []))
                linked_notes.extend(updated)
                print(f"   ✅ Linked {len(updated)} notes")
            else:
                print("   ⏭️  Skipped")

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Hubs created: {len(created_hubs)}")
        for hub in created_hubs:
            print(f"  - {hub}")
        print(f"Notes linked: {len(linked_notes)}")
        print("=" * 60 + "\n")

        return {
            'created_hubs': created_hubs,
            'linked_notes': linked_notes,
        }

    # =========================================================================
    # Hub Maintenance Operations (from 21-hub-maintenance-operations.md)
    # =========================================================================

    def detect_missing_backlinks(self, hub_name: str) -> List[str]:
        """
        Find notes that link to hub but aren't in hub's backlink list.

        From 21-hub-maintenance-operations.md.
        """
        hub_path = self.repo_root / "hubs" / f"{hub_name}.md"
        if not hub_path.exists():
            return []

        # Find all notes linking to this hub
        notes_linking_to_hub = []
        for folder in self.note_folders:
            folder_path = self.repo_root / folder
            if not folder_path.exists():
                continue
            for note_file in folder_path.glob("*.md"):
                try:
                    content = note_file.read_text(encoding='utf-8')
                    if f"[[{hub_name}]]" in content:
                        notes_linking_to_hub.append(str(note_file.relative_to(self.repo_root)))
                except Exception:
                    pass

        # Get existing backlinks in hub
        hub_content = hub_path.read_text(encoding='utf-8')
        existing_backlinks = self._extract_backlinks_from_hub(hub_content)

        # Find missing
        missing = [n for n in notes_linking_to_hub if n not in existing_backlinks]
        return missing

    def _extract_backlinks_from_hub(self, content: str) -> Set[str]:
        """Extract note paths from hub's Linked Notes section."""
        backlinks = set()
        in_linked_section = False

        for line in content.split('\n'):
            if line.startswith('## Linked Notes'):
                in_linked_section = True
                continue
            if in_linked_section and line.startswith('## '):
                break
            if in_linked_section:
                # Look for [[note-path]] patterns
                links = extract_links(line)
                for link in links:
                    # Convert to relative path format
                    for folder in self.note_folders:
                        possible = f"{folder}/{link}.md"
                        backlinks.add(possible)
        return backlinks

    def detect_dormant_hubs(self) -> List[Dict[str, Any]]:
        """
        Identify hubs that may be dormant.

        From 21-hub-maintenance-operations.md:
        A hub is dormant if:
        - No new backlinks added in 12+ months
        - No mentions in recent captures
        """
        dormant_candidates = []
        hubs_dir = self.repo_root / "hubs"

        if not hubs_dir.exists():
            return dormant_candidates

        for hub_file in hubs_dir.glob("*.md"):
            hub_name = hub_file.stem
            content = hub_file.read_text(encoding='utf-8')

            # Get all notes linking to this hub
            backlinks = self._get_hub_backlinks(hub_name)

            if not backlinks:
                dormant_candidates.append({
                    'hub': hub_name,
                    'last_linked': None,
                    'total_backlinks': 0,
                    'reason': 'No backlinks'
                })
                continue

            # Find most recent backlink date
            dates = []
            for link in backlinks:
                date = self._extract_date_from_path(link)
                if date:
                    dates.append(date)

            if not dates:
                continue

            most_recent = max(dates)
            days_since = (datetime.now() - most_recent).days

            if days_since > DORMANCY_THRESHOLD_DAYS:
                dormant_candidates.append({
                    'hub': hub_name,
                    'last_linked': most_recent.isoformat(),
                    'total_backlinks': len(backlinks),
                    'days_since_last_link': days_since,
                    'reason': f'Last linked {days_since} days ago'
                })

        return dormant_candidates

    def _get_hub_backlinks(self, hub_name: str) -> List[str]:
        """Get all notes that link to a hub."""
        backlinks = []
        for folder in self.note_folders:
            folder_path = self.repo_root / folder
            if not folder_path.exists():
                continue
            for note_file in folder_path.glob("*.md"):
                try:
                    content = note_file.read_text(encoding='utf-8')
                    if f"[[{hub_name}]]" in content:
                        backlinks.append(str(note_file.relative_to(self.repo_root)))
                except Exception:
                    pass
        return backlinks

    def _extract_date_from_path(self, path: str) -> Optional[datetime]:
        """Extract date from note path like notes/2024-01-15--slug.md."""
        match = re.search(r'(\d{4}-\d{2}-\d{2})', path)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d')
            except ValueError:
                pass
        return None

    def detect_hub_split_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify hubs that may benefit from splitting.

        From 21-hub-maintenance-operations.md:
        - Hub has 50+ backlinks
        - Clear sub-themes emerge
        """
        candidates = []
        hubs_dir = self.repo_root / "hubs"

        if not hubs_dir.exists():
            return candidates

        for hub_file in hubs_dir.glob("*.md"):
            hub_name = hub_file.stem
            backlinks = self._get_hub_backlinks(hub_name)

            if len(backlinks) >= HUB_SPLIT_THRESHOLD:
                candidates.append({
                    'hub': hub_name,
                    'backlink_count': len(backlinks),
                    'recommendation': 'Consider splitting into sub-hubs' if len(backlinks) >= HUB_LARGE_THRESHOLD else 'Monitor for sub-themes'
                })

        return sorted(candidates, key=lambda x: x['backlink_count'], reverse=True)

    def detect_hub_merge_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify hub pairs with high overlap.

        From 21-hub-maintenance-operations.md:
        - Two hubs have 80%+ overlapping backlinks
        - Hubs represent synonym concepts
        """
        hubs_dir = self.repo_root / "hubs"
        if not hubs_dir.exists():
            return []

        # Get backlinks for all hubs
        hub_backlinks = {}
        for hub_file in hubs_dir.glob("*.md"):
            hub_name = hub_file.stem
            hub_backlinks[hub_name] = set(self._get_hub_backlinks(hub_name))

        # Compare all pairs
        merge_candidates = []
        for hub1, hub2 in combinations(hub_backlinks.keys(), 2):
            backlinks1 = hub_backlinks[hub1]
            backlinks2 = hub_backlinks[hub2]

            if not backlinks1 or not backlinks2:
                continue

            overlap = backlinks1.intersection(backlinks2)
            smaller_set_size = min(len(backlinks1), len(backlinks2))

            if smaller_set_size > 0:
                similarity = len(overlap) / smaller_set_size
                if similarity >= HUB_MERGE_SIMILARITY_THRESHOLD:
                    merge_candidates.append({
                        'hub1': hub1,
                        'hub2': hub2,
                        'overlap_ratio': round(similarity, 2),
                        'shared_backlinks': len(overlap),
                        'recommendation': 'Consider merging'
                    })

        return sorted(merge_candidates, key=lambda x: x['overlap_ratio'], reverse=True)

    def get_hub_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive hub health report.

        From 21-hub-maintenance-operations.md.
        """
        hubs_dir = self.repo_root / "hubs"
        if not hubs_dir.exists():
            return {'total_hubs': 0}

        report = {
            'total_hubs': 0,
            'by_status': defaultdict(int),
            'by_size': {
                'small': 0,    # 1-10 backlinks
                'medium': 0,   # 11-50 backlinks
                'large': 0,    # 51-100 backlinks
                'very_large': 0  # 100+ backlinks
            },
            'needs_attention': [],
            'recent_activity': {
                'hubs_with_new_backlinks': 0,
                'new_hubs_created': 0
            }
        }

        thirty_days_ago = datetime.now() - timedelta(days=30)

        for hub_file in hubs_dir.glob("*.md"):
            report['total_hubs'] += 1
            hub_name = hub_file.stem

            try:
                content = hub_file.read_text(encoding='utf-8')

                # Parse status
                status_match = re.search(r'status:\s*(\w+)', content)
                status = status_match.group(1) if status_match else 'unknown'
                report['by_status'][status] += 1

                # Count backlinks
                backlinks = self._get_hub_backlinks(hub_name)
                backlink_count = len(backlinks)

                # Categorize by size
                if backlink_count <= 10:
                    report['by_size']['small'] += 1
                elif backlink_count <= 50:
                    report['by_size']['medium'] += 1
                elif backlink_count <= 100:
                    report['by_size']['large'] += 1
                else:
                    report['by_size']['very_large'] += 1
                    report['needs_attention'].append({
                        'hub': hub_name,
                        'issue': f'{backlink_count} backlinks, consider splitting'
                    })

                # Check for recent activity
                for link in backlinks:
                    date = self._extract_date_from_path(link)
                    if date and date >= thirty_days_ago:
                        report['recent_activity']['hubs_with_new_backlinks'] += 1
                        break

                # Check created_at for new hubs
                created_match = re.search(r'created_at:\s*([^\n]+)', content)
                if created_match:
                    try:
                        created_str = created_match.group(1).strip()
                        # Handle both date and datetime formats
                        if 'T' in created_str:
                            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        else:
                            created = datetime.strptime(created_str, '%Y-%m-%d')
                        if created >= thirty_days_ago:
                            report['recent_activity']['new_hubs_created'] += 1
                    except (ValueError, TypeError):
                        pass

            except Exception as e:
                logger.warning(f"Error analyzing hub {hub_name}: {e}")

        # Add dormant and merge candidates to needs_attention
        dormant = self.detect_dormant_hubs()
        for d in dormant[:5]:  # Top 5
            report['needs_attention'].append({
                'hub': d['hub'],
                'issue': f"Potentially dormant: {d['reason']}"
            })

        merge_candidates = self.detect_hub_merge_candidates()
        for m in merge_candidates[:3]:  # Top 3
            report['needs_attention'].append({
                'hub': f"{m['hub1']} + {m['hub2']}",
                'issue': f"{int(m['overlap_ratio']*100)}% overlap, consider merge"
            })

        return report

    def update_hub_backlinks(self, hub_name: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Update hub's backlinks section with missing notes.

        From 21-hub-maintenance-operations.md:
        Requires confirmation (dry_run=True by default).
        """
        missing = self.detect_missing_backlinks(hub_name)

        if not missing:
            return {'hub': hub_name, 'missing': 0, 'updated': False}

        if dry_run:
            return {
                'hub': hub_name,
                'missing': len(missing),
                'notes_to_add': missing,
                'updated': False,
                'message': 'Dry run - no changes made. Set dry_run=False to update.'
            }

        # Actually update the hub
        hub_path = self.repo_root / "hubs" / f"{hub_name}.md"
        content = hub_path.read_text(encoding='utf-8')

        # Find Linked Notes section and add missing backlinks
        for note_path in missing:
            # Extract just the filename for the link
            note_name = Path(note_path).stem
            link_line = f"- [[{note_name}]]\n"

            # Add to Linked Notes section
            if "## Linked Notes" in content:
                # Find the section
                parts = content.split("## Linked Notes")
                if len(parts) == 2:
                    header = parts[0] + "## Linked Notes\n"
                    # Find where section content ends (next ## or end)
                    rest = parts[1]
                    next_section = rest.find('\n## ')
                    if next_section != -1:
                        section_content = rest[:next_section]
                        after_section = rest[next_section:]
                    else:
                        section_content = rest
                        after_section = ""

                    # Add the new link if not already present
                    if f"[[{note_name}]]" not in section_content:
                        section_content = section_content.rstrip() + "\n" + link_line
                        content = header + section_content + after_section

        # Update last_updated timestamp
        now = datetime.now().isoformat()
        content = re.sub(r'last_updated:.*', f'last_updated: {now}', content)

        # Update status to active if was empty
        content = re.sub(r'status: empty', 'status: active', content)

        hub_path.write_text(content, encoding='utf-8')
        logger.info(f"Updated hub {hub_name} with {len(missing)} backlinks")

        return {
            'hub': hub_name,
            'missing': len(missing),
            'notes_added': missing,
            'updated': True
        }

    def mark_hub_dormant(self, hub_name: str) -> bool:
        """Mark a hub as dormant."""
        hub_path = self.repo_root / "hubs" / f"{hub_name}.md"
        if not hub_path.exists():
            return False

        content = hub_path.read_text(encoding='utf-8')
        content = re.sub(r'status:\s*\w+', f'status: {HubStatus.DORMANT.value}', content)
        content = re.sub(r'last_updated:.*', f'last_updated: {datetime.now().isoformat()}', content)
        hub_path.write_text(content, encoding='utf-8')
        logger.info(f"Marked hub {hub_name} as dormant")
        return True


def main():
    """Main entry point with CLI commands from 21-hub-maintenance-operations.md."""
    import argparse

    parser = argparse.ArgumentParser(description="Hub Analyzer and Maintenance")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze notes and suggest hubs')
    analyze_parser.add_argument('--limit', '-l', type=int, default=50, help='Max notes to analyze')

    # create command (interactive)
    subparsers.add_parser('create', help='Interactive hub creation')

    # check-backlinks command
    backlinks_parser = subparsers.add_parser('check-backlinks', help='Check hub backlinks')
    backlinks_parser.add_argument('--hub', help='Specific hub to check (optional)')
    backlinks_parser.add_argument('--update', action='store_true', help='Update backlinks (requires confirmation)')

    # detect-dormant command
    subparsers.add_parser('detect-dormant', help='Detect dormant hubs')

    # detect-splits command
    subparsers.add_parser('detect-splits', help='Detect hub split candidates')

    # detect-merges command
    subparsers.add_parser('detect-merges', help='Detect hub merge candidates')

    # health command
    subparsers.add_parser('health', help='Hub health report')

    args = parser.parse_args()

    analyzer = HubAnalyzer()

    if args.command == 'analyze':
        result = analyzer.analyze_and_suggest_hubs(limit_notes=args.limit)
        print("\n" + "=" * 60)
        print("HUB SUGGESTIONS (Analysis Only)")
        print("=" * 60)
        for s in result.get('suggestions', []):
            print(f"\n  {s['name']}")
            print(f"   Reason: {s.get('reason', 'N/A')}")
            print(f"   Notes: {s.get('note_count', len(s.get('notes', [])))}")
            print(f"   Confidence: {s.get('confidence', 'unknown')}")

    elif args.command == 'create':
        analyzer.interactive_hub_creation()

    elif args.command == 'check-backlinks':
        if args.hub:
            result = analyzer.update_hub_backlinks(args.hub, dry_run=not args.update)
            print(f"\nHub: {result['hub']}")
            print(f"Missing backlinks: {result['missing']}")
            if result.get('notes_to_add'):
                print("Notes to add:")
                for note in result['notes_to_add']:
                    print(f"  - {note}")
            if result.get('updated'):
                print("Backlinks updated.")
            elif result['missing'] > 0:
                print("Run with --update to add these backlinks.")
        else:
            # Check all hubs
            print("\n" + "=" * 60)
            print("Hub Backlink Check")
            print("=" * 60)
            for hub_name in analyzer.existing_hubs:
                missing = analyzer.detect_missing_backlinks(hub_name)
                if missing:
                    print(f"\n  {hub_name}: {len(missing)} missing backlinks")
                    for note in missing[:5]:
                        print(f"      - {note}")
                    if len(missing) > 5:
                        print(f"      ... and {len(missing) - 5} more")

    elif args.command == 'detect-dormant':
        dormant = analyzer.detect_dormant_hubs()
        print("\n" + "=" * 60)
        print("Potentially Dormant Hubs")
        print("=" * 60)
        if not dormant:
            print("\nNo dormant hubs detected.")
        else:
            for d in dormant:
                print(f"\n  [[{d['hub']}]]")
                print(f"   Last linked: {d.get('last_linked', 'Never')}")
                print(f"   Total backlinks: {d['total_backlinks']}")
                print(f"   Reason: {d['reason']}")

    elif args.command == 'detect-splits':
        candidates = analyzer.detect_hub_split_candidates()
        print("\n" + "=" * 60)
        print("Hub Split Candidates")
        print("=" * 60)
        if not candidates:
            print("\nNo hubs large enough to consider splitting.")
        else:
            for c in candidates:
                print(f"\n  [[{c['hub']}]]")
                print(f"   Backlinks: {c['backlink_count']}")
                print(f"   Recommendation: {c['recommendation']}")

    elif args.command == 'detect-merges':
        candidates = analyzer.detect_hub_merge_candidates()
        print("\n" + "=" * 60)
        print("Hub Merge Candidates")
        print("=" * 60)
        if not candidates:
            print("\nNo hub pairs with significant overlap detected.")
        else:
            for c in candidates:
                print(f"\n  [[{c['hub1']}]] + [[{c['hub2']}]]")
                print(f"   Overlap: {int(c['overlap_ratio']*100)}%")
                print(f"   Shared backlinks: {c['shared_backlinks']}")

    elif args.command == 'health':
        report = analyzer.get_hub_health_report()
        print("\n" + "=" * 60)
        print("Hub Health Report")
        print("=" * 60)
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

    else:
        # Default: show help
        parser.print_help()


if __name__ == "__main__":
    main()

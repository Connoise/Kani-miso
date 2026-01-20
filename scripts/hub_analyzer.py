"""
Hub Analyzer for Second Brain
Analyzes notes and suggests hubs for creation using Claude.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
import yaml
from dotenv import load_dotenv
import anthropic

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

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

        # Initialize notes root (can be different from repo root)
        notes_root_config = self.config.get('notes_root', '.')
        if notes_root_config == '.' or not notes_root_config:
            self.notes_root = self.repo_root
        else:
            self.notes_root = Path(notes_root_config)

        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = self.config['claude']['model']

        # Note folders to analyze
        self.note_folders = ['notes', 'reflections', 'sources', 'tweets']

        # Load existing hubs
        self.existing_hubs = self._load_existing_hubs()

        logger.info(f"Hub Analyzer initialized with {len(self.existing_hubs)} existing hubs")
        if self.notes_root != self.repo_root:
            logger.info(f"Notes location: {self.notes_root}")

    def _load_existing_hubs(self) -> List[str]:
        """Load list of existing hub names."""
        hubs_dir = self.notes_root / "hubs"
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
            folder = self.notes_root / folder_name
            if not folder.exists():
                continue

            for file in folder.glob("*.md"):
                try:
                    content = file.read_text(encoding='utf-8')
                    notes.append({
                        'path': str(file.relative_to(self.notes_root)),
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
        """Create a hub stub following the spec."""
        hubs_dir = self.notes_root / "hubs"
        hubs_dir.mkdir(exist_ok=True)

        hub_path = hubs_dir / f"{hub_name}.md"

        content = f"""---
type: hub
status: empty
created_at: {datetime.now().strftime('%Y-%m-%d')}
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
            full_path = self.notes_root / note_path

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


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Hub Analyzer")
    parser.add_argument('--analyze', '-a', action='store_true', help='Analyze only, no creation')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Max notes to analyze')
    args = parser.parse_args()

    analyzer = HubAnalyzer()

    if args.analyze:
        result = analyzer.analyze_and_suggest_hubs(limit_notes=args.limit)
        print("\n" + "=" * 60)
        print("HUB SUGGESTIONS (Analysis Only)")
        print("=" * 60)
        for s in result.get('suggestions', []):
            print(f"\n🏷️  {s['name']}")
            print(f"   Reason: {s.get('reason', 'N/A')}")
            print(f"   Notes: {s.get('note_count', len(s.get('notes', [])))}")
            print(f"   Confidence: {s.get('confidence', 'unknown')}")
    else:
        analyzer.interactive_hub_creation()


if __name__ == "__main__":
    main()

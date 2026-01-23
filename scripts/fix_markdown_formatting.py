"""
Fix markdown files that are incorrectly wrapped in code blocks.

Many files start with ```markdown and end with ```, which prevents
Obsidian from parsing the YAML frontmatter and recognizing tags.

This script removes those wrappers while preserving the content.
"""

import os
import re
from pathlib import Path


def fix_file(filepath: Path) -> bool:
    """
    Fix a single file by removing markdown code block wrappers.

    Returns True if the file was modified, False otherwise.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    # Check if file starts with ```markdown
    if not content.startswith('```markdown'):
        return False

    # Find the opening marker and remove it
    lines = content.split('\n')

    # Remove the first line (```markdown)
    if lines[0].strip() == '```markdown':
        lines = lines[1:]
    else:
        return False

    # Find and remove the closing ``` marker
    # It might not be at the very end if there's trailing content
    new_lines = []
    found_closing = False
    trailing_content = []

    for i, line in enumerate(lines):
        if line.strip() == '```' and not found_closing:
            found_closing = True
            # Check if there's content after this line
            trailing_content = lines[i+1:]
            break
        new_lines.append(line)

    if not found_closing:
        return False

    # Combine the content (inner content + any trailing content)
    final_content = '\n'.join(new_lines)

    # Add trailing content if it exists and is meaningful
    if trailing_content:
        trailing_text = '\n'.join(trailing_content).strip()
        if trailing_text:
            final_content = final_content + '\n' + trailing_text

    try:
        filepath.write_text(final_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}")
        return False


def main():
    obsidian_path = Path(r"C:\Users\gilli\Desktop\Connor Work\Obsidian Notes")

    if not obsidian_path.exists():
        print(f"Path does not exist: {obsidian_path}")
        return

    # Find all markdown files
    md_files = list(obsidian_path.rglob("*.md"))

    fixed_count = 0
    error_count = 0
    skipped_count = 0

    for filepath in md_files:
        result = fix_file(filepath)
        if result:
            fixed_count += 1
            print(f"Fixed: {filepath.name}")
        else:
            # Check if it needs fixing but failed
            try:
                content = filepath.read_text(encoding='utf-8')
                if content.startswith('```markdown'):
                    error_count += 1
                    print(f"Error (still has wrapper): {filepath.name}")
                else:
                    skipped_count += 1
            except:
                error_count += 1

    print(f"\n--- Summary ---")
    print(f"Total files scanned: {len(md_files)}")
    print(f"Files fixed: {fixed_count}")
    print(f"Files already correct: {skipped_count}")
    print(f"Errors: {error_count}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Diagnostic script to check vault configuration and tweet files.
"""

import sys
import yaml
import sqlite3
from pathlib import Path

# Add viewer module to path
sys.path.insert(0, str(Path(__file__).parent))

from viewer.indexer import get_index_path

def main():
    # Load config
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'

    if not config_path.exists():
        print(f"❌ Config file not found at: {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Get vault path
    vault_path_str = config.get('notes_root', '.')
    vault_path = Path(vault_path_str).expanduser()

    print(f"📁 Vault path from config: {vault_path}")
    print(f"   Exists: {vault_path.exists()}")
    print()

    if not vault_path.exists():
        print(f"❌ Vault path does not exist!")
        sys.exit(1)

    # Check for tweets folder
    tweets_folder_name = config.get('folders', {}).get('tweets', 'tweets')
    tweets_folder = vault_path / tweets_folder_name

    print(f"🐦 Tweets folder: {tweets_folder}")
    print(f"   Exists: {tweets_folder.exists()}")

    if tweets_folder.exists():
        tweet_files = list(tweets_folder.glob('*.md'))
        print(f"   Files found: {len(tweet_files)}")

        if tweet_files:
            print("\n   Sample files:")
            for f in tweet_files[:5]:
                print(f"     - {f.name}")

                # Check frontmatter
                content = f.read_text(encoding='utf-8')
                if content.startswith('---'):
                    lines = content.split('\n')
                    frontmatter_end = None
                    for i, line in enumerate(lines[1:], 1):
                        if line.strip() == '---':
                            frontmatter_end = i
                            break

                    if frontmatter_end:
                        frontmatter_text = '\n'.join(lines[1:frontmatter_end])
                        if 'type:' in frontmatter_text:
                            # Extract type value
                            for line in frontmatter_text.split('\n'):
                                if line.strip().startswith('type:'):
                                    type_value = line.split(':', 1)[1].strip()
                                    print(f"       Type: {type_value}")
                                    break
                        else:
                            print(f"       ⚠️  No 'type' field in frontmatter")
                    else:
                        print(f"       ⚠️  Malformed frontmatter (no closing ---)")
                else:
                    print(f"       ⚠️  No frontmatter found")
    else:
        print(f"   ⚠️  Tweets folder does not exist at {tweets_folder}")

    print()

    # Check all markdown files for tweet type
    print("🔍 Searching for all notes with type: tweet...")
    all_md_files = list(vault_path.rglob('*.md'))
    print(f"   Total markdown files in vault: {len(all_md_files)}")

    tweet_type_count = 0
    for md_file in all_md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            if content.startswith('---'):
                lines = content.split('\n')
                frontmatter_end = None
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == '---':
                        frontmatter_end = i
                        break

                if frontmatter_end:
                    frontmatter_text = '\n'.join(lines[1:frontmatter_end])
                    for line in frontmatter_text.split('\n'):
                        if line.strip().startswith('type:'):
                            type_value = line.split(':', 1)[1].strip().strip('"\'')
                            if type_value.lower() == 'tweet':
                                tweet_type_count += 1
                                print(f"   ✓ Found: {md_file.relative_to(vault_path)}")
                            break
        except Exception as e:
            pass

    print(f"\n   Total files with type: tweet = {tweet_type_count}")

    if tweet_type_count == 0:
        print("\n⚠️  No tweet files found with frontmatter!")
        print("   However, as of the latest update, tweets can be detected by folder location.")
        print("   Files in the tweets/ folder will automatically be tagged as type: tweet")

    # Check the database index
    print("\n" + "="*70)
    print("📊 CHECKING VIEWER INDEX DATABASE")
    print("="*70)

    index_path = get_index_path(vault_path)
    print(f"Index location: {index_path}")

    if not index_path.exists():
        print("⚠️  Index database does not exist!")
        print("   Run: python scripts\\rebuild_index.py")
    else:
        print(f"✓ Index exists (size: {index_path.stat().st_size / 1024:.1f} KB)")

        try:
            db = sqlite3.connect(str(index_path))
            db.row_factory = sqlite3.Row

            # Check tweet count in database
            cursor = db.execute("SELECT COUNT(*) as count FROM notes WHERE type = 'tweet'")
            db_tweet_count = cursor.fetchone()[0]

            cursor = db.execute("SELECT COUNT(*) as count FROM notes")
            total_count = cursor.fetchone()[0]

            print(f"\n📈 Database Statistics:")
            print(f"   Total indexed notes: {total_count}")
            print(f"   Tweets in database: {db_tweet_count}")

            if db_tweet_count > 0:
                print(f"\n   Sample tweets from database:")
                cursor = db.execute("""
                    SELECT path, title
                    FROM notes
                    WHERE type = 'tweet'
                    LIMIT 5
                """)
                for row in cursor:
                    print(f"     - {row['title']}")
            else:
                print(f"\n   ⚠️  No tweets indexed in database!")
                print(f"   This means the index needs to be rebuilt with the latest code.")
                print(f"   Run: python scripts\\rebuild_index.py")

            db.close()

        except Exception as e:
            print(f"   ❌ Error reading database: {e}")

if __name__ == '__main__':
    main()

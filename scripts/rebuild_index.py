#!/usr/bin/env python3
"""
Script to manually rebuild the viewer index with verbose output.
"""

import sys
import yaml
import sqlite3
from pathlib import Path

# Add viewer module to path
sys.path.insert(0, str(Path(__file__).parent))

from viewer.indexer import get_index_path, init_index


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

    if not vault_path.exists():
        print(f"❌ Vault path does not exist: {vault_path}")
        sys.exit(1)

    print(f"📁 Vault path: {vault_path}")

    # Get index path
    index_path = get_index_path(vault_path)
    print(f"💾 Index path: {index_path}")

    # Delete old index if it exists
    if index_path.exists():
        print(f"🗑️  Deleting old index...")
        index_path.unlink()

    # Rebuild index
    print(f"🔨 Rebuilding index...")
    db = init_index(vault_path)

    # Check how many tweets were indexed
    cursor = db.execute("SELECT COUNT(*) FROM notes WHERE type = 'tweet'")
    tweet_count = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM notes WHERE type = 'note'")
    note_count = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM notes WHERE type = 'reflection'")
    reflection_count = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM notes WHERE type = 'source'")
    source_count = cursor.fetchone()[0]

    cursor = db.execute("SELECT COUNT(*) FROM notes")
    total_count = cursor.fetchone()[0]

    print(f"\n✅ Index rebuilt successfully!")
    print(f"   Total notes: {total_count}")
    print(f"   Notes: {note_count}")
    print(f"   Reflections: {reflection_count}")
    print(f"   Sources: {source_count}")
    print(f"   Tweets: {tweet_count}")

    if tweet_count > 0:
        print(f"\n🐦 Sample tweets:")
        cursor = db.execute("""
            SELECT path, title, created_at
            FROM notes
            WHERE type = 'tweet'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        for row in cursor:
            print(f"   - {row[1]} ({row[0]})")
    else:
        print(f"\n⚠️  No tweets found!")
        print(f"   Checking for files in tweets/ folder...")
        tweets_folder = vault_path / 'tweets'
        if tweets_folder.exists():
            tweet_files = list(tweets_folder.glob('*.md'))
            print(f"   Found {len(tweet_files)} .md files in tweets/ folder")
            if tweet_files:
                print(f"   Sample file: {tweet_files[0].name}")
                print(f"   Relative path: {tweet_files[0].relative_to(vault_path)}")
                print(f"   Parts: {tweet_files[0].relative_to(vault_path).parts}")

    db.close()


if __name__ == '__main__':
    main()

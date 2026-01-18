"""
Tweet Tracker for Second Brain
Tracks which tweets have been forwarded to Telegram to avoid duplicates.
Uses a separate SQLite database.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import sys
sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TweetTracker:
    """Tracks forwarded tweets using SQLite."""

    def __init__(self, db_path: str = "queue/tweet_tracker.db"):
        """
        Initialize tweet tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def _initialize_db(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS forwarded_tweets (
                    tweet_id TEXT PRIMARY KEY,
                    tweet_created_at TEXT,
                    tweet_text TEXT,
                    forwarded_at TEXT NOT NULL,
                    telegram_message_id INTEGER,
                    has_media INTEGER DEFAULT 0,
                    media_count INTEGER DEFAULT 0
                )
            """)

            # Track the last processed tweet ID for efficient fetching
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
            logger.info(f"Tweet tracker database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def is_forwarded(self, tweet_id: str) -> bool:
        """
        Check if a tweet has already been forwarded.

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            True if already forwarded
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM forwarded_tweets WHERE tweet_id = ?",
                (tweet_id,)
            )
            return cursor.fetchone() is not None

    def mark_forwarded(
        self,
        tweet_id: str,
        tweet_created_at: Optional[str] = None,
        tweet_text: Optional[str] = None,
        telegram_message_id: Optional[int] = None,
        has_media: bool = False,
        media_count: int = 0,
    ):
        """
        Mark a tweet as forwarded.

        Args:
            tweet_id: Twitter tweet ID
            tweet_created_at: When the tweet was posted
            tweet_text: Tweet text content
            telegram_message_id: Telegram message ID (if available)
            has_media: Whether the tweet has media attachments
            media_count: Number of media attachments
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO forwarded_tweets (
                    tweet_id, tweet_created_at, tweet_text,
                    forwarded_at, telegram_message_id,
                    has_media, media_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tweet_id,
                    tweet_created_at,
                    tweet_text[:500] if tweet_text else None,  # Truncate for storage
                    datetime.now().isoformat(),
                    telegram_message_id,
                    1 if has_media else 0,
                    media_count,
                )
            )
            conn.commit()
        logger.info(f"Marked tweet {tweet_id} as forwarded")

    def get_last_tweet_id(self) -> Optional[str]:
        """
        Get the ID of the last processed tweet.

        Returns:
            Last tweet ID or None if no tweets processed yet
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM sync_state WHERE key = 'last_tweet_id'"
            )
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_last_tweet_id(self, tweet_id: str):
        """
        Update the last processed tweet ID.

        Args:
            tweet_id: Most recent tweet ID processed
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sync_state (key, value, updated_at)
                VALUES ('last_tweet_id', ?, ?)
                """,
                (tweet_id, datetime.now().isoformat())
            )
            conn.commit()
        logger.debug(f"Updated last tweet ID to {tweet_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get forwarding statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as total FROM forwarded_tweets")
            total = cursor.fetchone()["total"]

            cursor = conn.execute(
                "SELECT COUNT(*) as with_media FROM forwarded_tweets WHERE has_media = 1"
            )
            with_media = cursor.fetchone()["with_media"]

            cursor = conn.execute(
                "SELECT value FROM sync_state WHERE key = 'last_tweet_id'"
            )
            row = cursor.fetchone()
            last_id = row["value"] if row else None

        return {
            "total_forwarded": total,
            "with_media": with_media,
            "last_tweet_id": last_id,
        }

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently forwarded tweets.

        Args:
            limit: Maximum number to return

        Returns:
            List of forwarded tweet records
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM forwarded_tweets
                ORDER BY forwarded_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]


def main():
    """Test the tweet tracker."""
    tracker = TweetTracker()

    print("Tweet Tracker Stats:")
    stats = tracker.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nRecent forwards:")
    for tweet in tracker.get_recent(5):
        print(f"  {tweet['tweet_id']}: {tweet['tweet_text'][:50] if tweet['tweet_text'] else 'N/A'}...")


if __name__ == "__main__":
    main()

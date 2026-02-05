"""
Queue Manager for Second Brain
Handles durable storage of unprocessed captures using SQLite.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

from utils.logger import setup_logger

logger = setup_logger(__name__)


class QueueManager:
    """Manages the capture queue using SQLite."""

    def __init__(self, db_path: str = "queue/captures.db"):
        """
        Initialize queue manager.

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
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_message_id INTEGER UNIQUE,
                    captured_at TEXT NOT NULL,
                    type TEXT DEFAULT 'Thought',
                    surface TEXT DEFAULT 'unknown',
                    mood TEXT,
                    energy TEXT,
                    confidence TEXT,
                    trigger TEXT,
                    context TEXT,
                    body TEXT NOT NULL,
                    attachments TEXT,  -- JSON array of attachment info
                    image_paths TEXT,  -- JSON array of image paths for this capture
                    status TEXT DEFAULT 'pending',
                    processed_at TEXT,
                    error_message TEXT,
                    output_file TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table for pending images (waiting for text association)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_message_id INTEGER UNIQUE,
                    chat_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_path TEXT,  -- Local path after download
                    captured_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',  -- pending, associated, orphan
                    associated_capture_id INTEGER,  -- FK to captures.id when associated
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (associated_capture_id) REFERENCES captures(id)
                )
            """)

            # Table for bot state persistence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

            # Run migrations for existing databases
            self._run_migrations(conn)

            logger.info(f"Queue database initialized at {self.db_path}")

    def _run_migrations(self, conn):
        """Run database migrations to add new columns to existing tables."""
        # Check existing columns in captures table
        cursor = conn.execute("PRAGMA table_info(captures)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'image_paths' not in columns:
            logger.info("Migrating database: adding image_paths column to captures table")
            conn.execute("ALTER TABLE captures ADD COLUMN image_paths TEXT")
            conn.commit()

        if 'document_paths' not in columns:
            logger.info("Migrating database: adding document_paths column to captures table")
            conn.execute("ALTER TABLE captures ADD COLUMN document_paths TEXT")
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    def add_capture(
        self,
        body: str,
        captured_at: datetime,
        type: str = "Thought",
        surface: str = "unknown",
        telegram_message_id: Optional[int] = None,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        confidence: Optional[str] = None,
        trigger: Optional[str] = None,
        context: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> int:
        """
        Add a new capture to the queue.

        Args:
            body: Main capture content
            captured_at: When the capture was made
            type: Type of capture (Thought, Reflection, Question, etc.)
            surface: Capture surface (mobile, desktop-work, etc.)
            telegram_message_id: Telegram message ID (if from Telegram)
            mood: Mood/emotional state
            energy: Energy level
            confidence: Confidence level
            trigger: What triggered the capture
            context: Situational context
            attachments: List of attachment metadata

        Returns:
            Database ID of the new capture
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO captures (
                    telegram_message_id, captured_at, type, surface,
                    mood, energy, confidence, trigger, context,
                    body, attachments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    telegram_message_id,
                    captured_at.isoformat(),
                    type,
                    surface,
                    mood,
                    energy,
                    confidence,
                    trigger,
                    context,
                    body,
                    json.dumps(attachments) if attachments else None,
                ),
            )
            conn.commit()
            capture_id = cursor.lastrowid
            logger.info(f"Added capture {capture_id} to queue (type: {type})")
            return capture_id

    def get_pending(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all pending captures with prioritization.

        Priority order:
        1. Telegram messages and images (surface = 'mobile' or 'telegram', or has images)
        2. Other captures
        3. Tweets (type = 'Tweet' or surface = 'twitter-archive')

        Args:
            limit: Maximum number of captures to return

        Returns:
            List of capture dictionaries
        """
        query = """
            SELECT * FROM captures
            WHERE status = 'pending'
            ORDER BY
                CASE
                    -- Priority 1: Telegram messages and images
                    WHEN surface IN ('mobile', 'telegram')
                         OR image_paths IS NOT NULL
                         OR attachments IS NOT NULL THEN 1
                    -- Priority 3: Tweets (processed last)
                    WHEN type = 'Tweet' OR surface = 'twitter-archive' THEN 3
                    -- Priority 2: Everything else
                    ELSE 2
                END,
                captured_at ASC
        """
        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            cursor = conn.execute(query)
            captures = [dict(row) for row in cursor.fetchall()]

        logger.info(f"Retrieved {len(captures)} pending captures (prioritized: Telegram/images first, tweets last)")
        return captures

    def mark_processing(self, capture_id: int):
        """Mark a capture as being processed."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE captures SET status = 'processing' WHERE id = ?",
                (capture_id,),
            )
            conn.commit()
        logger.debug(f"Marked capture {capture_id} as processing")

    def mark_completed(self, capture_id: int, output_file: str):
        """
        Mark a capture as successfully processed.

        Args:
            capture_id: Database ID of the capture
            output_file: Path to the created markdown file
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE captures SET
                    status = 'done',
                    processed_at = ?,
                    output_file = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), output_file, capture_id),
            )
            conn.commit()
        logger.info(f"Completed capture {capture_id} → {output_file}")

    def mark_failed(self, capture_id: int, error_message: str):
        """
        Mark a capture as failed with error message.

        Args:
            capture_id: Database ID of the capture
            error_message: Description of the error
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE captures SET
                    status = 'failed',
                    error_message = ?,
                    processed_at = ?
                WHERE id = ?
                """,
                (error_message, datetime.now().isoformat(), capture_id),
            )
            conn.commit()
        logger.error(f"Failed capture {capture_id}: {error_message}")

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM captures
                GROUP BY status
            """)
            stats = {row['status']: row['count'] for row in cursor.fetchall()}

        return stats

    def reset_processing(self):
        """Reset any captures stuck in 'processing' status back to 'pending'."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE captures SET status = 'pending'
                WHERE status = 'processing'
            """)
            conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.warning(f"Reset {count} stuck captures from processing to pending")

        return count

    # === Image handling methods ===

    def add_pending_image(
        self,
        chat_id: int,
        file_id: str,
        file_path: str,
        captured_at: datetime,
        telegram_message_id: Optional[int] = None,
    ) -> int:
        """
        Add a pending image waiting for text association.

        Args:
            chat_id: Telegram chat ID
            file_id: Telegram file ID
            file_path: Local path where image is saved
            captured_at: When the image was sent
            telegram_message_id: Telegram message ID

        Returns:
            Database ID of the pending image
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pending_images (
                    telegram_message_id, chat_id, file_id, file_path, captured_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    telegram_message_id,
                    chat_id,
                    file_id,
                    file_path,
                    captured_at.isoformat(),
                ),
            )
            conn.commit()
            image_id = cursor.lastrowid
            logger.info(f"Added pending image {image_id} (file: {file_path})")
            return image_id

    def get_pending_images(self, chat_id: int) -> List[Dict[str, Any]]:
        """
        Get all pending images for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            List of pending image dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM pending_images
                WHERE chat_id = ? AND status = 'pending'
                ORDER BY captured_at ASC
                """,
                (chat_id,),
            )
            images = [dict(row) for row in cursor.fetchall()]

        logger.debug(f"Retrieved {len(images)} pending images for chat {chat_id}")
        return images

    def associate_images_with_capture(
        self,
        image_ids: List[int],
        capture_id: int,
    ) -> int:
        """
        Associate pending images with a text capture.

        Args:
            image_ids: List of pending image IDs
            capture_id: Capture ID to associate with

        Returns:
            Number of images associated
        """
        if not image_ids:
            return 0

        with self._get_connection() as conn:
            placeholders = ','.join('?' * len(image_ids))
            cursor = conn.execute(
                f"""
                UPDATE pending_images
                SET status = 'associated', associated_capture_id = ?
                WHERE id IN ({placeholders}) AND status = 'pending'
                """,
                [capture_id] + image_ids,
            )
            conn.commit()
            count = cursor.rowcount

        logger.info(f"Associated {count} images with capture {capture_id}")
        return count

    def get_images_for_capture(self, capture_id: int) -> List[Dict[str, Any]]:
        """
        Get all images associated with a capture.

        Args:
            capture_id: Capture ID

        Returns:
            List of image dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM pending_images
                WHERE associated_capture_id = ?
                ORDER BY captured_at ASC
                """,
                (capture_id,),
            )
            images = [dict(row) for row in cursor.fetchall()]

        return images

    def get_pending_image_count(self, chat_id: int) -> int:
        """
        Get count of pending images for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Number of pending images
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM pending_images
                WHERE chat_id = ? AND status = 'pending'
                """,
                (chat_id,),
            )
            return cursor.fetchone()[0]

    def update_capture_image_paths(
        self,
        capture_id: int,
        image_paths: List[str],
    ) -> None:
        """
        Update the image_paths field for a capture.

        Args:
            capture_id: Capture ID
            image_paths: List of image file paths
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE captures
                SET image_paths = ?
                WHERE id = ?
                """,
                (json.dumps(image_paths), capture_id),
            )
            conn.commit()
        logger.debug(f"Updated capture {capture_id} with {len(image_paths)} image paths")

    def update_capture_document_paths(
        self,
        capture_id: int,
        document_paths: List[str],
    ) -> None:
        """
        Update the document_paths field for a capture.

        Args:
            capture_id: Capture ID
            document_paths: List of document file paths
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE captures
                SET document_paths = ?
                WHERE id = ?
                """,
                (json.dumps(document_paths), capture_id),
            )
            conn.commit()
        logger.debug(f"Updated capture {capture_id} with {len(document_paths)} document paths")

    # === Bot state persistence methods ===

    def get_last_update_id(self) -> int:
        """
        Get the last processed Telegram update ID.

        Returns:
            Last update ID, or 0 if not set
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM bot_state WHERE key = 'last_update_id'"
            )
            row = cursor.fetchone()
            if row:
                return int(row['value'])
            return 0

    def set_last_update_id(self, update_id: int) -> None:
        """
        Save the last processed Telegram update ID.

        Args:
            update_id: The update ID to save
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO bot_state (key, value, updated_at)
                VALUES ('last_update_id', ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (str(update_id), datetime.now().isoformat()),
            )
            conn.commit()

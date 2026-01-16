"""
Reset failed captures back to pending status for retry.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from queue_manager import QueueManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Reset all failed captures to pending."""
    repo_root = Path(__file__).parent.parent
    queue_db = repo_root / "queue" / "captures.db"

    queue = QueueManager(queue_db)

    # Get stats before
    stats_before = queue.get_stats()
    failed_count = stats_before.get('failed', 0)

    if failed_count == 0:
        logger.info("No failed captures to reset")
        return

    # Reset failed to pending
    with queue._get_connection() as conn:
        cursor = conn.execute("""
            UPDATE captures
            SET status = 'pending', error_message = NULL
            WHERE status = 'failed'
        """)
        conn.commit()
        count = cursor.rowcount

    logger.info(f"Reset {count} failed captures back to pending")

    # Show new stats
    stats_after = queue.get_stats()
    logger.info("\nQueue status:")
    for status, count in stats_after.items():
        logger.info(f"  {status}: {count}")


if __name__ == "__main__":
    main()

"""
Test script to manually add captures to the queue.
Use this until the Telegram bot is configured.
"""

import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from queue_manager import QueueManager
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


def add_test_capture():
    """Add a test capture to the queue interactively."""
    repo_root = Path(__file__).parent.parent
    queue_db = repo_root / "queue" / "captures.db"

    queue = QueueManager(queue_db)

    print("\n" + "=" * 60)
    print("Add Test Capture to Queue")
    print("=" * 60)

    # Get capture details
    print("\nCapture Type [Thought/Reflection/Question/Source]:")
    capture_type = input("> ").strip() or "Thought"

    print("\nCapture body (the main content):")
    body = input("> ").strip()

    if not body:
        print("Error: Body cannot be empty")
        return

    print("\nSurface [mobile/desktop-work/desktop-home]:")
    surface = input("> ").strip() or "mobile"

    print("\nMood (optional):")
    mood = input("> ").strip() or None

    print("\nEnergy (optional):")
    energy = input("> ").strip() or None

    print("\nConfidence (optional):")
    confidence = input("> ").strip() or None

    print("\nTrigger (optional):")
    trigger = input("> ").strip() or None

    print("\nContext (optional):")
    context = input("> ").strip() or None

    # Add to queue
    captured_at = datetime.now()
    capture_id = queue.add_capture(
        body=body,
        captured_at=captured_at,
        type=capture_type,
        surface=surface,
        mood=mood,
        energy=energy,
        confidence=confidence,
        trigger=trigger,
        context=context,
    )

    print(f"\n✓ Added capture {capture_id} to queue")
    print("\nRun 'python scripts/processor.py' to process it")


def quick_add(body: str, type: str = "Thought", mood: str = None):
    """Quickly add a capture without interactive prompts."""
    repo_root = Path(__file__).parent.parent
    queue_db = repo_root / "queue" / "captures.db"

    queue = QueueManager(queue_db)

    capture_id = queue.add_capture(
        body=body,
        captured_at=datetime.now(),
        type=type,
        surface="manual",
        mood=mood,
    )

    print(f"✓ Added capture {capture_id}: {body[:50]}...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Quick add mode: python test_add_capture.py "Some quick thought"
        body = " ".join(sys.argv[1:])
        quick_add(body)
    else:
        # Interactive mode
        add_test_capture()

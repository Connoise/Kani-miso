"""
Combined Runner for Kani-miso
Runs Telegram bot with automatic periodic processing.

Usage:
    python scripts/run.py              # Run bot + auto-process every 5 minutes
    python scripts/run.py --interval 10  # Process every 10 minutes
    python scripts/run.py --manual     # Bot only, process with /process command
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse
import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from queue_manager import QueueManager
from processor import Processor
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class KaniMisoRunner:
    """Combined Telegram bot + processor runner."""

    def __init__(
        self,
        process_interval: int = 300,  # 5 minutes default
        auto_process: bool = True,
    ):
        """
        Initialize runner.

        Args:
            process_interval: Seconds between auto-processing (default 300 = 5 min)
            auto_process: Whether to automatically process or wait for /process command
        """
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in config/.env")

        if self.allowed_chat_id:
            self.allowed_chat_id = int(self.allowed_chat_id)

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.process_interval = process_interval
        self.auto_process = auto_process
        self.running = True
        self.last_process_time = time.time()

        # Initialize components
        repo_root = Path(__file__).parent.parent
        queue_db = repo_root / "queue" / "captures.db"
        self.queue = QueueManager(queue_db)

        # Load persisted last_update_id from database
        self.last_update_id = self.queue.get_last_update_id()
        if self.last_update_id > 0:
            logger.info(f"Resuming from last update ID: {self.last_update_id}")

        logger.info("Kani-miso Runner initialized")
        if self.allowed_chat_id:
            logger.info(f"Listening to chat ID: {self.allowed_chat_id}")
        if self.auto_process:
            logger.info(f"Auto-processing every {process_interval} seconds")
        else:
            logger.info("Manual processing mode (use /process command)")

    def send_message(self, chat_id: int, text: str):
        """Send a Telegram message."""
        url = f"{self.base_url}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    def get_updates(self, timeout: int = 3):
        """Get Telegram updates."""
        url = f"{self.base_url}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": timeout}
        try:
            response = requests.get(url, params=params, timeout=timeout + 2)
            return response.json()
        except KeyboardInterrupt:
            raise
        except:
            return None

    def parse_message(self, text: str) -> dict:
        """Parse message into capture fields."""
        lines = text.strip().split('\n')
        first_line = lines[0] if lines else ""
        capture_type = "Thought"

        type_patterns = {
            'thought:': 'Thought', 'reflection:': 'Reflection',
            'question:': 'Question', 'source:': 'Source',
            'quote:': 'Quote', 'idea:': 'Idea', 'log:': 'Log',
        }

        first_line_lower = first_line.lower()
        for pattern, type_name in type_patterns.items():
            if first_line_lower.startswith(pattern):
                capture_type = type_name
                first_line = first_line[len(pattern):].strip()
                lines[0] = first_line
                break

        context_fields = {
            'surface': None, 'mood': None, 'energy': None,
            'confidence': None, 'trigger': None, 'context': None,
        }
        body_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            matched = False
            line_lower = line.lower()
            for field in context_fields.keys():
                if line_lower.startswith(f"{field}:"):
                    context_fields[field] = line[len(field)+1:].strip()
                    matched = True
                    break
            if not matched:
                body_lines.append(line)

        return {'type': capture_type, 'body': '\n'.join(body_lines), **context_fields}

    def run_processor(self, chat_id: Optional[int] = None) -> dict:
        """Run the processor and optionally notify via Telegram."""
        try:
            logger.info("Starting processing...")
            if chat_id:
                self.send_message(chat_id, "⏳ Processing captures...")

            processor = Processor()
            result = processor.process_batch()

            if chat_id:
                if result['processed'] > 0:
                    msg = f"✅ Processed {result['processed']} captures\n"
                    if result.get('commit_sha'):
                        msg += f"Commit: `{result['commit_sha'][:8]}`"
                    self.send_message(chat_id, msg)
                elif result['failed'] > 0:
                    self.send_message(chat_id, f"❌ {result['failed']} captures failed")
                else:
                    self.send_message(chat_id, "📭 No pending captures")

            return result

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            if chat_id:
                self.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
            return {'processed': 0, 'failed': 0}

    def handle_command(self, chat_id: int, command: str):
        """Handle bot commands."""
        if command == '/start':
            self.send_message(chat_id, (
                f"🧠 *Kani-miso Bot*\n\n"
                f"Chat ID: `{chat_id}`\n\n"
                f"Commands:\n"
                f"/process - Process queue now\n"
                f"/stats - Queue statistics\n"
                f"/help - Message format"
            ))

        elif command == '/process':
            self.run_processor(chat_id)

        elif command == '/stats':
            stats = self.queue.get_stats()
            text = "*Queue Statistics:*\n\n"
            for status, count in stats.items():
                text += f"{status.capitalize()}: {count}\n"
            self.send_message(chat_id, text)

        elif command == '/help':
            self.send_message(chat_id, (
                "*Message Format:*\n\n"
                "Just type or use prefixes:\n"
                "`thought:` `reflection:` `source:`\n"
                "`question:` `idea:` `quote:` `log:`\n\n"
                "Add context:\n"
                "`mood:` `energy:` `trigger:`"
            ))

    def handle_message(self, update: dict):
        """Handle incoming message."""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')

            if not chat_id or not text:
                return

            if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                return

            if text.startswith('/'):
                self.handle_command(chat_id, text.split()[0])
                return

            parsed = self.parse_message(text)
            capture_id = self.queue.add_capture(
                body=parsed['body'],
                captured_at=datetime.now(),
                type=parsed['type'],
                surface=parsed['surface'] or 'mobile',
                telegram_message_id=message.get('message_id'),
                mood=parsed['mood'],
                energy=parsed['energy'],
                confidence=parsed['confidence'],
                trigger=parsed['trigger'],
                context=parsed['context'],
            )

            confirm = f"✅ #{capture_id}"
            if parsed['type'] != 'Thought':
                confirm += f" ({parsed['type']})"
            self.send_message(chat_id, confirm)

        except Exception as e:
            logger.error(f"Error: {e}")

    def run(self):
        """Main run loop."""
        logger.info("=" * 60)
        logger.info("Kani-miso Running")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop")
        logger.info("")

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            logger.info("\nShutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self.running:
                # Get Telegram updates
                result = self.get_updates()
                if result and result.get('ok'):
                    for update in result.get('result', []):
                        self.last_update_id = update['update_id']
                        self.handle_message(update)
                        # Persist update ID so we don't lose messages on restart
                        self.queue.set_last_update_id(self.last_update_id)

                # Auto-process if enabled
                if self.auto_process:
                    elapsed = time.time() - self.last_process_time
                    if elapsed >= self.process_interval:
                        pending = self.queue.get_stats().get('pending', 0)
                        if pending > 0:
                            logger.info(f"Auto-processing {pending} pending captures...")
                            self.run_processor()
                        self.last_process_time = time.time()

        except KeyboardInterrupt:
            pass

        logger.info("Goodbye!")


def main():
    parser = argparse.ArgumentParser(description="Kani-miso Runner")
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=300,
        help='Auto-process interval in seconds (default: 300 = 5 min)'
    )
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='Disable auto-processing (use /process command instead)'
    )
    args = parser.parse_args()

    runner = KaniMisoRunner(
        process_interval=args.interval,
        auto_process=not args.manual,
    )
    runner.run()


if __name__ == "__main__":
    main()

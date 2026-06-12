"""
Combined Runner for Kani-miso
Runs the full Telegram bot (text, images, documents, commands) with periodic
queue processing.

The bot behavior lives entirely in TelegramBot (telegram_bot.py) — this runner
only adds the processing schedule and Telegram progress notifications. It must
not reimplement parsing or message handling (that duplication previously meant
run.py silently dropped photo/document captures).

Usage:
    python scripts/run.py                # bot + auto-process every 5 minutes
    python scripts/run.py --interval 10  # auto-process every 10 minutes
    python scripts/run.py --manual       # bot only; process via /process
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from telegram_bot import TelegramBot
from processor import Processor
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class KaniMisoRunner:
    """Telegram bot + periodic processor."""

    def __init__(self, process_interval_minutes: int = 5, auto_process: bool = True):
        """
        Args:
            process_interval_minutes: Minutes between auto-processing passes.
            auto_process: If False, process only on the /process command.
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or bot_token == "your_bot_token_here":
            logger.error("TELEGRAM_BOT_TOKEN not set in config/.env (see SETUP.md)")
            sys.exit(1)

        # TelegramBot enforces the mandatory chat allowlist (raises if unset).
        try:
            self.bot = TelegramBot(bot_token, chat_id)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)

        # Wire the /process command to a processing pass with notifications.
        self.bot.on_process_request = self.run_processor

        self.process_interval = process_interval_minutes * 60
        self.auto_process = auto_process
        self.last_process_time = time.time()
        self.running = True

    def run_processor(self, chat_id: Optional[int] = None) -> dict:
        """Run one processing pass; report via Telegram if chat_id is given."""
        try:
            logger.info("Starting processing...")
            if chat_id:
                self.bot.send_message(chat_id, "⏳ Processing captures...")

            processor = Processor()
            result = processor.process_batch()

            if chat_id:
                if result['processed'] > 0:
                    msg = f"✅ Processed {result['processed']} captures\n"
                    if result.get('commit_sha'):
                        msg += f"Commit: `{result['commit_sha'][:8]}`"
                    self.bot.send_message(chat_id, msg)
                elif result['failed'] > 0:
                    self.bot.send_message(chat_id, f"❌ {result['failed']} captures failed")
                else:
                    self.bot.send_message(chat_id, "📭 No pending captures")

            return result

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            if chat_id:
                self.bot.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
            return {'processed': 0, 'failed': 0}

    def run(self):
        """Main loop: poll Telegram, process on schedule."""
        logger.info("=" * 60)
        logger.info("Kani-miso Running (bot + processor)")
        logger.info("=" * 60)
        if self.auto_process:
            logger.info(f"Auto-processing every {self.process_interval // 60} min")
        else:
            logger.info("Manual mode: use /process in Telegram to process")
        logger.info("Press Ctrl+C to stop")
        logger.info("")

        def signal_handler(sig, frame):
            logger.info("\nShutting down...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            self.bot.poll_once()

            if self.auto_process:
                elapsed = time.time() - self.last_process_time
                if elapsed >= self.process_interval:
                    pending = self.bot.queue.get_stats().get('pending', 0)
                    if pending > 0:
                        logger.info(f"Auto-processing {pending} pending captures...")
                        self.run_processor()
                    self.last_process_time = time.time()

        logger.info("Goodbye!")


def main():
    parser = argparse.ArgumentParser(description="Kani-miso Runner (bot + processor)")
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=5,
        help='Auto-process interval in minutes (default: 5)'
    )
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='Disable auto-processing (use /process command instead)'
    )
    args = parser.parse_args()

    runner = KaniMisoRunner(
        process_interval_minutes=args.interval,
        auto_process=not args.manual,
    )
    runner.run()


if __name__ == "__main__":
    main()

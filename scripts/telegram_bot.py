"""
Telegram Bot for Second Brain
Uses Telegram HTTP API directly (no library dependencies, works with Python 3.14)
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from queue_manager import QueueManager
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class TelegramBot:
    """Simple Telegram bot using HTTP API."""

    def __init__(self, bot_token: str, allowed_chat_id: Optional[str] = None):
        """
        Initialize Telegram bot.

        Args:
            bot_token: Telegram bot token from BotFather
            allowed_chat_id: Optional chat ID to restrict to
        """
        self.bot_token = bot_token
        self.allowed_chat_id = int(allowed_chat_id) if allowed_chat_id else None
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0

        # Initialize queue
        repo_root = Path(__file__).parent.parent
        queue_db = repo_root / "queue" / "captures.db"
        self.queue = QueueManager(queue_db)

        logger.info("Telegram bot initialized")
        if self.allowed_chat_id:
            logger.info(f"Listening to chat ID: {self.allowed_chat_id}")
        else:
            logger.info("Listening to ALL chats (no restriction)")

    def send_message(self, chat_id: int, text: str):
        """Send a message to a Telegram chat."""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    def get_updates(self, timeout: int = 30):
        """Get updates from Telegram."""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": timeout,
        }

        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return None

    def parse_message(self, message_text: str) -> Dict[str, Any]:
        """
        Parse a Telegram message into capture fields.

        Args:
            message_text: Raw message text

        Returns:
            Dictionary of parsed fields
        """
        lines = message_text.strip().split('\n')

        # Extract type from first line
        first_line = lines[0] if lines else ""
        capture_type = "Thought"  # default

        type_patterns = {
            'Thought:': 'Thought',
            'Reflection:': 'Reflection',
            'Question:': 'Question',
            'Source:': 'Source',
            'Quote:': 'Quote',
            'Idea:': 'Idea',
            'Log:': 'Log',
        }

        for pattern, type_name in type_patterns.items():
            if first_line.startswith(pattern):
                capture_type = type_name
                # Remove the type prefix from first line
                first_line = first_line[len(pattern):].strip()
                lines[0] = first_line
                break

        # Parse context fields
        context_fields = {
            'surface': None,
            'mood': None,
            'energy': None,
            'confidence': None,
            'trigger': None,
            'context': None,
        }

        body_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for context field
            matched = False
            for field in context_fields.keys():
                pattern = f"{field.capitalize()}:"
                if line.startswith(pattern):
                    value = line[len(pattern):].strip()
                    context_fields[field] = value
                    matched = True
                    break

            # If not a context field, it's part of the body
            if not matched:
                body_lines.append(line)

        # Reconstruct body
        body = '\n'.join(body_lines)

        return {
            'type': capture_type,
            'body': body,
            **context_fields
        }

    def handle_command(self, chat_id: int, command: str, args: str):
        """Handle bot commands."""
        if command == '/start':
            welcome = (
                f"🧠 *Second Brain Bot*\n\n"
                f"Your chat ID: `{chat_id}`\n\n"
                f"Send me your thoughts and I'll save them to the queue!\n\n"
                f"Commands:\n"
                f"/help - Show message format\n"
                f"/stats - Queue statistics\n"
            )
            self.send_message(chat_id, welcome)

        elif command == '/help':
            help_text = (
                "*Message Format:*\n\n"
                "Basic:\n"
                "`Just type your thought`\n\n"
                "With type:\n"
                "`Thought: your thought here`\n"
                "`Reflection: personal note`\n"
                "`Question: something to explore`\n\n"
                "With context:\n"
                "`Thought: your thought`\n"
                "`Mood: curious`\n"
                "`Energy: high`\n\n"
                "Fields: Surface, Mood, Energy, Confidence, Trigger, Context"
            )
            self.send_message(chat_id, help_text)

        elif command == '/stats':
            stats = self.queue.get_stats()
            stats_text = "*Queue Statistics:*\n\n"
            for status, count in stats.items():
                stats_text += f"{status.capitalize()}: {count}\n"
            total = sum(stats.values())
            stats_text += f"\nTotal: {total}"
            self.send_message(chat_id, stats_text)

        else:
            self.send_message(chat_id, f"Unknown command: {command}")

    def handle_message(self, update: Dict[str, Any]):
        """Handle an incoming message."""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')

            if not chat_id or not text:
                return

            # Check if chat is allowed
            if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                logger.warning(f"Ignoring message from unauthorized chat: {chat_id}")
                return

            # Handle commands
            if text.startswith('/'):
                command = text.split()[0]
                args = ' '.join(text.split()[1:])
                self.handle_command(chat_id, command, args)
                return

            # Parse message
            parsed = self.parse_message(text)

            # Add to queue
            capture_id = self.queue.add_capture(
                body=parsed['body'],
                captured_at=datetime.now(),
                type=parsed['type'],
                surface=parsed['surface'] or 'mobile',  # Default to mobile for Telegram
                telegram_message_id=message.get('message_id'),
                mood=parsed['mood'],
                energy=parsed['energy'],
                confidence=parsed['confidence'],
                trigger=parsed['trigger'],
                context=parsed['context'],
            )

            # Confirm
            confirmation = f"✅ Captured #{capture_id}\n"
            if parsed['type'] != 'Thought':
                confirmation += f"Type: {parsed['type']}\n"
            if parsed['mood']:
                confirmation += f"Mood: {parsed['mood']}"

            self.send_message(chat_id, confirmation)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            if chat_id:
                self.send_message(chat_id, f"❌ Error: {str(e)}")

    def run(self):
        """Run the bot (blocking)."""
        logger.info("=" * 60)
        logger.info("Second Brain Telegram Bot Starting")
        logger.info("=" * 60)
        logger.info("Bot is running. Press Ctrl+C to stop.")
        logger.info("")

        try:
            while True:
                # Get updates
                result = self.get_updates()

                if not result or not result.get('ok'):
                    time.sleep(1)
                    continue

                # Process updates
                updates = result.get('result', [])

                for update in updates:
                    self.last_update_id = update['update_id']
                    self.handle_message(update)

        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    # Get credentials from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in config/.env")
        logger.error("Please set your bot token from @BotFather")
        logger.error("See TELEGRAM_SETUP.md for instructions")
        sys.exit(1)

    if bot_token == "your_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN is still the placeholder value")
        logger.error("Please replace with your actual bot token")
        sys.exit(1)

    # Create and run bot
    bot = TelegramBot(bot_token, chat_id)
    bot.run()


if __name__ == "__main__":
    main()

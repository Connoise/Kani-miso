"""
Telegram Bot for Second Brain
Uses Telegram HTTP API directly (no library dependencies, works with Python 3.14)
Supports both text messages and image captures.
"""

import os
import sys
import time
import json
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from queue_manager import QueueManager
from utils.logger import setup_logger
from utils.image_manager import ImageManager

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

        # Load config
        repo_root = Path(__file__).parent.parent
        config_path = repo_root / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Get notes root for image storage
        notes_root = self.config.get('notes_root', '.')
        if notes_root == '.':
            notes_root = repo_root
        else:
            notes_root = Path(notes_root)

        # Initialize queue
        queue_db = repo_root / "queue" / "captures.db"
        self.queue = QueueManager(queue_db)

        # Initialize image manager
        self.image_manager = ImageManager(notes_root, bot_token)

        # Image configuration
        self.images_enabled = self.config.get('images', {}).get('enabled', True)
        self.max_pending_images = self.config.get('images', {}).get('max_pending_images', 10)

        logger.info("Telegram bot initialized")
        if self.allowed_chat_id:
            logger.info(f"Listening to chat ID: {self.allowed_chat_id}")
        else:
            logger.info("Listening to ALL chats (no restriction)")
        if self.images_enabled:
            logger.info("Image capture enabled")

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

    def get_updates(self, timeout: int = 5):
        """Get updates from Telegram."""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": timeout,
        }

        try:
            response = requests.get(url, params=params, timeout=timeout + 2)
            response.raise_for_status()
            return response.json()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # Don't log timeout errors, they're normal
            if "timeout" not in str(e).lower():
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

        # Extract type from first line (case-insensitive)
        first_line = lines[0] if lines else ""
        capture_type = "Thought"  # default

        type_patterns = {
            'thought:': 'Thought',
            'reflection:': 'Reflection',
            'question:': 'Question',
            'source:': 'Source',
            'quote:': 'Quote',
            'idea:': 'Idea',
            'log:': 'Log',
            'tweet:': 'Tweet',
        }

        first_line_lower = first_line.lower()
        for pattern, type_name in type_patterns.items():
            if first_line_lower.startswith(pattern):
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

            # Check for context field (case-insensitive)
            matched = False
            line_lower = line.lower()
            for field in context_fields.keys():
                pattern = f"{field}:"
                if line_lower.startswith(pattern):
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
                f"/pending - Show pending images\n"
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
                "Fields: Surface, Mood, Energy, Confidence, Trigger, Context\n\n"
                "*Images:*\n"
                "Send photos, then follow with text to create a combined note."
            )
            self.send_message(chat_id, help_text)

        elif command == '/stats':
            stats = self.queue.get_stats()
            stats_text = "*Queue Statistics:*\n\n"
            for status, count in stats.items():
                stats_text += f"{status.capitalize()}: {count}\n"
            total = sum(stats.values())
            stats_text += f"\nTotal: {total}"

            # Add pending images count
            pending_images = self.queue.get_pending_image_count(chat_id)
            if pending_images > 0:
                stats_text += f"\n\n📷 Pending images: {pending_images}"

            self.send_message(chat_id, stats_text)

        elif command == '/pending':
            pending_images = self.queue.get_pending_images(chat_id)
            if pending_images:
                text = f"*Pending Images:* {len(pending_images)}\n\n"
                text += "Send a text message to associate these images with your capture."
            else:
                text = "No pending images."
            self.send_message(chat_id, text)

        else:
            self.send_message(chat_id, f"Unknown command: {command}")

    def handle_photo(self, update: Dict[str, Any]):
        """Handle an incoming photo message."""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            photos = message.get('photo', [])
            caption = message.get('caption', '')

            if not chat_id or not photos:
                return

            # Check if chat is allowed
            if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                logger.warning(f"Ignoring photo from unauthorized chat: {chat_id}")
                return

            if not self.images_enabled:
                self.send_message(chat_id, "❌ Image capture is disabled")
                return

            # Get the largest photo (last in array)
            largest_photo = photos[-1]
            file_id = largest_photo['file_id']

            # Download and save the image
            captured_at = datetime.now()
            local_path, error = self.image_manager.download_telegram_photo(
                file_id,
                captured_at=captured_at
            )

            if error:
                self.send_message(chat_id, f"❌ Failed to save image: {error}")
                return

            # Add to pending images
            image_id = self.queue.add_pending_image(
                chat_id=chat_id,
                file_id=file_id,
                file_path=str(local_path),
                captured_at=captured_at,
                telegram_message_id=message.get('message_id'),
            )

            pending_count = self.queue.get_pending_image_count(chat_id)

            # If there's a caption, treat it as the associated text
            if caption:
                self._create_capture_with_images(chat_id, caption, message)
            else:
                # Notify user about pending image
                self.send_message(
                    chat_id,
                    f"📷 Image saved ({pending_count} pending)\nSend text to create note."
                )

        except Exception as e:
            logger.error(f"Error handling photo: {e}", exc_info=True)
            if chat_id:
                self.send_message(chat_id, f"❌ Error: {str(e)}")

    def _create_capture_with_images(
        self,
        chat_id: int,
        text: str,
        message: Dict[str, Any],
    ) -> int:
        """
        Create a capture with associated pending images.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            message: Original Telegram message

        Returns:
            Capture ID
        """
        # Parse the text message
        parsed = self.parse_message(text)

        # Get pending images
        pending_images = self.queue.get_pending_images(chat_id)
        image_paths = [img['file_path'] for img in pending_images]

        # Add to queue with image paths
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

        # Update capture with image paths
        if image_paths:
            self.queue.update_capture_image_paths(capture_id, image_paths)

            # Associate pending images with this capture
            image_ids = [img['id'] for img in pending_images]
            self.queue.associate_images_with_capture(image_ids, capture_id)

        return capture_id

    def handle_message(self, update: Dict[str, Any]):
        """Handle an incoming message (text or photo)."""
        try:
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')

            if not chat_id:
                return

            # Check if chat is allowed
            if self.allowed_chat_id and chat_id != self.allowed_chat_id:
                logger.warning(f"Ignoring message from unauthorized chat: {chat_id}")
                return

            # Check if this is a photo message
            if message.get('photo'):
                self.handle_photo(update)
                return

            text = message.get('text', '')
            if not text:
                return

            # Handle commands
            if text.startswith('/'):
                command = text.split()[0]
                args = ' '.join(text.split()[1:])
                self.handle_command(chat_id, command, args)
                return

            # Check for pending images to associate with this text
            pending_count = self.queue.get_pending_image_count(chat_id)

            if pending_count > 0:
                # Create capture with associated images
                capture_id = self._create_capture_with_images(chat_id, text, message)
                parsed = self.parse_message(text)

                # Confirm with image info
                confirmation = f"✅ Captured #{capture_id}\n"
                confirmation += f"📷 {pending_count} image(s) attached\n"
                if parsed['type'] != 'Thought':
                    confirmation += f"Type: {parsed['type']}\n"
                if parsed['mood']:
                    confirmation += f"Mood: {parsed['mood']}"

                self.send_message(chat_id, confirmation)
            else:
                # Regular text capture (no images)
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

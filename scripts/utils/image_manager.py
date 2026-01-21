"""
Image Manager for Second Brain
Handles downloading images from Telegram and organizing them by date.
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import yaml

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ImageManager:
    """Manages image storage with date-based organization."""

    def __init__(self, notes_root: Path, bot_token: str):
        """
        Initialize image manager.

        Args:
            notes_root: Path to notes storage directory
            bot_token: Telegram bot token for API calls
        """
        self.notes_root = Path(notes_root)
        self.bot_token = bot_token
        self.images_base = self.notes_root / "images"
        self.images_base.mkdir(parents=True, exist_ok=True)

        logger.info(f"Image manager initialized. Storage: {self.images_base}")

    def get_date_folder(self, date: datetime = None) -> Path:
        """
        Get or create date-based folder for image storage.

        Args:
            date: Date for folder (defaults to now)

        Returns:
            Path to date folder (images/YYYY/MM/DD/)
        """
        if date is None:
            date = datetime.now()

        date_folder = self.images_base / date.strftime("%Y") / date.strftime("%m") / date.strftime("%d")
        date_folder.mkdir(parents=True, exist_ok=True)
        return date_folder

    def get_next_image_name(self, date_folder: Path, extension: str = ".jpg") -> str:
        """
        Get the next sequential image name for the folder.

        Args:
            date_folder: Date folder path
            extension: File extension

        Returns:
            Filename like "image-001.jpg"
        """
        existing = list(date_folder.glob(f"image-*{extension}"))
        if not existing:
            return f"image-001{extension}"

        # Find highest number
        numbers = []
        for f in existing:
            try:
                num = int(f.stem.split('-')[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue

        next_num = max(numbers) + 1 if numbers else 1
        return f"image-{next_num:03d}{extension}"

    def download_telegram_photo(
        self,
        file_id: str,
        captured_at: datetime = None,
    ) -> Tuple[Optional[Path], Optional[str]]:
        """
        Download a photo from Telegram and save to date-organized folder.

        Args:
            file_id: Telegram file_id
            captured_at: When the photo was captured

        Returns:
            Tuple of (local_path, error_message)
        """
        try:
            # Get file path from Telegram
            file_info_url = f"https://api.telegram.org/bot{self.bot_token}/getFile"
            response = requests.get(file_info_url, params={"file_id": file_id}, timeout=10)
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                return None, f"Failed to get file info: {result.get('description', 'Unknown error')}"

            telegram_file_path = result["result"]["file_path"]

            # Determine extension from Telegram path
            ext = Path(telegram_file_path).suffix or ".jpg"

            # Get date folder and filename
            date_folder = self.get_date_folder(captured_at)
            filename = self.get_next_image_name(date_folder, ext)
            local_path = date_folder / filename

            # Download the file
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{telegram_file_path}"
            download_response = requests.get(download_url, timeout=30)
            download_response.raise_for_status()

            # Save to local path
            with open(local_path, 'wb') as f:
                f.write(download_response.content)

            logger.info(f"Downloaded image to: {local_path}")
            return local_path, None

        except requests.RequestException as e:
            error_msg = f"Network error downloading image: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error downloading image: {e}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    def get_relative_path(self, image_path: Path) -> str:
        """
        Get path relative to notes root for use in markdown.

        Args:
            image_path: Absolute path to image

        Returns:
            Relative path string
        """
        return str(image_path.relative_to(self.notes_root))

    def get_obsidian_embed(self, image_path: Path) -> str:
        """
        Generate Obsidian-compatible image embed syntax.

        Args:
            image_path: Path to image (absolute or relative)

        Returns:
            Obsidian embed string like ![[images/2026/01/21/image-001.jpg]]
        """
        if image_path.is_absolute():
            rel_path = self.get_relative_path(image_path)
        else:
            rel_path = str(image_path)

        # Use forward slashes for Obsidian compatibility
        rel_path = rel_path.replace("\\", "/")
        return f"![[{rel_path}]]"


def load_image_manager(config_path: Path = None, bot_token: str = None) -> ImageManager:
    """
    Create ImageManager from config.

    Args:
        config_path: Path to config.yaml
        bot_token: Telegram bot token

    Returns:
        Configured ImageManager instance
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    notes_root = config.get('notes_root', '.')
    if notes_root == '.':
        notes_root = Path(__file__).parent.parent.parent
    else:
        notes_root = Path(notes_root)

    if bot_token is None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    return ImageManager(notes_root, bot_token)

"""
Document Manager for Kani-miso
Handles downloading documents (PDFs, etc.) from Telegram and organizing them by date.
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import yaml

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentManager:
    """Manages document storage with date-based organization."""

    # Supported document types and their extensions
    SUPPORTED_TYPES = {
        'application/pdf': '.pdf',
        'application/x-pdf': '.pdf',
        'text/plain': '.txt',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/epub+zip': '.epub',
    }

    # File extensions we'll process
    PROCESSABLE_EXTENSIONS = {'.pdf'}

    def __init__(self, notes_root: Path, bot_token: str):
        """
        Initialize document manager.

        Args:
            notes_root: Path to notes storage directory
            bot_token: Telegram bot token for API calls
        """
        self.notes_root = Path(notes_root)
        self.bot_token = bot_token
        self.documents_base = self.notes_root / "documents"
        self.documents_base.mkdir(parents=True, exist_ok=True)

        logger.info(f"Document manager initialized. Storage: {self.documents_base}")

    def get_date_folder(self, date: datetime = None) -> Path:
        """
        Get or create date-based folder for document storage.

        Args:
            date: Date for folder (defaults to now)

        Returns:
            Path to date folder (documents/YYYY/MM/DD/)
        """
        if date is None:
            date = datetime.now()

        date_folder = self.documents_base / date.strftime("%Y") / date.strftime("%m") / date.strftime("%d")
        date_folder.mkdir(parents=True, exist_ok=True)
        return date_folder

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be filesystem-safe.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace problematic characters
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')

        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200 - len(ext)] + ext

        return filename or 'document'

    def get_unique_filename(self, date_folder: Path, filename: str) -> str:
        """
        Get a unique filename, adding numbers if file exists.

        Args:
            date_folder: Date folder path
            filename: Desired filename

        Returns:
            Unique filename
        """
        sanitized = self.sanitize_filename(filename)
        target_path = date_folder / sanitized

        if not target_path.exists():
            return sanitized

        # Add number suffix
        name, ext = os.path.splitext(sanitized)
        counter = 1
        while True:
            new_name = f"{name}-{counter:03d}{ext}"
            if not (date_folder / new_name).exists():
                return new_name
            counter += 1

    def is_processable(self, filename: str) -> bool:
        """
        Check if a document type can be processed (text extracted).

        Args:
            filename: Document filename

        Returns:
            True if processable
        """
        ext = Path(filename).suffix.lower()
        return ext in self.PROCESSABLE_EXTENSIONS

    def download_telegram_document(
        self,
        file_id: str,
        file_name: str,
        mime_type: str = None,
        captured_at: datetime = None,
    ) -> Tuple[Optional[Path], Optional[str]]:
        """
        Download a document from Telegram and save to date-organized folder.

        Args:
            file_id: Telegram file_id
            file_name: Original filename from Telegram
            mime_type: MIME type of the document
            captured_at: When the document was captured

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
            file_size = result["result"].get("file_size", 0)

            # Log file info
            logger.info(f"Downloading document: {file_name} ({file_size} bytes)")

            # Check file size (Telegram bot API limit is 20MB)
            max_size = 20 * 1024 * 1024  # 20MB
            if file_size > max_size:
                return None, f"File too large: {file_size} bytes (max {max_size})"

            # Get date folder and unique filename
            date_folder = self.get_date_folder(captured_at)
            unique_name = self.get_unique_filename(date_folder, file_name)
            local_path = date_folder / unique_name

            # Download the file
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{telegram_file_path}"
            download_response = requests.get(download_url, timeout=60, stream=True)
            download_response.raise_for_status()

            # Save to local path
            with open(local_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded document to: {local_path}")
            return local_path, None

        except requests.RequestException as e:
            error_msg = f"Network error downloading document: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error downloading document: {e}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    def get_relative_path(self, doc_path: Path) -> str:
        """
        Get path relative to notes root for use in markdown.

        Args:
            doc_path: Absolute path to document

        Returns:
            Relative path string
        """
        return str(doc_path.relative_to(self.notes_root))

    def get_obsidian_link(self, doc_path: Path) -> str:
        """
        Generate Obsidian-compatible link to document.

        Args:
            doc_path: Path to document (absolute or relative)

        Returns:
            Obsidian link string like [[documents/2026/01/21/file.pdf]]
        """
        if doc_path.is_absolute():
            rel_path = self.get_relative_path(doc_path)
        else:
            rel_path = str(doc_path)

        # Use forward slashes for Obsidian compatibility
        rel_path = rel_path.replace("\\", "/")
        return f"[[{rel_path}]]"

    def get_document_info(self, doc_path: Path) -> Dict[str, Any]:
        """
        Get information about a stored document.

        Args:
            doc_path: Path to document

        Returns:
            Dictionary with document info
        """
        path = Path(doc_path)
        return {
            'path': str(path),
            'name': path.name,
            'extension': path.suffix.lower(),
            'size': path.stat().st_size if path.exists() else 0,
            'processable': self.is_processable(path.name),
            'relative_path': self.get_relative_path(path) if path.is_absolute() else str(path),
        }


def load_document_manager(config_path: Path = None, bot_token: str = None) -> DocumentManager:
    """
    Create DocumentManager from config.

    Args:
        config_path: Path to config.yaml
        bot_token: Telegram bot token

    Returns:
        Configured DocumentManager instance
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

    return DocumentManager(notes_root, bot_token)

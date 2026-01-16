"""
Logging utility for Second Brain automation.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows color support
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)


def setup_logger(name: str, log_file: str = None, level: str = "INFO", console: bool = True) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console: Whether to output to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = ColoredFormatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger

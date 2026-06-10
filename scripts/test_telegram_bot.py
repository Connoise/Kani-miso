"""
Quick test to verify Telegram bot configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


def main():
    """Check Telegram bot configuration."""
    print("\n" + "=" * 60)
    print("Telegram Bot Configuration Check")
    print("=" * 60 + "\n")

    # Check bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in config/.env")
        print("\nTo fix:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Copy the bot token")
        print("3. Add to config/.env:")
        print("   TELEGRAM_BOT_TOKEN=your_token_here")
        print("\nSee SETUP.md for detailed instructions")
        return False

    if bot_token == "your_bot_token_here":
        print("❌ TELEGRAM_BOT_TOKEN is still the placeholder")
        print("\nReplace with your actual bot token from @BotFather")
        return False

    print(f"✓ Bot token found: {bot_token[:10]}...")

    # Check chat ID
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not chat_id:
        print("\n⚠️  TELEGRAM_CHAT_ID not set (optional)")
        print("\nBot will accept messages from any chat.")
        print("To restrict to your chat only:")
        print("1. Send /start to your bot")
        print("2. Bot will reply with your chat ID")
        print("3. Add to config/.env:")
        print("   TELEGRAM_CHAT_ID=your_chat_id")
    elif chat_id == "your_chat_id_here":
        print("\n⚠️  TELEGRAM_CHAT_ID is still the placeholder")
    else:
        print(f"✓ Chat ID configured: {chat_id}")

    # Try to import telegram library
    print("\n" + "-" * 60)
    print("Checking python-telegram-bot library...")

    try:
        import telegram
        print(f"✓ python-telegram-bot installed (version {telegram.__version__})")
    except ImportError:
        print("❌ python-telegram-bot not installed")
        print("\nTo fix:")
        print("  pip install -r requirements.txt")
        return False

    # All good
    print("\n" + "=" * 60)
    print("✓ Telegram bot configuration looks good!")
    print("\nNext steps:")
    print("1. Run: python scripts/telegram_bot.py")
    print("2. Send a test message to your bot on Telegram")
    print("3. Check that bot confirms with ✅")
    print("4. Run: python scripts/processor.py")
    print("\nSee SETUP.md for detailed guide")
    print("=" * 60 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
Tweet to Telegram Forwarder for Second Brain
Fetches tweets and forwards them to Telegram chat for processing.
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from twitter_fetcher import TwitterFetcher
from tweet_tracker import TweetTracker
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class TweetToTelegram:
    """Forwards tweets to Telegram for processing by Second Brain."""

    def __init__(
        self,
        twitter_bearer_token: str,
        twitter_user_id: str,
        telegram_bot_token: str,
        telegram_chat_id: str,
    ):
        """
        Initialize the forwarder.

        Args:
            twitter_bearer_token: Twitter API bearer token
            twitter_user_id: Twitter user ID to fetch tweets from
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat ID to forward to
        """
        self.twitter = TwitterFetcher(twitter_bearer_token, twitter_user_id)
        self.telegram_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_base_url = f"https://api.telegram.org/bot{telegram_bot_token}"

        # Initialize tracker
        repo_root = Path(__file__).parent.parent
        self.tracker = TweetTracker(repo_root / "queue" / "tweet_tracker.db")

        logger.info("Tweet-to-Telegram forwarder initialized")

    def format_tweet_for_telegram(self, tweet: Dict[str, Any]) -> str:
        """
        Format a tweet as a Telegram message in Second Brain format.

        Args:
            tweet: Tweet dictionary from Twitter API

        Returns:
            Formatted message string
        """
        text = tweet.get("text", "")
        created_at = tweet.get("created_at", "")
        tweet_id = tweet.get("id", "")
        media = tweet.get("media", [])

        # Build the message in Second Brain format
        lines = [
            "Tweet: self-published tweet",
            "Surface: twitter",
            f"Context: Posted on Twitter/X at {created_at}",
            f"Trigger: self-published tweet (ID: {tweet_id})",
            "",
            text,
        ]

        # Add media URLs if present
        if media:
            lines.append("")
            lines.append("Attachments:")
            for m in media:
                media_type = m.get("type", "unknown")
                url = m.get("url") or m.get("preview_image_url")
                if url:
                    lines.append(f"- [{media_type}] {url}")

        return "\n".join(lines)

    def send_to_telegram(self, message: str) -> Optional[int]:
        """
        Send a message to Telegram.

        Args:
            message: Message text to send

        Returns:
            Telegram message ID if successful, None otherwise
        """
        url = f"{self.telegram_base_url}/sendMessage"
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                message_id = result.get("result", {}).get("message_id")
                logger.info(f"Sent message to Telegram (ID: {message_id})")
                return message_id
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return None

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

    def send_photo_to_telegram(self, photo_url: str, caption: str) -> Optional[int]:
        """
        Send a photo to Telegram with caption.

        Args:
            photo_url: URL of the photo
            caption: Caption text

        Returns:
            Telegram message ID if successful, None otherwise
        """
        url = f"{self.telegram_base_url}/sendPhoto"
        data = {
            "chat_id": self.telegram_chat_id,
            "photo": photo_url,
            "caption": caption[:1024],  # Telegram caption limit
        }

        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                message_id = result.get("result", {}).get("message_id")
                logger.info(f"Sent photo to Telegram (ID: {message_id})")
                return message_id
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return None

        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return None

    def forward_tweet(self, tweet: Dict[str, Any]) -> bool:
        """
        Forward a single tweet to Telegram.

        Args:
            tweet: Tweet dictionary

        Returns:
            True if forwarded successfully
        """
        tweet_id = tweet.get("id")
        media = tweet.get("media", [])

        # Check if already forwarded
        if self.tracker.is_forwarded(tweet_id):
            logger.debug(f"Tweet {tweet_id} already forwarded, skipping")
            return False

        # Format the message
        message = self.format_tweet_for_telegram(tweet)

        # Send text message first
        telegram_message_id = self.send_to_telegram(message)

        if telegram_message_id is None:
            logger.error(f"Failed to forward tweet {tweet_id}")
            return False

        # Send photos separately for better display
        photo_media = [m for m in media if m.get("type") == "photo"]
        for photo in photo_media:
            photo_url = photo.get("url") or photo.get("preview_image_url")
            if photo_url:
                alt_text = photo.get("alt_text", "Tweet image")
                self.send_photo_to_telegram(photo_url, f"📷 {alt_text}")
                time.sleep(0.5)  # Rate limit protection

        # Mark as forwarded
        self.tracker.mark_forwarded(
            tweet_id=tweet_id,
            tweet_created_at=tweet.get("created_at"),
            tweet_text=tweet.get("text"),
            telegram_message_id=telegram_message_id,
            has_media=len(media) > 0,
            media_count=len(media),
        )

        return True

    def sync(
        self,
        max_tweets: int = 10,
        include_replies: bool = True,
        include_retweets: bool = True,
    ) -> Dict[str, int]:
        """
        Sync recent tweets to Telegram.

        Args:
            max_tweets: Maximum number of tweets to fetch
            include_replies: Include reply tweets
            include_retweets: Include retweets

        Returns:
            Stats dictionary with forwarded/skipped counts
        """
        logger.info("Starting tweet sync...")

        # Get last processed tweet ID for efficient fetching
        since_id = self.tracker.get_last_tweet_id()
        if since_id:
            logger.info(f"Fetching tweets since ID: {since_id}")

        # Fetch tweets
        tweets = self.twitter.get_user_tweets(
            since_id=since_id,
            max_results=max_tweets,
            include_replies=include_replies,
            include_retweets=include_retweets,
        )

        if not tweets:
            logger.info("No new tweets found")
            return {"fetched": 0, "forwarded": 0, "skipped": 0}

        # Process in reverse order (oldest first) to maintain chronological order
        tweets.reverse()

        stats = {"fetched": len(tweets), "forwarded": 0, "skipped": 0}
        newest_id = None

        for tweet in tweets:
            tweet_id = tweet.get("id")
            newest_id = tweet_id  # Track the newest

            if self.forward_tweet(tweet):
                stats["forwarded"] += 1
                # Small delay between messages
                time.sleep(1)
            else:
                stats["skipped"] += 1

        # Update last tweet ID
        if newest_id:
            self.tracker.set_last_tweet_id(newest_id)

        logger.info(
            f"Sync complete: {stats['fetched']} fetched, "
            f"{stats['forwarded']} forwarded, {stats['skipped']} skipped"
        )

        return stats

    def show_stats(self):
        """Display forwarding statistics."""
        stats = self.tracker.get_stats()
        print("\n" + "=" * 50)
        print("Tweet-to-Telegram Sync Statistics")
        print("=" * 50)
        print(f"Total forwarded:     {stats['total_forwarded']}")
        print(f"With media:          {stats['with_media']}")
        print(f"Last tweet ID:       {stats['last_tweet_id'] or 'None'}")
        print("=" * 50)

        print("\nRecent forwards:")
        for tweet in self.tracker.get_recent(5):
            text = tweet.get("tweet_text", "")[:40]
            forwarded = tweet.get("forwarded_at", "")[:10]
            print(f"  [{forwarded}] {text}...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Forward tweets to Telegram for Second Brain processing"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sync recent tweets to Telegram",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show forwarding statistics",
    )
    parser.add_argument(
        "--max-tweets",
        type=int,
        default=10,
        help="Maximum tweets to fetch (default: 10)",
    )
    parser.add_argument(
        "--no-replies",
        action="store_true",
        help="Exclude reply tweets",
    )
    parser.add_argument(
        "--no-retweets",
        action="store_true",
        help="Exclude retweets",
    )
    parser.add_argument(
        "--lookup-user",
        type=str,
        metavar="USERNAME",
        help="Look up user ID for a Twitter username",
    )

    args = parser.parse_args()

    # Get credentials
    twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
    twitter_user_id = os.getenv("TWITTER_USER_ID")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Handle user lookup
    if args.lookup_user:
        if not twitter_bearer:
            logger.error("TWITTER_BEARER_TOKEN required for user lookup")
            sys.exit(1)
        fetcher = TwitterFetcher(twitter_bearer, "")
        user_id = fetcher.get_user_id_by_username(args.lookup_user)
        if user_id:
            print(f"\nUser @{args.lookup_user} has ID: {user_id}")
            print(f"\nAdd this to your config/.env:")
            print(f"TWITTER_USER_ID={user_id}")
        else:
            print(f"Could not find user @{args.lookup_user}")
        return

    # Validate credentials
    missing = []
    if not twitter_bearer:
        missing.append("TWITTER_BEARER_TOKEN")
    if not twitter_user_id:
        missing.append("TWITTER_USER_ID")
    if not telegram_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not telegram_chat_id:
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        logger.error("Please set them in config/.env")
        logger.error("See TWITTER_SETUP.md for instructions")
        sys.exit(1)

    # Initialize forwarder
    forwarder = TweetToTelegram(
        twitter_bearer_token=twitter_bearer,
        twitter_user_id=twitter_user_id,
        telegram_bot_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
    )

    # Execute requested action
    if args.stats:
        forwarder.show_stats()
    elif args.sync:
        stats = forwarder.sync(
            max_tweets=args.max_tweets,
            include_replies=not args.no_replies,
            include_retweets=not args.no_retweets,
        )
        print(f"\nSync complete:")
        print(f"  Fetched:   {stats['fetched']}")
        print(f"  Forwarded: {stats['forwarded']}")
        print(f"  Skipped:   {stats['skipped']}")
    else:
        # Default: show stats and run sync
        forwarder.show_stats()
        print("\n" + "-" * 50)
        print("Running sync...")
        print("-" * 50)
        stats = forwarder.sync(
            max_tweets=args.max_tweets,
            include_replies=not args.no_replies,
            include_retweets=not args.no_retweets,
        )
        print(f"\nSync complete:")
        print(f"  Fetched:   {stats['fetched']}")
        print(f"  Forwarded: {stats['forwarded']}")
        print(f"  Skipped:   {stats['skipped']}")


if __name__ == "__main__":
    main()

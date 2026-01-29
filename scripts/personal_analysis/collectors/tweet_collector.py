"""
Tweet collector for personal analysis.

Collects tweets from /tweets/ directory.
Supports both processed markdown files and raw tweet data.
"""

import json
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from ..models import Tweet

logger = logging.getLogger(__name__)


class TweetCollector:
    """Collect and parse tweets from the tweets directory."""

    def __init__(self, tweets_dir: Path):
        """
        Initialize the tweet collector.

        Args:
            tweets_dir: Path to the /tweets/ directory
        """
        self.tweets_dir = tweets_dir

    def collect_all(
        self,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[Tweet]:
        """
        Collect all tweets from the directory.

        Args:
            date_start: Optional start date filter
            date_end: Optional end date filter

        Returns:
            List of Tweet objects sorted by creation date
        """
        tweets = []

        if not self.tweets_dir.exists():
            logger.warning(f"Tweets directory does not exist: {self.tweets_dir}")
            return tweets

        # Try to collect from markdown files first
        md_tweets = self._collect_from_markdown()
        tweets.extend(md_tweets)

        # Also try to collect from JSON/JS files (Twitter archive format)
        json_tweets = self._collect_from_archive()
        tweets.extend(json_tweets)

        # Apply date filters
        filtered_tweets = []
        for tweet in tweets:
            if date_start and tweet.created_at < date_start:
                continue
            if date_end and tweet.created_at > date_end:
                continue
            filtered_tweets.append(tweet)

        # Remove duplicates by tweet_id
        seen_ids = set()
        unique_tweets = []
        for tweet in filtered_tweets:
            if tweet.tweet_id not in seen_ids:
                seen_ids.add(tweet.tweet_id)
                unique_tweets.append(tweet)

        # Sort by creation date
        return sorted(unique_tweets, key=lambda t: t.created_at)

    def _collect_from_markdown(self) -> List[Tweet]:
        """Collect tweets stored as markdown files."""
        tweets = []

        for md_file in self.tweets_dir.glob("*.md"):
            try:
                tweet = self._parse_markdown_tweet(md_file)
                if tweet:
                    tweets.append(tweet)
            except Exception as e:
                logger.error(f"Error parsing tweet markdown {md_file}: {e}")

        return tweets

    def _collect_from_archive(self) -> List[Tweet]:
        """Collect tweets from Twitter archive files."""
        tweets = []

        # Look for tweets.js or tweets.json
        archive_files = list(self.tweets_dir.glob("tweets.js")) + list(self.tweets_dir.glob("tweets.json"))

        for archive_file in archive_files:
            try:
                archive_tweets = self._parse_archive_file(archive_file)
                tweets.extend(archive_tweets)
            except Exception as e:
                logger.error(f"Error parsing tweet archive {archive_file}: {e}")

        return tweets

    def _parse_markdown_tweet(self, path: Path) -> Optional[Tweet]:
        """Parse a tweet stored as markdown."""
        content = path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(content)

        tweet_id = frontmatter.get("tweet_id", path.stem)
        text = body.strip()

        # Get creation date
        created_at = self._get_created_at(frontmatter, path)

        return Tweet(
            tweet_id=str(tweet_id),
            text=text,
            created_at=created_at,
            path=path,
            is_retweet=frontmatter.get("is_retweet", False),
            is_reply=frontmatter.get("is_reply", False),
            reply_to=frontmatter.get("reply_to"),
            hashtags=frontmatter.get("hashtags", []),
            mentions=frontmatter.get("mentions", []),
            urls=frontmatter.get("urls", []),
        )

    def _parse_archive_file(self, path: Path) -> List[Tweet]:
        """Parse a Twitter archive file."""
        content = path.read_text(encoding="utf-8")

        # Handle tweets.js format (starts with "window.YTD.tweets.part0 = ")
        if content.startswith("window.YTD"):
            json_start = content.find("[")
            if json_start == -1:
                return []
            content = content[json_start:]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {path}: {e}")
            return []

        tweets = []
        for item in data:
            # Handle nested tweet structure
            tweet_data = item.get("tweet", item)

            try:
                tweet = self._parse_tweet_dict(tweet_data)
                if tweet:
                    tweets.append(tweet)
            except Exception as e:
                logger.error(f"Error parsing tweet data: {e}")

        return tweets

    def _parse_tweet_dict(self, data: Dict[str, Any]) -> Optional[Tweet]:
        """Parse a tweet from dictionary data."""
        tweet_id = data.get("id_str", data.get("id", ""))
        text = data.get("full_text", data.get("text", ""))

        if not tweet_id or not text:
            return None

        # Parse created_at
        created_at_str = data.get("created_at", "")
        try:
            # Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
            created_at = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
            created_at = created_at.replace(tzinfo=None)  # Remove timezone for consistency
        except ValueError:
            created_at = datetime.now()

        # Check if retweet
        is_retweet = text.startswith("RT @") or "retweeted_status" in data

        # Check if reply
        is_reply = data.get("in_reply_to_status_id") is not None
        reply_to = data.get("in_reply_to_screen_name")

        # Extract entities
        entities = data.get("entities", {})
        hashtags = [h.get("text", "") for h in entities.get("hashtags", [])]
        mentions = [m.get("screen_name", "") for m in entities.get("user_mentions", [])]
        urls = [u.get("expanded_url", u.get("url", "")) for u in entities.get("urls", [])]

        return Tweet(
            tweet_id=str(tweet_id),
            text=text,
            created_at=created_at,
            is_retweet=is_retweet,
            is_reply=is_reply,
            reply_to=reply_to,
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
        )

    def _split_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Split content into frontmatter and body."""
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            frontmatter = {}

        body = parts[2].strip()
        return frontmatter, body

    def _get_created_at(self, frontmatter: Dict[str, Any], path: Path) -> datetime:
        """Get creation date from frontmatter or filename."""
        for field in ["created_at", "tweeted_at", "date"]:
            if field in frontmatter:
                value = frontmatter[field]
                if isinstance(value, datetime):
                    # Normalize to naive datetime
                    if value.tzinfo is not None:
                        return value.replace(tzinfo=None)
                    return value
                if isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        # Normalize to naive datetime
                        if dt.tzinfo is not None:
                            return dt.replace(tzinfo=None)
                        return dt
                    except ValueError:
                        pass

        # Try to extract from filename
        match = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                pass

        return datetime.fromtimestamp(path.stat().st_mtime)

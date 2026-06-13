"""
Twitter Archive Processor for Kani-miso
Processes exported Twitter archive data and adds tweets to the processing queue.

Twitter archive format:
- Request your data at: https://twitter.com/settings/download_your_data
- Extract the zip file
- Point this script at the extracted folder

Usage:
    python scripts/twitter_archive_processor.py /path/to/twitter-archive
    python scripts/twitter_archive_processor.py /path/to/twitter-archive --from 2023-01-01 --to 2023-12-31
    python scripts/twitter_archive_processor.py /path/to/twitter-archive --year 2023
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

sys.path.append(str(Path(__file__).parent))
from queue_manager import QueueManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TwitterArchiveProcessor:
    """Processes Twitter archive exports and adds tweets to the queue."""

    def __init__(self, archive_path: str, queue_manager: QueueManager):
        """
        Initialize the processor.

        Args:
            archive_path: Path to extracted Twitter archive folder
            queue_manager: QueueManager instance for adding captures
        """
        self.archive_path = Path(archive_path)
        self.queue = queue_manager
        self.tweets_file = self.archive_path / "data" / "tweets.js"

        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive path not found: {archive_path}")

        if not self.tweets_file.exists():
            # Try alternative locations
            alt_paths = [
                self.archive_path / "data" / "tweet.js",
                self.archive_path / "tweet.js",
                self.archive_path / "tweets.js",
            ]
            for alt in alt_paths:
                if alt.exists():
                    self.tweets_file = alt
                    break
            else:
                raise FileNotFoundError(
                    f"Could not find tweets.js in archive. "
                    f"Looked in: {self.tweets_file} and alternatives"
                )

        logger.info(f"Twitter archive processor initialized: {self.archive_path}")

    def parse_archive(self) -> List[Dict[str, Any]]:
        """
        Parse the Twitter archive tweets.js file.

        Returns:
            List of tweet dictionaries
        """
        logger.info(f"Parsing archive: {self.tweets_file}")

        with open(self.tweets_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Twitter archive format: window.YTD.tweets.part0 = [...]
        # Need to extract the JSON array
        json_match = re.search(r'=\s*(\[[\s\S]*\])\s*;?\s*$', content)
        if not json_match:
            # Try parsing as pure JSON
            try:
                tweets_data = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("Could not parse tweets.js - unexpected format")
        else:
            tweets_data = json.loads(json_match.group(1))

        # Extract tweet objects (archive wraps each in {"tweet": {...}})
        tweets = []
        for item in tweets_data:
            if isinstance(item, dict):
                if 'tweet' in item:
                    tweets.append(item['tweet'])
                else:
                    tweets.append(item)

        logger.info(f"Parsed {len(tweets)} tweets from archive")
        return tweets

    def parse_tweet_date(self, tweet: Dict[str, Any]) -> Optional[datetime]:
        """
        Parse the created_at field from a tweet.

        Args:
            tweet: Tweet dictionary

        Returns:
            datetime object or None if parsing fails
        """
        created_at = tweet.get('created_at', '')

        # Twitter archive format: "Sat Oct 10 20:19:24 +0000 2020"
        # or ISO format: "2020-10-10T20:19:24.000Z"

        formats = [
            "%a %b %d %H:%M:%S %z %Y",  # Twitter classic format
            "%Y-%m-%dT%H:%M:%S.%fZ",     # ISO format with milliseconds
            "%Y-%m-%dT%H:%M:%SZ",        # ISO format without milliseconds
            "%Y-%m-%d %H:%M:%S",         # Simple format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(created_at, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {created_at}")
        return None

    def filter_by_date_range(
        self,
        tweets: List[Dict[str, Any]],
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter tweets by date range.

        Args:
            tweets: List of tweet dictionaries
            from_date: Start date (inclusive)
            to_date: End date (inclusive)

        Returns:
            Filtered list of tweets
        """
        if not from_date and not to_date:
            return tweets

        filtered = []
        for tweet in tweets:
            tweet_date = self.parse_tweet_date(tweet)
            if not tweet_date:
                continue

            # Make naive if comparing with naive dates
            if tweet_date.tzinfo and from_date and not from_date.tzinfo:
                tweet_date = tweet_date.replace(tzinfo=None)

            if from_date and tweet_date < from_date:
                continue
            if to_date and tweet_date > to_date:
                continue

            filtered.append(tweet)

        logger.info(f"Filtered to {len(filtered)} tweets in date range")
        return filtered

    def format_tweet_body(self, tweet: Dict[str, Any]) -> str:
        """
        Format tweet content for Kani-miso.

        Args:
            tweet: Tweet dictionary

        Returns:
            Formatted tweet text
        """
        # Get the full text
        text = tweet.get('full_text') or tweet.get('text', '')

        # Get metadata
        tweet_id = tweet.get('id_str') or tweet.get('id', '')
        created_at = tweet.get('created_at', '')

        # Check for media
        media_urls = []
        entities = tweet.get('entities', {})
        extended = tweet.get('extended_entities', {})

        for media in extended.get('media', []) or entities.get('media', []):
            media_url = media.get('media_url_https') or media.get('media_url', '')
            media_type = media.get('type', 'photo')
            if media_url:
                media_urls.append(f"[{media_type}] {media_url}")

        # Check for URLs
        urls = []
        for url_entity in entities.get('urls', []):
            expanded = url_entity.get('expanded_url', '')
            if expanded:
                urls.append(expanded)

        # Build the body
        body_parts = [text]

        if urls:
            body_parts.append("")
            body_parts.append("Links:")
            for url in urls:
                body_parts.append(f"- {url}")

        if media_urls:
            body_parts.append("")
            body_parts.append("Media:")
            for media in media_urls:
                body_parts.append(f"- {media}")

        return "\n".join(body_parts)

    def add_tweet_to_queue(self, tweet: Dict[str, Any]) -> Optional[int]:
        """
        Add a single tweet to the processing queue.

        Args:
            tweet: Tweet dictionary

        Returns:
            Queue ID if successful, None otherwise
        """
        tweet_date = self.parse_tweet_date(tweet)
        if not tweet_date:
            tweet_date = datetime.now()

        # Make timezone-naive for storage
        if tweet_date.tzinfo:
            tweet_date = tweet_date.replace(tzinfo=None)

        tweet_id = tweet.get('id_str') or tweet.get('id', '')
        body = self.format_tweet_body(tweet)

        # Check for media attachments
        attachments = []
        entities = tweet.get('entities', {})
        extended = tweet.get('extended_entities', {})

        for media in extended.get('media', []) or entities.get('media', []):
            attachments.append({
                'type': media.get('type', 'photo'),
                'url': media.get('media_url_https') or media.get('media_url', ''),
            })

        try:
            capture_id = self.queue.add_capture(
                body=body,
                captured_at=tweet_date,
                type="Tweet",
                surface="twitter-archive",
                trigger=f"Twitter archive import (ID: {tweet_id})",
                context=f"Originally posted on Twitter",
                attachments=attachments if attachments else None,
                tweet_id=str(tweet_id) if tweet_id else None,
            )
            return capture_id
        except Exception as e:
            logger.error(f"Failed to add tweet {tweet_id}: {e}")
            return None

    def process(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """
        Process the archive and add tweets to queue.

        Args:
            from_date: Start date filter (inclusive)
            to_date: End date filter (inclusive)
            dry_run: If True, don't actually add to queue

        Returns:
            Stats dictionary
        """
        # Parse archive
        tweets = self.parse_archive()

        # Filter by date
        tweets = self.filter_by_date_range(tweets, from_date, to_date)

        # Sort by date (oldest first)
        tweets.sort(key=lambda t: self.parse_tweet_date(t) or datetime.min)

        stats = {
            'total': len(tweets),
            'added': 0,
            'skipped': 0,
            'failed': 0,
        }

        if dry_run:
            logger.info(f"DRY RUN: Would add {len(tweets)} tweets to queue")
            return stats

        # Process each tweet
        for i, tweet in enumerate(tweets, 1):
            if i % 100 == 0:
                logger.info(f"Processing tweet {i}/{len(tweets)}...")

            # Dedup: a tweet that was ever queued (any status) is skipped, so
            # re-importing a fresh full archive export only adds new tweets.
            tweet_id = str(tweet.get('id_str') or tweet.get('id', '') or '')
            if tweet_id and self.queue.has_tweet(tweet_id):
                stats['skipped'] += 1
                continue

            capture_id = self.add_tweet_to_queue(tweet)
            if capture_id:
                stats['added'] += 1
            else:
                stats['failed'] += 1

        logger.info(
            f"Processing complete: {stats['added']} added, "
            f"{stats['skipped']} skipped (already imported), "
            f"{stats['failed']} failed out of {stats['total']} total"
        )

        return stats

    def get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get the date range of tweets in the archive.

        Returns:
            Tuple of (earliest_date, latest_date)
        """
        tweets = self.parse_archive()

        dates = []
        for tweet in tweets:
            tweet_date = self.parse_tweet_date(tweet)
            if tweet_date:
                dates.append(tweet_date)

        if not dates:
            return None, None

        return min(dates), max(dates)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the archive.

        Returns:
            Stats dictionary
        """
        tweets = self.parse_archive()
        earliest, latest = self.get_date_range()

        # Count by year
        by_year = {}
        for tweet in tweets:
            tweet_date = self.parse_tweet_date(tweet)
            if tweet_date:
                year = tweet_date.year
                by_year[year] = by_year.get(year, 0) + 1

        return {
            'total_tweets': len(tweets),
            'earliest': earliest.isoformat() if earliest else None,
            'latest': latest.isoformat() if latest else None,
            'by_year': dict(sorted(by_year.items())),
        }


def parse_date(date_str: str) -> datetime:
    """Parse a date string in various formats."""
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Process Twitter archive and add tweets to Kani-miso queue"
    )
    parser.add_argument(
        "archive_path",
        help="Path to extracted Twitter archive folder",
    )
    parser.add_argument(
        "--from", "-f",
        dest="from_date",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to", "-t",
        dest="to_date",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--year", "-y",
        type=int,
        help="Process only tweets from this year",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show archive statistics without processing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without adding to queue",
    )
    parser.add_argument(
        "--list-years",
        action="store_true",
        help="List available years in the archive",
    )

    args = parser.parse_args()

    # Initialize
    repo_root = Path(__file__).parent.parent
    queue = QueueManager(repo_root / "queue" / "captures.db")

    try:
        processor = TwitterArchiveProcessor(args.archive_path, queue)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Handle --stats
    if args.stats or args.list_years:
        stats = processor.get_stats()
        print("\n" + "=" * 50)
        print("Twitter Archive Statistics")
        print("=" * 50)
        print(f"Total tweets:  {stats['total_tweets']}")
        print(f"Earliest:      {stats['earliest']}")
        print(f"Latest:        {stats['latest']}")
        print("\nTweets by year:")
        for year, count in stats['by_year'].items():
            print(f"  {year}: {count}")
        print("=" * 50)
        return

    # Parse date filters
    from_date = None
    to_date = None

    if args.year:
        from_date = datetime(args.year, 1, 1)
        to_date = datetime(args.year, 12, 31, 23, 59, 59)
    else:
        if args.from_date:
            from_date = parse_date(args.from_date)
        if args.to_date:
            to_date = parse_date(args.to_date)
            # Set to end of day
            to_date = to_date.replace(hour=23, minute=59, second=59)

    # Show what we're doing
    print("\n" + "=" * 50)
    print("Twitter Archive Import")
    print("=" * 50)
    print(f"Archive:    {args.archive_path}")
    if from_date:
        print(f"From:       {from_date.strftime('%Y-%m-%d')}")
    if to_date:
        print(f"To:         {to_date.strftime('%Y-%m-%d')}")
    if args.dry_run:
        print("Mode:       DRY RUN (no changes)")
    print("=" * 50)

    # Process
    stats = processor.process(
        from_date=from_date,
        to_date=to_date,
        dry_run=args.dry_run,
    )

    # Show results
    print("\nResults:")
    print(f"  Total in range:  {stats['total']}")
    print(f"  Added to queue:  {stats['added']}")
    print(f"  Failed:          {stats['failed']}")

    if not args.dry_run and stats['added'] > 0:
        print("\nNext steps:")
        print("  python scripts/processor.py   # Process the queue")


if __name__ == "__main__":
    main()

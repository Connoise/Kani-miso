"""
Twitter Fetcher for Second Brain
Fetches user tweets from Twitter/X API v2.
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

import sys
sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

logger = setup_logger(__name__)


class TwitterFetcher:
    """Fetches tweets from Twitter/X API v2."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, bearer_token: str, user_id: str):
        """
        Initialize Twitter fetcher.

        Args:
            bearer_token: Twitter API Bearer token
            user_id: Twitter user ID to fetch tweets from
        """
        self.bearer_token = bearer_token
        self.user_id = user_id
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "SecondBrainBot/1.0"
        }
        logger.info(f"Twitter fetcher initialized for user ID: {user_id}")

    def get_user_tweets(
        self,
        since_id: Optional[str] = None,
        max_results: int = 10,
        include_replies: bool = True,
        include_retweets: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent tweets from the configured user.

        Args:
            since_id: Only return tweets newer than this ID
            max_results: Maximum number of tweets to return (5-100)
            include_replies: Include reply tweets
            include_retweets: Include retweets

        Returns:
            List of tweet dictionaries
        """
        url = f"{self.BASE_URL}/users/{self.user_id}/tweets"

        # Request tweet fields and media expansions
        params = {
            "max_results": min(max(max_results, 5), 100),
            "tweet.fields": "created_at,text,attachments,referenced_tweets,entities",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url,type,alt_text",
        }

        if since_id:
            params["since_id"] = since_id

        # Exclude retweets if not wanted
        exclude = []
        if not include_replies:
            exclude.append("replies")
        if not include_retweets:
            exclude.append("retweets")
        if exclude:
            params["exclude"] = ",".join(exclude)

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            tweets = data.get("data", [])
            includes = data.get("includes", {})
            media_map = {}

            # Build media lookup map
            for media in includes.get("media", []):
                media_key = media.get("media_key")
                if media_key:
                    media_map[media_key] = media

            # Attach media info to tweets
            for tweet in tweets:
                attachments = tweet.get("attachments", {})
                media_keys = attachments.get("media_keys", [])
                tweet["media"] = [media_map.get(key) for key in media_keys if key in media_map]

            logger.info(f"Fetched {len(tweets)} tweets")
            return tweets

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("Twitter API rate limit exceeded. Please wait and try again.")
            elif e.response.status_code == 401:
                logger.error("Twitter API authentication failed. Check your bearer token.")
            elif e.response.status_code == 403:
                logger.error("Twitter API access forbidden. Check your API permissions.")
            else:
                logger.error(f"Twitter API HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch tweets: {e}")
            return []

    def get_user_id_by_username(self, username: str) -> Optional[str]:
        """
        Look up a user ID by username.

        Args:
            username: Twitter username (without @)

        Returns:
            User ID string or None if not found
        """
        url = f"{self.BASE_URL}/users/by/username/{username}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            user_id = data.get("data", {}).get("id")
            if user_id:
                logger.info(f"Found user ID for @{username}: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Failed to look up user @{username}: {e}")
            return None


def main():
    """Test the Twitter fetcher."""
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    user_id = os.getenv("TWITTER_USER_ID")

    if not bearer_token:
        logger.error("TWITTER_BEARER_TOKEN not found in config/.env")
        return

    if not user_id:
        # Try to look up by username
        username = os.getenv("TWITTER_USERNAME")
        if username:
            fetcher = TwitterFetcher(bearer_token, "")
            user_id = fetcher.get_user_id_by_username(username)
            if user_id:
                logger.info(f"Add this to your .env: TWITTER_USER_ID={user_id}")
        if not user_id:
            logger.error("TWITTER_USER_ID not found. Set it in config/.env or provide TWITTER_USERNAME")
            return

    fetcher = TwitterFetcher(bearer_token, user_id)
    tweets = fetcher.get_user_tweets(max_results=5)

    for tweet in tweets:
        print(f"\n--- Tweet {tweet['id']} ---")
        print(f"Created: {tweet.get('created_at')}")
        print(f"Text: {tweet.get('text')}")
        if tweet.get("media"):
            print(f"Media: {len(tweet['media'])} attachments")
            for m in tweet["media"]:
                print(f"  - {m.get('type')}: {m.get('url') or m.get('preview_image_url')}")


if __name__ == "__main__":
    main()

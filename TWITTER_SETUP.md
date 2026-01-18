# Twitter Integration Setup

This guide explains how to set up automatic forwarding of your tweets to the Second Brain system via Telegram.

## How It Works

```
Your Tweet → Twitter API → tweet_to_telegram.py → Telegram Chat → telegram_bot.py → Queue → Processing → /tweets/ folder
```

1. You post a tweet on Twitter/X
2. The `tweet_to_telegram.py` script fetches your recent tweets
3. Tweets are formatted and sent to your Telegram chat
4. The existing Telegram bot receives them and adds them to the queue
5. When you run the processor, tweets are processed like any other capture
6. Processed tweets are saved to the `/tweets/` folder

## Prerequisites

- Working Telegram bot setup (see TELEGRAM_SETUP.md)
- Twitter/X Developer account with API access

## Step 1: Create a Twitter Developer Account

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Sign up for a developer account (free tier works)
3. Create a new Project and App
4. Note: You need at least "Read" permissions for tweets

## Step 2: Get Your Bearer Token

1. In the Twitter Developer Portal, go to your App
2. Navigate to "Keys and tokens"
3. Generate a Bearer Token (under "Authentication Tokens")
4. Copy the Bearer Token

## Step 3: Find Your Twitter User ID

Your Twitter user ID is a numeric ID, not your username.

**Option A: Use the included tool**
```bash
python scripts/tweet_to_telegram.py --lookup-user YOUR_USERNAME
```

**Option B: Use Twitter's API manually**
Visit: https://tweeterid.com/ and enter your username

## Step 4: Configure Environment Variables

Add these to your `config/.env` file:

```bash
# Twitter/X API Configuration
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_USER_ID=your_numeric_user_id_here
```

## Step 5: Test the Connection

```bash
# Test fetching tweets (doesn't forward yet)
python scripts/twitter_fetcher.py
```

You should see your recent tweets listed.

## Usage

### Manual Sync (Recommended)

Run this before processing your Telegram queue:

```bash
# Sync recent tweets to Telegram
python scripts/tweet_to_telegram.py --sync

# Then process everything
python scripts/processor.py
```

### Command Line Options

```bash
# Show statistics
python scripts/tweet_to_telegram.py --stats

# Sync with options
python scripts/tweet_to_telegram.py --sync --max-tweets 20

# Exclude replies
python scripts/tweet_to_telegram.py --sync --no-replies

# Exclude retweets
python scripts/tweet_to_telegram.py --sync --no-retweets

# Exclude both
python scripts/tweet_to_telegram.py --sync --no-replies --no-retweets

# Look up a user ID
python scripts/tweet_to_telegram.py --lookup-user someusername
```

### Typical Workflow

```bash
# 1. Sync your tweets to Telegram
python scripts/tweet_to_telegram.py --sync

# 2. Process all queued captures (including tweets)
python scripts/processor.py

# 3. Review and commit
git status
git add .
git commit -m "process: batch with tweets"
```

## Configuration

Edit `config/config.yaml` to customize Twitter behavior:

```yaml
twitter:
  enabled: true
  default_type: "Tweet"      # Note type for tweets
  include_replies: true      # Include reply tweets
  include_retweets: true     # Include retweets
  max_tweets_per_sync: 10    # Max tweets per sync
```

## Tweet Message Format

Tweets are formatted as:

```
Tweet: self-published tweet
Surface: twitter
Context: Posted on Twitter/X at 2026-01-18T12:00:00Z
Trigger: self-published tweet (ID: 1234567890)

Your tweet text here...

Attachments:
- [photo] https://pbs.twimg.com/media/...
```

## Where Tweets Are Saved

Processed tweets are saved to:
- **Repository:** `/tweets/YYYY-MM-DD--slug.md`
- **Or notes_root:** If configured, saves to your Obsidian notes folder

## Tracking & Duplicates

The system tracks forwarded tweets in `queue/tweet_tracker.db`:
- Each tweet is only forwarded once
- The last processed tweet ID is stored for efficient fetching
- Run `--stats` to see forwarding history

## Troubleshooting

### "TWITTER_BEARER_TOKEN not found"
Add your Bearer Token to `config/.env`

### "TWITTER_USER_ID not found"
Look up your user ID:
```bash
python scripts/tweet_to_telegram.py --lookup-user YOUR_USERNAME
```

### "Twitter API rate limit exceeded"
The free tier has rate limits. Wait 15 minutes and try again.

### "Twitter API authentication failed"
- Check your Bearer Token is correct
- Ensure your app has "Read" permissions
- Regenerate the token if needed

### "Twitter API access forbidden"
- Your developer account may need approval
- Check your app's permissions in the Developer Portal

### Tweets not appearing in Telegram
1. Check Telegram bot is running: `python scripts/telegram_bot.py`
2. Verify TELEGRAM_CHAT_ID is correct
3. Check the tweet_tracker.db for forwarding status

### Images not showing
Twitter API requires elevated access for some media. Photos should work with basic access, but videos may require higher tier access.

## Security Notes

- Never commit your `.env` file
- Bearer tokens should be kept secret
- The tracker database stores tweet IDs and text snippets locally
- Consider rate limits when syncing frequently

## API Tier Limits (Free)

- 1,500 tweet reads per month (50/day approx)
- 10 requests per 15 minutes
- For more, consider Twitter API Pro ($100/month)

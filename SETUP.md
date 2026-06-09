# Kani-miso - Automation Setup Guide

This guide will help you set up the automation system for processing Telegram captures.

## Prerequisites

- **Python 3.11+** installed
- **Git** installed and configured
- **Anthropic API key** (for Claude)
- **Telegram Bot Token** (optional for Phase 2)

---

## Phase 1: Setup Foundation (Manual Processing)

### Step 1: Install Python Dependencies

```bash
cd "C:\Users\gilli\Desktop\Connor Work\Github\Kani-miso"
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy config\.env.example config\.env
   ```

2. Edit `config/.env` and add your API keys:
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   ```

#### Getting an Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new key
5. Copy it to `config/.env`

**Note:** Claude API is pay-as-you-go. Typical costs: ~$0.003 per note processed.

### Step 3: Verify Setup

Test that everything works:

```bash
python scripts/processor.py --stats
```

You should see:
```
Queue Statistics
================
Pending: 0
Total: 0
```

---

## Phase 1 Usage: Manual Capture Processing

### Adding Captures Manually

Until the Telegram bot is set up, you can add captures to the queue manually:

**Interactive mode:**
```bash
python scripts/test_add_capture.py
```

**Quick mode:**
```bash
python scripts/test_add_capture.py "This is a quick thought"
```

### Processing Captures

Once you've added captures to the queue:

```bash
python scripts/processor.py
```

This will:
1. Fetch pending captures from the queue
2. Process each with Claude API
3. Generate markdown files in appropriate folders
4. Create a Git commit (but NOT push)
5. Mark captures as completed

### Review and Push

After processing:

1. Review the created files in `/notes`, `/reflections`, or `/sources`
2. Check the Git commit:
   ```bash
   git log -1
   git show
   ```
3. If satisfied, push manually:
   ```bash
   git push
   ```

---

## Phase 2: Telegram Bot Setup (Future)

### Prerequisites

- Telegram account
- Bot created via @BotFather

### Steps

1. **Create Telegram Bot:**
   - Open Telegram and message @BotFather
   - Send `/newbot`
   - Follow prompts to name your bot
   - Copy the bot token

2. **Get Your Chat ID:**
   - Message your new bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat.id` in the JSON response

3. **Configure `.env`:**
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

4. **Run Telegram Bot:**
   ```bash
   python scripts/telegram_bot.py
   ```

   (Bot script to be created in next phase)

---

## Common Tasks

### View Queue Status

```bash
python scripts/processor.py --stats
```

### Process Limited Batch

```bash
python scripts/processor.py --batch-size 10
```

### View Logs

```bash
tail -f logs/processor.log
```

Or on Windows:
```bash
type logs\processor.log
```

### Reset Stuck Processing Items

If the processor crashed, some items might be stuck in "processing" status.
Next run will automatically reset them to "pending".

---

## Troubleshooting

### "No module named 'anthropic'"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"

1. Ensure `config/.env` exists (copy from `config/.env.example`)
2. Add your actual API key to the file
3. Make sure there are no extra spaces

### "Not a valid Git repository"

Make sure you're running commands from the repository root:
```bash
cd "C:\Users\gilli\Desktop\Connor Work\Github\Kani-miso"
```

### Processing Fails with API Error

Check:
1. API key is correct in `config/.env`
2. You have available API credits
3. Internet connection is working

---

## Configuration

Edit `config/config.yaml` to customize:

- **Batch size:** How many captures to process at once
- **Claude model:** Trade off cost vs quality
- **Auto-commit:** Whether to create Git commits automatically
- **Logging level:** DEBUG for more detail, ERROR for less

---

## Next Steps

Once Phase 1 is working:

1. Set up Telegram bot for automatic capture
2. Add scheduled processing (runs automatically when PC boots)
3. Enhance with source document processing (PDFs)
4. Add hub suggestion improvements

---

## Security Notes

- **Never commit `config/.env`** - it's gitignored for security
- Keep your API keys secret
- The queue database (`queue/captures.db`) is local and gitignored
- Logs may contain capture content - keep them private

# Telegram Bot Setup Guide

This guide will help you set up the Telegram bot for automatic capture from your phone.

---

## Step 1: Create a Telegram Bot

1. **Open Telegram** on your phone or desktop

2. **Search for @BotFather** (the official bot for creating bots)

3. **Send `/newbot`** to BotFather

4. **Choose a name** for your bot (e.g., "My Second Brain")

5. **Choose a username** for your bot (must end in 'bot', e.g., "mysecondbrainbot")

6. **Copy the API token** that BotFather gives you
   - It looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - ⚠️ Keep this secret!

---

## Step 2: Get Your Chat ID

There are two options for where to send captures:

### Option A: Private Chat with Bot (Recommended)

1. **Find your bot** in Telegram (search for the username you created)
2. **Send `/start`** to your bot
3. **The bot will reply with your chat ID** (a number)
4. Copy this chat ID

### Option B: Private Group/Channel

1. **Create a private group** or use an existing one
2. **Add your bot** to the group (as admin if needed)
3. **Send a test message** to the group
4. **Get the chat ID** using this method:
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual token
   - Find the `"chat":{"id":` field in the JSON
   - Use this negative number as your chat ID

---

## Step 3: Configure Environment Variables

1. **Edit `config/.env`**

2. **Add your Telegram credentials:**
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

3. **Save the file**

---

## Step 4: Test the Bot

1. **Start the bot:**
   ```bash
   python scripts/telegram_bot.py
   ```

2. **Send a test message** to your bot on Telegram:
   ```
   Thought: Testing the telegram bot integration
   Mood: excited
   ```

3. **You should see:**
   - Bot replies with ✅ confirmation
   - Logs show "Added capture X to queue"

4. **Stop the bot** with `Ctrl+C`

5. **Process the capture:**
   ```bash
   python scripts/processor.py
   ```

6. **Check the result** in your `/notes` folder!

---

## Step 5: Running the Bot Continuously

### Option A: Manual (Simple)

Just run when you want to capture:
```bash
python scripts/telegram_bot.py
```

Leave it running while you're working. Stop with `Ctrl+C` when done.

### Option B: Background Process (Windows)

Create a batch file to run the bot in the background:

**File: `run_telegram_bot.bat`**
```batch
@echo off
cd /d "C:\Users\gilli\Desktop\Connor Work\Github\Second-Brian"
python scripts/telegram_bot.py
pause
```

Double-click this file to start the bot.

### Option C: Startup Task (Windows)

To run automatically when your PC starts:

1. **Press Win+R**, type `shell:startup`, press Enter
2. **Create a shortcut** to your `run_telegram_bot.bat` file
3. **Bot will start automatically** on PC boot

### Option D: Always-On Server (Advanced)

If you want 24/7 capture without your PC on:
- Deploy to a cloud service (Heroku, Railway, fly.io, etc.)
- Or use a Raspberry Pi at home
- (Instructions for this are beyond scope, but the bot code is ready)

---

## Message Format

### Basic Capture
Just send text:
```
Testing the capture system from my phone
```

### With Type
```
Reflection: I noticed something interesting today
```

### With Metadata
```
Thought: early internet felt more intimate
Mood: nostalgic
Trigger: reading old forum posts
Surface: mobile
```

### Types Available
- `Thought:` - General thoughts (default)
- `Reflection:` - Personal, emotional notes
- `Question:` - Questions to explore
- `Source:` - External materials
- `Quote:` - Quotes to remember
- `Idea:` - Ideas for later
- `Log:` - Activity/event logs

### Context Fields
- `Surface:` mobile | desktop-work | desktop-home
- `Mood:` any text (e.g., curious, tired, excited)
- `Energy:` any text (e.g., high, low, locked in)
- `Confidence:` any text (e.g., certain, unsure, high af)
- `Trigger:` what prompted the capture
- `Context:` situational details

---

## Bot Commands

Send these to your bot:

- `/start` - Show welcome message and your chat ID
- `/stats` - View queue statistics
- `/help` - Show format guide

---

## Workflow with Telegram Bot

### Daily Use

1. **Bot runs in background** (or always-on server)

2. **Send messages to bot** throughout the day from your phone:
   ```
   Reflection: interesting conversation about AI safety
   Mood: thoughtful
   Trigger: lunch discussion
   ```

3. **Bot confirms** with ✅ message

4. **When ready to process** (end of day, etc.):
   ```bash
   python scripts/processor.py
   ```

5. **Review and push:**
   ```bash
   git show
   git push
   ```

---

## Troubleshooting

### Bot doesn't respond
- Check bot token is correct in `config/.env`
- Check bot is running (`python scripts/telegram_bot.py`)
- Try `/start` command

### "Unauthorized chat" in logs
- Check chat ID is correct in `config/.env`
- Make sure you're sending from the right Telegram account

### Messages captured but not processed
- Captures go to queue first
- Run `python scripts/processor.py` to process them
- Or set up automatic processing (see SETUP.md)

### Bot crashes
- Check logs in `logs/processor.log`
- Restart with `python scripts/telegram_bot.py`

---

## Next Steps

Once Telegram bot is working:

1. **Set up automatic processing**
   - Schedule processor to run periodically
   - Or run on PC startup

2. **Test from phone**
   - Capture while away from computer
   - Process when you get home

3. **Customize format**
   - Develop your own shorthand
   - Use consistent mood/energy terms
   - Build your personal capture style

---

## Security Notes

- ⚠️ **Never share your bot token** - it's like a password
- ⚠️ **Keep `config/.env` gitignored** - don't commit it
- The bot only responds to your chat ID (if configured)
- Messages are stored locally in your queue database
- No data leaves your computer except to Anthropic API for processing

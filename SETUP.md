# Kani-miso — Setup Guide (Linux)

Setting up the engine on a Linux machine (reference host: Bentendo). The engine
repo and the Obsidian vault are separate: clone the repo anywhere; the vault path
is configured, not assumed.

## Prerequisites

- Python 3.11+
- Git
- An Anthropic API key (https://console.anthropic.com/ → Settings → API Keys)
- A Telegram bot (optional, for mobile capture)

## 1. Install

```bash
git clone <repo-url> && cd Kani-miso
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure

**Secrets** — copy the template and fill it in:

```bash
cp config/.env.example config/.env
```

```ini
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=...        # from @BotFather (step 4)
TELEGRAM_CHAT_ID=...          # your chat ID — REQUIRED; the bot must never run open
```

**Vault path** — edit `config/config.yaml`:

```yaml
notes_root: "/home/<you>/path/to/vault"   # your Obsidian vault; never commit a personal path
```

## 3. Verify

```bash
python scripts/check_setup.py
python scripts/processor.py --stats     # queue reachable, config parses
```

Smoke-test the pipeline end to end:

```bash
python scripts/test_add_capture.py "Setup smoke test"
python scripts/processor.py
# then inspect the new file under <vault>/notes/ and review the commit
```

## 4. Telegram bot (mobile capture)

1. In Telegram, message **@BotFather** → `/newbot` → copy the token into
   `config/.env`.
2. Send any message to your new bot, then visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy
   `message.chat.id` into `TELEGRAM_CHAT_ID`.
3. Run the bot + processor loop:

```bash
python scripts/run.py                # bot + auto-process every 5 min
python scripts/run.py --interval 10  # or every 10 min
python scripts/telegram_bot.py       # bot only; process separately
```

Message conventions (all optional): see `specs/02-capture.md`.

## 5. X / Twitter archive import (primary capture source)

Request your archive at https://twitter.com/settings/download_your_data, extract
the zip, then:

```bash
python scripts/twitter_archive_processor.py /path/to/twitter-archive --year 2025
python scripts/processor.py          # process the queued tweets in batches
```

Useful flags: `--from YYYY-MM-DD --to YYYY-MM-DD`, plus `--stats` on the processor.

## 6. Snapshot analysis

See `specs/04-analysis.md`. Run the cost estimate first; outputs land in
`<vault>/analysis/<run-id>/`.

## Common tasks

```bash
python scripts/processor.py --stats        # queue status
python scripts/processor.py --batch-size 10
python scripts/reset_failed.py             # requeue failed captures
tail -f logs/processor.log
```

## Troubleshooting

- **`No module named anthropic`** — activate the venv, reinstall requirements.
- **`ANTHROPIC_API_KEY not found`** — key goes in `config/.env`, not the shell;
  no extra spaces.
- **Bot logs "Listening to ALL chats"** — `TELEGRAM_CHAT_ID` is unset. Stop and
  set it; the bot must never run unrestricted (see `specs/05-ai-and-ops.md`).
- **Processing fails with API error** — check key validity and account credit;
  failed captures stay queued and are retryable.
- **Stuck `processing` items** — the processor resets them on next startup.

## Security notes

- Never commit `config/.env` (gitignored) or a personal `notes_root` path.
- The queue DB (`queue/`) and logs (`logs/`) are local state, gitignored; logs
  may contain capture content — keep them private.

## Daily rhythm

1. Capture via Telegram / import an X archive batch.
2. `python scripts/processor.py` (or let `run.py` do it).
3. Review the commit(s), then push manually when satisfied. Nothing pushes
   automatically.

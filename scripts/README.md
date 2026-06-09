# Kani-miso Automation Scripts

This directory contains the automation system for processing Telegram captures into the Kani-miso archive.

## Architecture Overview

```
Telegram → Queue (SQLite) → Processor → Markdown Files → Git Commit
```

## Core Scripts

### `processor.py` - Main Orchestrator
The primary script that processes queued captures.

**Usage:**
```bash
python scripts/processor.py              # Process all pending
python scripts/processor.py --stats      # Show queue stats
python scripts/processor.py --batch-size 10  # Process 10 items
```

**What it does:**
1. Fetches pending captures from queue
2. Processes each with Claude API using specs
3. Generates markdown files
4. Creates Git commit
5. Marks items as processed

### `queue_manager.py` - Queue Operations
Manages the SQLite database that stores unprocessed captures.

**Database:** `queue/captures.db`

**Provides:**
- Add captures
- Retrieve pending items
- Mark processed/failed
- Get statistics

### `test_add_capture.py` - Manual Capture Entry
Add captures to the queue manually (for testing or until Telegram bot is set up).

**Usage:**
```bash
python scripts/test_add_capture.py              # Interactive mode
python scripts/test_add_capture.py "Quick thought"  # Quick add
```

### `check_setup.py` - Setup Verification
Verifies that all requirements are met.

**Usage:**
```bash
python scripts/check_setup.py
```

Checks:
- Python version
- Required packages
- Directory structure
- Configuration files
- Environment variables
- Git repository status

## Processors

### `processors/claude_client.py`
Handles communication with Anthropic's Claude API.

- Loads prompt templates from `/specs`
- Formats capture data
- Calls API
- Returns processed markdown

### `processors/file_writer.py`
Generates and writes markdown files.

- Determines destination folder
- Generates filenames (`YYYY-MM-DD--slug.md`)
- Extracts titles from markdown
- Handles file conflicts
- Writes Obsidian-compatible markdown

### `processors/git_manager.py`
Manages Git operations safely.

- Checks repository state
- Stages files
- Creates commits with meaningful messages
- Handles push operations
- Provides commit summaries

## Utilities

### `utils/logger.py`
Consistent logging across all modules with color-coded console output.

### `utils/slugify.py`
Filename generation and slugification.

## Configuration

- **Config:** `config/config.yaml` (tracked in Git)
- **Secrets:** `config/.env` (gitignored)

## Data Storage

- **Queue Database:** `queue/captures.db` (gitignored)
- **Logs:** `logs/processor.log` (gitignored)
- **Archive:** Markdown files in `/notes`, `/reflections`, `/sources`, etc. (tracked)

## Workflow

### Phase 1 (Current): Manual Trigger

1. Add capture manually:
   ```bash
   python scripts/test_add_capture.py
   ```

2. Process when ready:
   ```bash
   python scripts/processor.py
   ```

3. Review and push:
   ```bash
   git log -1
   git show
   git push
   ```

### Phase 2 (Future): Telegram Bot

1. Telegram bot receives messages
2. Bot adds to queue automatically
3. Processor runs on schedule or manually
4. Files created and committed automatically

## Safety Features

- **Original text preserved:** Raw capture never modified
- **No auto-push:** Commits created but manual push required for review
- **Error handling:** Failed items marked, can be retried
- **Stuck item recovery:** Automatic reset of "processing" items on restart
- **Specs-governed:** All processing follows rules in `/specs`

## Error Handling

- Failed captures remain in queue with status "failed"
- Error messages logged to `logs/processor.log`
- Can be retried by resetting status manually in database
- Partial batches are acceptable (repo remains consistent)

## Future Enhancements

- Telegram bot integration
- Scheduled processing
- PDF/source document handling
- Enhanced hub suggestion
- Retry logic for failed items
- Processing status dashboard

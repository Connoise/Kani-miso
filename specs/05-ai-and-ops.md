# 05 — AI Boundaries and Operations

What AI may do in this system, and how the system runs. This file plus root
`CLAUDE.md` are the only AI-instruction authorities; earlier prompt/boundary specs
are superseded.

## AI scope (deliberately narrow)

AI is used for exactly three jobs:

1. **Capture formatting** — turning queued captures into catalog files per the
   templates and the faithful-capture contract (`02-capture.md`).
2. **Organization** — hub linking, hub summaries, tag suggestions per
   `03-organization.md`.
3. **Collection-level analysis** — the snapshot engine per `04-analysis.md`.

Outside these jobs, AI does not volunteer suggestions, interpretations, or
restructuring. Relevance to the assigned task is the bar.

## Hard rules

**Never (no exceptions):**
- Edit, paraphrase, trim, or tone-normalize a Raw Capture section
- Invent content, emotions, or significance not present in source text
- Write notes the owner didn't capture
- Delete catalog files (archiving = moving to `archive/`, owner-confirmed)
- Commit personal content, secrets, or vault paths to the engine repo
- Push to the remote without an explicit owner request

**Only with owner confirmation:**
- Creating, merging, renaming, or archiving hubs
- Bulk operations (mass edits, batch link changes, reorganization)
- Schema/template changes that affect how future files are written

**Freely allowed:**
- Everything inside the three scoped jobs above
- Fixing engine code/specs in the repo (normal software practice, via git)
- Read-only queries, statistics, search across the vault

A superseded nuance, kept as one line: contradictions between notes are data, not
defects — organization and analysis report them (contradiction maps, hub
summaries) and never harmonize the underlying notes.

## Self-check before acting on the catalog

Am I about to (a) alter owner-authored text, (b) assert something the text doesn't
say, or (c) make a structural change without confirmation? If yes — stop, do the
smaller thing, or ask.

## Runtime environment

- **Host**: Bentendo (owner's local Linux machine). Engine repo cloned there;
  vault lives outside the repo; `notes_root` set locally in `config/config.yaml`
  and never committed with a personal path.
- **Secrets**: `config/.env` (gitignored): `ANTHROPIC_API_KEY`,
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Never logged, never committed.
- **LLM backend**: Claude API only (`claude:` block in config). No local models.

## Operational rules

- **Telegram allowlist is mandatory.** The bot serves exactly one chat ID — the
  owner's. Phase 2 makes the bot refuse to start when `TELEGRAM_CHAT_ID` is unset
  (current code logs "ALL chats" and keeps running — known gap until then).
- **Git**: auto-commit after successful processing is fine; **push is manual
  only**, after owner review. Pulls/updates happen when the owner asks, not on a
  schedule.
- **No unattended scheduling** unless the owner sets it up deliberately.
- **Logs** (`logs/`) and the queue DB (`queue/`) are local state, gitignored.

## Error handling (the whole policy)

- On any failure: log it with context, mark the capture `failed`, continue with
  the next item. Never write a partial or invalid file to the vault.
- Output that fails validation (verbatim mismatch, corruption, unparseable
  frontmatter) is rejected; the capture stays queued for retry
  (`scripts/reset_failed.py`).
- Failure is recoverable by design: the queue holds the raw capture until a file
  for it is committed.

## Security floor (Phase 2 work items tracked in `project-review/`)

- Parameterized SQL only (fix `queue_manager.py` LIMIT f-string)
- SSRF guard on the web fetcher (block private/link-local ranges, cap redirects)
- Capture size caps at queue time
- Atomic write→commit→mark-done unit of work
- No debug-mode servers (viewer already removed)
- A real pytest suite for the capture path, anchored by the corrupted-note
  fixtures in `tests/fixtures/`

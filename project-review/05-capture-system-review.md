# Capture System Review — Pre-Phase 2 Baseline

> **Created:** 2026-06-12
> **Purpose:** Verified, code-grounded description of what the capture system
> does **today**, so Phase 2 hardening changes against an agreed baseline.
> Every claim below was checked against the code on this branch, not the specs.

## 1. End-to-end flow

```
                       ┌──────────────────────────────────────────────┐
 Telegram (long-poll)  │                SQLite queue                  │
 X archive import   ──►│  queue/captures.db                           │──► processor.py batch
 Manual script         │  status: pending → processing → done|failed  │
                       └──────────────────────────────────────────────┘
                                                                          │
              ┌───────────────────────────────────────────────────────────┘
              ▼
   per capture: route by content → Claude API (template as system prompt)
              → file_writer (fence-strip → title → folder → filename → write)
              → queue.mark_completed
   per batch:  one git commit of all written files (push always manual)
```

## 2. Capture surfaces — verified capabilities

### 2.1 Telegram bot (`telegram_bot.py`)

- **Transport:** long-polls `getUpdates` with the bot token; `last_update_id`
  persisted in the queue DB (`bot_state` table) so restarts don't replay or
  drop messages.
- **Auth:** if `TELEGRAM_CHAT_ID` is set, only that chat is served. **If unset,
  the bot serves ALL chats** (`telegram_bot.py:88`) — the known critical gap;
  Phase 2 makes the variable mandatory.
- **Text parsing** (`parse_message`):
  - First-line prefix → type (case-insensitive): `Thought:` `Reflection:`
    `Question:` `Source:` `Quote:` `Idea:` `Log:` `Tweet:`. No prefix →
    `Thought`.
  - Context keys on any line (case-insensitive): `Surface:` `Mood:` `Energy:`
    `Confidence:` `Trigger:` `Context:` — extracted into queue columns.
  - Everything else (including any `Hubs: [[..]]` line — **not parsed**) stays
    in the body and is visible to Claude.
  - No multi-message threads (the old spec's `Thread:` marker was never built).
- **Images:** photos download to `<vault>/images/YYYY/MM/DD/`; an image
  without text is held in `pending_images` and attached to the **next text
  message** from that chat (cap: `images.max_pending_images`, default 10).
  No download retry; no file-type validation (Phase 2 robustness items).
- **Documents (PDFs):** stored via the document manager; capture queued with
  `document_paths` and processed through the PDF branch.
- **Commands:** `/start`, `/help`, `/stats`, `/pending`.
- **Duplicate protection:** `telegram_message_id` is `UNIQUE` in the queue —
  the same message can't be queued twice.

### 2.2 X archive import (`twitter_archive_processor.py`) — primary source

- Input: an extracted X data export; reads `data/tweets.js` (falls back to
  `data/tweet.js`, `tweet.js`, `tweets.js`).
- Filters: `--year` or `--from`/`--to`; per-tweet dates parsed from Twitter's
  `created_at` format.
- Each tweet is queued with: `type=Tweet`, `surface=twitter-archive`,
  `captured_at=<original tweet date>` (so file dates match tweet dates),
  `trigger="Twitter archive import (ID: <id>)"`, media/URLs preserved — the
  body is the full tweet text plus a `Links:` list (expanded URLs) and a
  `Media:` list (https media URLs); media files themselves are not downloaded.
- **No tweet-level dedup**: the tweet ID lives only inside the `trigger` text;
  there is no UNIQUE constraint on it. **Re-importing an overlapping range
  (e.g., a fresh full archive export) will queue duplicates.** Phase 2 item.

### 2.3 Manual (`test_add_capture.py`)

Interactive or one-shot CLI insert into the queue. Same fields as Telegram.

## 3. Queue (`queue_manager.py`)

- SQLite at `queue/captures.db` (gitignored). Tables: `captures`,
  `pending_images`, `bot_state`.
- Capture columns: type, body (NOT NULL), captured_at, surface, mood, energy,
  confidence, trigger, context, attachments (JSON), image_paths (JSON),
  document_paths (JSON), status, error_message, output_file.
- Statuses: `pending → processing → done | failed`. Items stuck in
  `processing` (crash) are reset to `pending` on next processor start;
  `reset_failed.py` requeues `failed` items.
- Batch ordering: Telegram/image captures first, tweets last, else FIFO by
  `captured_at`.
- Known defect: `LIMIT {limit}` built by f-string (`queue_manager.py:209`) —
  not attacker-reachable today, parameterized in Phase 2.
- No body-size cap at queue time (Phase 2 item).

## 4. Processing (`processor.py` + `claude_client.py`)

Routing is content-based, in `process_batch`, in this order:

| Condition | Branch | Prompt template (system prompt) |
|---|---|---|
| `document_paths` present | PDF: extract text (pypdf, PyPDF2 fallback; >100 pages truncated) → Claude | `specs/pdf-processing-prompt.md` |
| `image_paths` present | Claude vision with base64 images + Obsidian embed paths | `specs/telegram-processing-prompt.md` + image instructions |
| `type == 'Source'` | Web fetcher (10 MB cap, 30 s timeout, scheme check; **no SSRF/IP guard, no redirect cap**) → Claude | `specs/source-processing-prompt.md` |
| otherwise | plain text → Claude | `specs/telegram-processing-prompt.md` |

- Claude call: model/max_tokens/temperature from `config.yaml` `claude:` block;
  template is the **system prompt**, capture fields formatted into the user
  message.
- Per-capture failure → `failed` + error message, batch continues. Nothing is
  written for failed items.

## 5. Writing and committing (`file_writer.py`, `git_manager.py`)

- Cleanup: `strip_code_block_wrapper()` removes a leading/trailing
  ``` / ```markdown fence. **That is the only output check in the live path**
  (see §6).
- Title from first `# heading`; filename `YYYY-MM-DD--slug.md` (capture date);
  collision → `-HHMMSS` suffix.
- Folder routing by type: Thought/Question/Log/Idea/Quote/Image → `notes/`;
  **Reflection → `reflections/`** (pre-pivot behavior; new spec folds it into
  `notes/` — Phase 2 code change); Source → `sources/`; Tweet → `tweets/`;
  unknown → `inbox/`.
- Write: plain UTF-8 `open().write()` — not atomic (no temp-file rename).
- Commit: **one batch commit after the whole batch**; each capture was already
  marked `done` as its file was written. Consequences if the process dies or
  commit fails mid-sequence: files on disk + queue `done` + no commit. Phase 2
  reworks this into a per-capture atomic unit (write → commit → mark done).
- Push: never automatic. `auto_push: true` only logs a warning telling you to
  push manually.

## 6. Safety nets: present vs. missing

**Present and live:**
- Telegram message dedup (UNIQUE id), update-id resume, stuck-item reset,
  failed-item requeue, fence stripping, conflict-proof filenames, manual push.

**Present but NOT wired (the key discovery of this review):**
- `output_validator.py` — frontmatter check + **verbatim raw-capture check**
  (whitespace-normalized, case-insensitive) with strict/lenient/off modes and
  per-kind preservation sections (telegram/image/source/pdf). It was only ever
  called by the deleted Ollama hybrid client. **The Claude path has never run
  it.** This is precisely how the January corrupted notes reached the vault.
  → Phase 2 wires it into `processor.py` for every branch (correcting the
  Phase 0 audit, which assumed it was active), and extends it to reject
  `&nbsp;`/escaped-markdown corruption explicitly, with the
  `tests/fixtures/corrupted-notes/` files as regression cases.
- `capture_router.py` — pure local-vs-Claude routing; orphaned and meaningless
  in a Claude-only system. → **Delete in Phase 2** (correcting the Phase 0
  audit's KEEP, which misread its purpose; the real per-content routing lives
  in `processor.py`).

**Missing (Phase 2 scope):**
1. Output validation on the live path (above) — *the* fidelity fix
2. Mandatory `TELEGRAM_CHAT_ID` (refuse to start unset)
3. Tweet-ID dedup on archive import
4. Atomic per-capture unit of work (write → commit → mark done)
5. SSRF guard + redirect cap on web fetcher
6. Queue-time body size cap
7. Parameterized `LIMIT`
8. Reflection → `notes/` routing per new data model
9. Single `parse_message` implementation (`run.py` carries a near-duplicate of
   the bot's parser — drift risk)
10. Atomic file writes (temp + rename); timezone-aware timestamps
11. Image download retry + content-type validation

**Spec nits found while verifying (fix in Phase 2 commit):**
- `specs/02-capture.md` omits the `Idea:` prefix the bot accepts, and should
  state that `Hubs:` lines ride along in the body unparsed.

## 7. Proposed Phase 2 order (capture-correctness first)

1. Wire + extend the output validator; pytest suite against the corrupted-note
   fixtures (items 1) — **the "cataloged accurately" guarantee**
2. Mandatory allowlist (2) — the security gate
3. Atomic unit of work + atomic writes (4, 10)
4. Tweet dedup (3) — protects the primary corpus before the next big import
5. The rest (5–9, 11) + spec nits + delete `capture_router.py`

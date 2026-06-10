# 02 — Capture

How content gets into the catalog, faithfully.

## Pipeline

```
surface → SQLite queue (queue/captures.db) → Claude processing → validation
        → markdown file in vault → git commit (auto) → git push (manual only)
```

- Every capture is queued before processing; a processing failure leaves the
  capture in the queue (`pending`/`failed`), never lost. Reprocessing is safe.
- File write + queue update + git commit form one unit of work: a capture is not
  marked `done` until its file exists and is committed (Phase 2 hardening).
- Push is always manual (`git push` after owner review). No automation pushes.

## Surfaces

| Surface | Path in | Notes |
|---|---|---|
| **X archive import** | `scripts/twitter_archive_processor.py <archive-dir>` | Primary source. Parses `data/tweets.js`, supports `--year` / `--from` / `--to` filters, queues each tweet. |
| **Telegram bot** | `scripts/telegram_bot.py` / `scripts/run.py` | Text, images, documents, links. **Only processes messages from `TELEGRAM_CHAT_ID`** — the allowlist is mandatory (Phase 2 enforces refusal to start without it). |
| **Manual** | `scripts/test_add_capture.py` | Direct queue entry for testing. |

Surface is recorded as context; it has no effect on how content is treated.

## Telegram message conventions

Optional, low-friction. Unformatted messages are valid (`type` defaults to
`thought`, `capture_mode` to `quick`, `surface` to `mobile`).

- First-line prefix sets type: `Thought:` `Reflection:` `Question:` `Source:`
  `Quote:` `Log:`
- Optional context keys on their own lines: `Mood:` `Energy:` `Trigger:`
  `Context:` `Surface:`
- Link capture: `Source: <label>` then the URL on its own line, then optionally
  why it was saved. The web fetcher retrieves and converts the page.
- Attachments (images, PDFs): send with a one-line intent; the attachment and text
  are one capture unit. Images without text are held pending and attached to the
  next text message (up to `images.max_pending_images`).
- Pre-suggested hubs: `Hubs: [[Name]], [[Name]]` (optional).

## Processing rules (the faithful-capture contract)

These bind every processing path and every prompt template:

1. **Raw capture is reproduced verbatim** — same characters, no paraphrase, no
   sanitization, no tone normalization. The output validator rejects output whose
   Raw Capture section does not match the queued text.
2. **Interpretation asserts nothing not present in the source text.** No invented
   emotions, significance, or conclusions. Provisional language. If the text is
   ambiguous, the interpretation says so or stays silent — it never resolves
   ambiguity the text leaves open.
3. **Context fields record only what the owner stated.** Absent mood/trigger stays
   absent.
4. **Tags and hub suggestions are conservative and optional.** Broad canonical
   concepts only; omit rather than stretch. No hub suggestion for passing mentions.
5. **Output is raw markdown** starting with `---` on line 1 — no code-fence
   wrapping, no HTML entities, no escaped markdown. Output failing validation is
   rejected and the capture stays queued.

## Runtime prompt templates

The operative processing instructions are loaded from these files by
`claude_client.py` — **they are runtime artifacts; edit with the same care as code
and keep them consistent with this spec**:

- `specs/telegram-processing-prompt.md` — notes (text & image captures)
- `specs/source-processing-prompt.md` — webpages/articles
- `specs/pdf-processing-prompt.md` — PDF documents

Where these templates still carry old-philosophy language, the rules above win;
template updates are batched into Phase 2 alongside the test harness so behavior
changes are verified, not guessed.

## Per-type output contracts

- **Note** (thought/reflection/question): schema in `01-data-model.md` § Note.
- **Source** (webpage): `type: source`, `source_type: article`, URL + summary +
  owner's stated reason + key content.
- **PDF**: `type: source`, `source_type: pdf`, document info + summary + key
  points; original file stored via the document manager and linked.
- **Tweet**: note with verbatim tweet text; tweet date as file date.

## Failure handling

- LLM/API failure → capture marked `failed` with the error; retryable via
  `scripts/reset_failed.py`. Nothing is written on failure.
- Validation failure → same as above; invalid output is never written to the vault.
- Oversized/empty input → rejected at queue time with a logged reason (Phase 2
  adds an explicit size cap).
- Queue database is local state (gitignored); the vault and git history are the
  durable record.

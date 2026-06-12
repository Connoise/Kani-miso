# Phase 2 Log — Capture-Core Hardening

> **Executed:** 2026-06-12
> **Basis:** work list in `04-phase-1-log.md` + `05-capture-system-review.md`,
> plus the link-capture design in `06-link-capture-design.md`.

## Commits

1. **Mandatory allowlist + runner unification + LIMIT + dead router**
2. **Output validation on the live path + atomic unit of work + tweet dedup**
3. **Web fetcher hardening + link capture + git_manager import fix**

## What changed, against the §6 "missing" list of the capture review

| # | Item | Status |
|---|------|--------|
| 1 | Output validation on the live path | **Done** — wired into processor.py for all four branches; was orphaned. Strict by default; corruption check (`&nbsp;`/escaped markdown) added. |
| 2 | Mandatory `TELEGRAM_CHAT_ID` | **Done** — `TelegramBot.__init__` raises if unset; both entry points exit cleanly; "listen to all chats" path removed. |
| 3 | Tweet-ID dedup | **Done** — `tweet_id` column + partial unique index; importer pre-checks and reports skips. |
| 4 | Atomic unit of work | **Done** — `written` status between write and commit; `done` only after commit; crash recovery folds written-but-uncommitted notes into the next commit (or resets if the file vanished). |
| 5 | SSRF guard + redirect cap | **Done** — `_validate_target` blocks non-public addresses on the initial URL and each hop; manual redirect following with a hop cap. |
| 6 | Queue-time body size cap | **Done** — empty and >100k-char bodies rejected at enqueue. |
| 7 | Parameterized `LIMIT` | **Done.** |
| 8 | Reflection → `notes/` | **Done** — routing updated; `reflections/` no longer created (legacy folder still read by the analyzer). |
| 9 | Single `parse_message` | **Done** — `run.py` rewritten as composition over `TelegramBot`; its duplicate parser (which silently dropped photos/documents) is gone. |
| 10 | Atomic file writes; tz-aware timestamps | **Partial** — atomic temp-file+rename done. Timezone-aware timestamps deferred (low risk; single host). |
| 11 | Image download retry + content-type validation | **Deferred** to a follow-up; not a fidelity blocker. |

## Link capture (new capability)

Design in `06-link-capture-design.md`. Implemented as **deterministic
preservation + LLM shell**:

- `snapshotter.py`: per page, always writes `page.html` (raw) and
  `extracted.md` (full text); writes `page.offline.html` via `monolith` when
  available. Lives in `sources/snapshots/<stem>/` in the vault. Never fails a
  capture.
- `processor._build_link_note`: the LLM emits only frontmatter/summary/themes
  (source prompt updated to forbid transcribing the body); the pipeline
  injects a verbatim `## Page Content` head (word-capped) plus links to the
  snapshot. So preserved page text is code-owned and validator-checkable, not
  LLM-paraphrased.
- Config: `link_capture:` block. Docs: SETUP.md monolith note; `check_setup.py`
  reports monolith presence.

## Incidental fix

`git_manager.py` used `Dict[str, Any]` annotations without importing them — an
import-time `NameError` that made the entire processor path unimportable. The
new pytest suite surfaced it immediately on first real import. Fixed.

## Tests

New `tests/` pytest suite, **43 passing**:
- `test_output_validator.py` — the two January corrupted notes are regression
  fixtures and must always fail; corruption/verbatim/fence/mode behavior.
- `test_queue_manager.py` — status flow, tweet + telegram dedup, size guards,
  written-state recovery.
- `test_file_writer.py` — routing (reflection→notes), atomicity, fences.
- `test_snapshotter.py` — artifacts, vault-relative paths, monolith-absence,
  `head_by_words` boundaries.
- `test_processor_link_note.py` — section injection helpers.

`pytest` added to `requirements.txt`. Run: `python -m pytest tests/ -q`.

## Verified, but NOT end-to-end

All checks here are unit-level + import + compile. No live run was possible in
this environment (no API key, Telegram, vault, monolith, or network). The
first real end-to-end pass on Bentendo — a Telegram capture, a tweet import, a
link capture with monolith installed — is the recommended Phase 2 acceptance
step before relying on the pipeline.

## Deferred to a Phase 2 follow-up

- Timezone-aware timestamps (item 10b)
- Image download retry + content-type/magic-byte validation (item 11)
- PDF library dedup (PyPDF2 vs pypdf)
- Reframing `personal_analysis` analyzer prompts to the 04 tone contract
  (Phase 4 territory, noted here so it isn't lost)
- Spec nit: `02-capture.md` still omits the `Idea:` prefix and the unparsed
  `Hubs:` passthrough note

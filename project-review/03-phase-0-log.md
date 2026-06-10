# Phase 0 Log — Prune & Split

> **Executed:** 2026-06-10
> **Basis:** Deletion list approved in `01-implemented-vs-aspirational.md` §10.

## What was removed

**Local LLM backend (Q11 — Claude only):**
- `scripts/processors/ollama_client.py`
- `scripts/processors/hybrid_llm_client.py`
- `specs/prompts/local/` (3 local-model prompt variants)
- `llm:` routing/ollama block in `config/config.yaml`
- `build_llm_client()` simplified to Claude-only; warns if a stale `llm:` block
  requests a removed backend

**Viewer (Q12 — Obsidian renders the vault):**
- `scripts/viewer/` (app, indexer, parser, templates, static, README)
- `scripts/start_viewer.py`, `scripts/rebuild_index.py`, `scripts/diagnose_vault.py`
- `test_viewer.sh`
- `specs/24-viewer-spec.md`, `specs/25-viewer-implementation.md`
- Viewer-only deps from `requirements.txt`: flask, werkzeug, markdown2, pygments,
  watchdog — plus `markdown` (imported nowhere)

**Personal content out of the engine repo (Q3):**
- The two corrupted test notes moved to `tests/fixtures/corrupted-notes/`
  (kept as regression fixtures for the Phase 2 output validator)
- 17 empty hub stubs deleted (names preserved below for vault regeneration)
- Hardcoded personal Windows vault path removed from `config/config.yaml`
  (`notes_root` is now a placeholder set locally, never committed)

**Stale docs:**
- `IMPLEMENTATION_STATUS.md` (frozen at January "Phase 2" state)

**Hygiene:**
- Fixed `,gitkeep` → `.gitkeep` typos in `inbox/` and `archive/`
- Added `.gitkeep` to now-empty `notes/` and `hubs/`

## Hub names preserved for vault regeneration

When hubs are recreated in the Obsidian vault (Phase 5 / Q10 — connector nodes plus
regenerated summaries), these were the 17 concepts, all created 2026-01-09, all of
which were still `status: empty` with no linked notes:

Aesthetics · Analysis · Change Over Time · Emotion · Health and Illness ·
Internet Culture · Meaning · Media History · Memory · Music · Performance ·
Persona · Relationships · Responsibility · Reviews · Storytelling ·
Stress and Burnout

Everything deleted remains recoverable from git history (last full state:
commit `45d5fa6`).

## What Phase 0 did NOT touch

- `run.py` vs `telegram_bot.py` entry-point consolidation (flagged VERIFY in the
  audit — decide during Phase 2)
- PDF library dedup (PyPDF2 vs pypdf — Phase 2)
- Telegram allowlist enforcement, queue `LIMIT` parameterization, atomic
  write+commit, web fetcher hardening (all Phase 2 fixes)
- All spec rewrites (Phase 1)

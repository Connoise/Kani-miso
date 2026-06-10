# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this repository is

**Kani-miso** is a personal catalog + analysis engine. **This repo is the engine
only** — Python pipeline, specs, prompts, config. The actual catalog (notes,
tweets, sources, hubs, analysis outputs) lives in a separate Obsidian vault on the
owner's machine, located via `notes_root` in `config/config.yaml` (set locally,
never committed with a personal path).

The system was consolidated in June 2026 ("the pivot"): catalog-not-archive
framing, Claude-only backend, viewer removed, 40+ specs collapsed into six. Git
history holds everything prior. Do not resurrect pre-pivot philosophy or
components without being asked.

## The six specs are the authority

Read before significant work; if anything conflicts, these win (highest number
wins within the set):

1. `specs/00-purpose.md` — what the project is, scope, success criteria
2. `specs/01-data-model.md` — entities, frontmatter, vault layout, validity
3. `specs/02-capture.md` — pipeline, surfaces, the faithful-capture contract
4. `specs/03-organization.md` — hubs (with regenerated summaries) and tags
5. `specs/04-analysis.md` — snapshot self-analysis engine
6. `specs/05-ai-and-ops.md` — AI boundaries, ops, security floor

`project-review/` holds the audit, consolidation plan, and phase logs that track
remaining work (Phase 2: capture-core hardening).

## Runtime-coupled files — edit with care

These are loaded by `claude_client.py` at runtime; treat them as code (behavior
changes, keep consistent with `specs/02-capture.md`):

- `specs/telegram-processing-prompt.md`
- `specs/source-processing-prompt.md`
- `specs/pdf-processing-prompt.md`

## Non-negotiable rules

- **Raw Capture sections are verbatim** — never edit, paraphrase, or normalize
  owner-authored capture text, anywhere, ever.
- **Interpretation asserts only what the source text supports** — no invented
  emotions, significance, or conclusions.
- **No personal content in this repo** — no vault content, no personal paths, no
  secrets (`config/.env` is gitignored; keep it that way).
- **Hub create/merge/rename/archive, bulk operations, deletions** → owner
  confirmation first.
- **Never `git push` without an explicit owner request.** Auto-commit after
  processing is fine.
- The Telegram bot must only serve `TELEGRAM_CHAT_ID`. Never weaken or remove
  the allowlist.

## Working on the code

- Entry points: `scripts/telegram_bot.py` (bot), `scripts/processor.py` (queue →
  Claude → vault → commit), `scripts/run.py` (both), 
  `scripts/twitter_archive_processor.py` (X archive import — the primary capture
  source), `scripts/personal_analysis/` (snapshot analysis), 
  `scripts/hub_analyzer.py` (hub linking/maintenance).
- Claude-only LLM backend via `build_llm_client()` in
  `scripts/processors/llm_client.py`. Do not reintroduce local/hybrid backends.
- `tests/fixtures/corrupted-notes/` are intentionally broken files for validator
  regression tests — do not "fix" them.
- There is no pytest suite yet (Phase 2). Until then, verify changes with
  `python -m py_compile`, `scripts/check_setup.py`, and manual smoke scripts.

## When uncertain

Prefer the smaller action; ask before structural changes; never trade fidelity
for tidiness.

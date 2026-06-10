# Kani-miso

A personal catalog and self-analysis engine.

Kani-miso ingests personal captures — Telegram messages, an X/Twitter archive,
articles, PDFs, images — into a faithful markdown catalog (an Obsidian vault),
organizes them through hub notes and tags, and periodically generates candid,
evidence-cited **snapshot analyses** of the author's thinking, emotional
patterns, philosophy, and life direction. Each snapshot is a dated checkpoint;
the sequence is the record.

**This repository is the engine only.** The catalog itself lives in a separate,
private vault and is never committed here.

## How it works

```
capture surfaces ──► SQLite queue ──► Claude processing ──► validated markdown
 (X archive,                                                 in the vault
  Telegram,                                                       │
  links/PDFs)                                              git commit (push manual)

vault corpus ──► personal_analysis engine ──► dated snapshot in vault/analysis/
```

## Layout

```
specs/            the six operational specs (authority) + runtime prompt templates
scripts/          the pipeline (bot, queue, processor, importers, analysis engine)
config/           config.yaml (tracked, no personal data) + .env (secrets, gitignored)
tests/fixtures/   regression fixtures (intentionally corrupted notes)
project-review/   audit, consolidation plan, phase logs (working documents)
```

Start with [`specs/00-purpose.md`](specs/00-purpose.md); setup instructions in
[`SETUP.md`](SETUP.md); rules for AI assistants in [`CLAUDE.md`](CLAUDE.md) and
[`specs/05-ai-and-ops.md`](specs/05-ai-and-ops.md).

## Principles (short form)

1. **Fidelity first** — original capture text is preserved verbatim, always.
2. **Interpretation only from evidence** — per-note processing asserts nothing
   the text doesn't say; deep synthesis happens at collection level, cited and
   confidence-marked.
3. **Catalog, not shrine** — standard data practices, plain markdown, git
   history; no ceremony.
4. **The owner is the authority** — AI formats, organizes, and analyzes within
   defined boundaries; structural decisions are confirmed.

## Status

Post-consolidation (June 2026). Phase 0 (prune) and Phase 1 (spec rewrite) are
done; Phase 2 (capture-core hardening: output validation, mandatory Telegram
allowlist, atomic write→commit, pytest suite) is next. Working log in
`project-review/`.

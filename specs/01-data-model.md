# 01 — Data Model

The vault filesystem is the database. Every entity is a markdown file with YAML
frontmatter, parseable by standard tools and readable raw.

## Vault layout

All paths are relative to `notes_root` (the Obsidian vault, configured locally):

```
inbox/        raw captures awaiting processing (rarely used; queue is SQLite)
notes/        all processed personal captures (thoughts, reflections, questions)
sources/      processed external material (articles, PDFs, links)
tweets/       processed tweets from the X archive import
images/       binary attachments, date-foldered (images/YYYY/MM/DD/)
hubs/         conceptual connector notes (no date in filename)
analysis/     snapshot analysis runs, one dated folder per run (see 04-analysis.md)
archive/      frozen material no longer active (manual moves only)
```

**Changes from the old model:**
- `/reflections/` is **merged into `/notes/`**. A reflection is a note with
  `type: reflection` in frontmatter, not a separate folder. (Code still routes
  reflections to a separate folder — scheduled for Phase 2; new vaults should not
  create the folder.)
- `/projects/` is **dropped**. It was specified but never used. Reintroduce only if
  a real need appears.

## Note (`notes/`)

The unit of capture. Filename: `YYYY-MM-DD--slug.md` (date = capture date).

```yaml
---
source: telegram | manual | twitter-archive
type: thought | reflection | question | log     # default: thought
captured_at: ISO-8601
surface: mobile | desktop | unknown             # context only; no behavioral effect
capture_mode: quick | extended                  # default: quick
mood: <short phrase, only if stated by owner>   # optional
energy: <short phrase, only if stated>          # optional
trigger: <what prompted it, only if stated>     # optional
tags: [..]                                      # optional, always
---
```

Body sections:

| Section | Rule |
|---|---|
| `# Title` | Short descriptive title |
| `## Raw Capture` | **Verbatim** original text. Never edited, paraphrased, or trimmed. |
| `## Context` | Only metadata the owner supplied (surface, mood, trigger). |
| `## Initial Interpretation` | Optional. States only what the text supports; provisional language. |
| `## Themes` | Optional. Broad themes present in the text. |
| `## Related Hub Notes` | Optional. `[[Hub]]` links; **omit the section if none apply**. |

A note is valid only if: frontmatter parses, the file starts with `---` on line 1,
`## Raw Capture` matches the queued capture text exactly, and the content contains
no formatting corruption (no `&nbsp;`, no escaped markdown like `\[`, no code-fence
wrapping). The Phase 2 output validator enforces this before any file is written;
`tests/fixtures/corrupted-notes/` holds the regression cases.

## Source (`sources/`)

External material. Filename: `YYYY-MM-DD--slug.md`.

```yaml
---
type: source
source_type: article | pdf | book | video | wikipedia
url: <if applicable>
title: ..
author: <if available>
captured_at: ISO-8601
tags: [source, ..]
---
```

Body: source info block, summary, "Why This Was Captured" (owner's stated reason
only), key content/excerpts, themes. The operative templates are the runtime
prompts (`specs/source-processing-prompt.md`, `specs/pdf-processing-prompt.md`).

## Tweet (`tweets/`)

A note with `source: twitter-archive`, `type: tweet`, original tweet text verbatim
in Raw Capture, and tweet date as the file date. Produced by
`scripts/twitter_archive_processor.py` via the normal queue.

## Hub (`hubs/`)

A connector node gathering notes around a concept. Filename: `Concept Name.md`
(Title Case, **no date**). Hubs are the only entity that is continuously edited.

```yaml
---
type: hub
status: empty | active | archived
created_at: ISO-8601
last_updated: ISO-8601
---
```

Sections: see `03-organization.md` for the template, including the regenerated
`## Summary` section and maintained `## Linked Notes` backlinks.

## Statuses

Old note lifecycle values (`evolving`, `evergreen`, `dormant`, `obsolete`) are
**dropped** — they were never operationalized. Remaining:

- **Notes/Sources**: none required. A written file is processed; a file moved to
  `archive/` is archived.
- **Hubs**: `empty` (no linked notes yet) → `active` (≥1 linked note) → `archived`
  (concept retired; file kept).

## Links

- `[[Hub Name]]` in a note body = "this note touches this concept".
- A hub's `## Linked Notes` lists `[[YYYY-MM-DD--slug]]` backlinks. Stubs start
  empty; the linking pass maintains them (`03-organization.md`). This resolves the
  old stub-vs-backlink contradiction: empty at creation, populated by maintenance.
- Note→note links are allowed anywhere, never required.
- Broken links are warnings, not errors.

## Identity and uniqueness

- Note/source/tweet identity = filename (date + slug). Filenames don't change.
  Collisions get a `-HHMMSS` suffix at write time.
- Hub identity = concept name; renames require updating inbound links.
- Tags are free-form lowercase strings; same string = same tag. Tags are optional
  everywhere and old tags are never retroactively edited.

# Corrupted Note Fixtures

These are the first two notes the pipeline ever produced (2026-01-10), moved here
from `/notes/` during Phase 0. They are kept **deliberately, in their broken state**
as test fixtures.

## What's wrong with them

Every line is prefixed with `&nbsp;`, markdown characters are backslash-escaped
(`captured\_at`, `\[raw, reflection]`), and the YAML frontmatter is mangled —
so Obsidian cannot parse the frontmatter or tags. This is **failure mode #2** from
the audit (`project-review/01-implemented-vs-aspirational.md` §6); it is distinct
from the ```` ```markdown ```` wrapper issue that `file_writer.strip_code_block_wrapper()`
handles.

## What they're for

Phase 2 adds a post-generation output validator that must reject content like this
before it is written to the vault. These files are the regression fixtures for that
validator: a test should assert that both files **fail** validation.

Do not "fix" these files.

# 00 — Purpose

> One of six operational specs. Together with `01-data-model.md`, `02-capture.md`,
> `03-organization.md`, `04-analysis.md`, and `05-ai-and-ops.md`, this replaces the
> previous 40+ spec files (consolidated 2026-06; history in git).

## What Kani-miso is

A personal **catalog and analysis engine** with two deliverables:

1. **A faithful catalog** of thoughts, captures, and external material — accurately
   ingested, stored as plain markdown, and interconnected through hubs and tags.
2. **Periodic snapshot analyses** — candid, evidence-based profiles of the author's
   thinking, emotional patterns, philosophy, and life direction, generated from the
   accumulated corpus. Each snapshot is a dated life checkpoint. The analysis function
   is also a deliberate experiment in LLM meaning- and pattern-processing.

It is a **catalog, not a sacred archive**. Standard data practices apply: don't lose
data, don't corrupt data, keep history in git. There is no immutability theology
beyond that.

## Repo vs. vault

- **This repository is the engine**: code, specs, prompts, configuration. No personal
  content is committed here.
- **The catalog lives in a separate Obsidian vault** on the owner's machine
  (`notes_root` in `config/config.yaml`, set locally, never committed). All notes,
  sources, tweets, images, hubs, and analysis outputs are written there.

## Who reads it

The owner — now, and at future checkpoints when comparing analyses over time.
Others may read it someday; if so, summaries will be prepared for them. Nothing is
written for an external audience.

## Operating principles

1. **Fidelity first.** The original capture text is preserved verbatim. Processing
   may add structure and metadata but never alters, paraphrases, or omits the source.
2. **Interpretation states only what the text supports.** Per-capture processing does
   not invent conclusions, emotions, or significance not present in the input.
3. **Deep interpretation happens at collection level.** Pattern-finding, synthesis,
   and judgment belong to the snapshot analysis (`04-analysis.md`), where aggregate
   evidence exists — not to individual note processing.
4. **The owner is the authority.** AI organizes and analyzes within the rules in
   `05-ai-and-ops.md`; structural decisions and deletions need owner confirmation.
5. **Durable formats.** Markdown + YAML frontmatter, readable without any tool.

## Scope

**In scope:**
- Thoughts, reflections, questions, observations (one note type — see `01-data-model.md`)
- The owner's X/Twitter archive — **a primary capture source and analysis corpus**
  (this supersedes the old spec's exclusion of social-media imports)
- Articles, links, documents, and PDFs the owner chooses to capture
- Images sent through capture surfaces
- External self-analysis inputs (e.g., Plastiglom morning-exercise outputs) as
  analysis corpus

**Out of scope:**
- Task management, to-do lists, calendars
- Credentials, secrets, others' private information
- Anything written to perform for an external audience

## Success and failure

The project **succeeds** if the catalog is accurate and navigable, and if each
analysis snapshot is honest, evidence-cited, and useful as a record of who the owner
was at that time.

The project **fails** if captures are cataloged inaccurately (lost, corrupted,
reformatted beyond recognition), or if analyses placate instead of inform.

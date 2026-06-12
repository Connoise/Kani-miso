# Link Capture Design — Preserve + Catalog

> **Created:** 2026-06-12
> **Decision:** Tier 1 + monolith (owner-selected). Raw HTML + deterministic text
> extraction always; self-contained offline snapshot via `monolith` when available.

## Goal

Capture a URL so that (a) the page's content is **preserved** and accessible
later even if the page dies, and (b) the capture is **cataloged** as a normal
Obsidian source note with summary, themes, and links.

## What exists today (verified)

`Source:` captures already fetch pages: `web_fetcher.fetch_and_convert()` →
requests (10 MB cap, 30 s timeout, scheme check) → BeautifulSoup metadata +
main-content extraction → html2text markdown → handed to Claude, which
*transcribes* content into the note's `## Key Content`.

Two failures for the preservation goal:
1. **The raw HTML is discarded** after parsing — nothing is preserved.
2. **The LLM is the transcriber** — page content in the note is
   LLM-paraphrased, lossy, and unverifiable (the validator mostly skips
   verbatim checks for source captures since the capture body is just a URL).

## Design principle

**The LLM never transcribes the page; the pipeline does.** Deterministic code
preserves content; the LLM only summarizes and tags around it. This extends
the faithful-capture contract to web content and makes it mechanically
verifiable.

## Architecture

### Layer A — Preservation artifacts (deterministic, no LLM)

For each link capture, a snapshot folder in the vault:

```
sources/snapshots/YYYY-MM-DD--slug/
  page.html           raw fetched HTML, exactly as received        (always)
  page.offline.html   self-contained snapshot, assets inlined      (monolith, if available)
  extracted.md        full deterministic text extraction           (always)
```

- `extracted.md` is the html2text conversion of the extracted main content —
  full length, no truncation. This is the in-Obsidian-readable preserved copy.
- `page.offline.html` is produced by shelling out to
  `monolith <url> -o page.offline.html` with a subprocess timeout and a size
  cap. Monolith inlines CSS/images/fonts into one file — a faithful visual
  copy, openable in any browser from the vault. It does **not** execute
  JavaScript; SPA-style pages will preserve thin (the raw HTML + extraction
  still capture what the server sent). A headless-browser tier can be added
  later behind the same config switch if that becomes a real limitation.
- Snapshot failure (monolith missing, timeout, oversized) **never fails the
  capture** — log, keep `page.html`, continue.

### Layer B — Catalog note (the Obsidian entry)

`sources/YYYY-MM-DD--slug.md`:

```markdown
---
type: source
source_type: article
url: <original URL>
title: / author: / site_name: / published_date:   (extracted metadata)
captured_at: <ISO>
snapshot: sources/snapshots/YYYY-MM-DD--slug/     (relative path)
tags: [source]
---
# <Title>

## Source Information
URL, author, site, capture time, links to the snapshot artifacts
([[.../extracted.md]], offline snapshot, raw HTML)

## Why This Was Captured
<owner's message text, verbatim — validator-checked>

## Summary            ← LLM (from the extracted text)
## Themes             ← LLM

## Page Content       ← INJECTED BY PIPELINE from extracted.md, verbatim,
                        truncated at a config cap (e.g. 2,000 words) with a
                        pointer to the full extracted.md
```

The LLM receives the extracted text and produces only
frontmatter/summary/themes; the pipeline assembles the final note and injects
`## Page Content` itself. The output validator then verifies (a) the owner's
context verbatim, (b) the injected content matches `extracted.md`'s head.

### Capture UX (Telegram)

Unchanged: `Source: <label>` + URL on its own line (+ optional "why"). One
added convenience: a message whose entire body is a bare URL is treated as a
`Source` capture instead of a `Thought` (today it becomes a Thought note
containing a naked link — almost never what's wanted).

### Config

```yaml
link_capture:
  snapshot: monolith        # monolith | none
  snapshot_timeout_seconds: 60
  max_snapshot_mb: 25
  note_content_word_cap: 2000   # Page Content section; full text in extracted.md
```

`SETUP.md` gains a one-line install note (monolith is a single static binary:
package manager or GitHub release). `check_setup.py` reports its presence.

## Dependencies

- **No new Python packages** (requests, bs4, html2text already pinned).
- **monolith**: external binary on Bentendo, optional at runtime by design.

## Sequencing

Link capture lands **after the Phase 2 fidelity/security core**, because it
builds directly on two of its items:
- the **SSRF guard + redirect cap** on `web_fetcher` (this feature widens the
  fetcher's exposure — guard first), and
- the **wired output validator** (which gains the injected-content check).

So the order becomes: Phase 2 items 1–4 (validator+tests, mandatory allowlist,
atomic unit of work, tweet dedup) → fetcher hardening → **link capture
upgrade** → remaining cleanups. Page-version refreshes need no special
handling: capturing the same URL later just creates a new dated note +
snapshot, which is correct catalog behavior (pages change; snapshots are
moments).

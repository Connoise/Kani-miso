# Hybrid Processing Model Specification

## Purpose

This document specifies the **hybrid model** for the archive:

- Captures are accepted anytime (including when no PC is online)
- A lightweight, always-available queue stores captures durably
- A home/work PC performs batch processing when turned on
- The PC writes Markdown into the repo and pushes to Git

This model minimizes always-on infrastructure while preserving reliability.

---

## Definitions

### Capture Surface
Where a capture originates (e.g., mobile, desktop-work, desktop-home).
See `capture-surface-abstraction.md`.

### Queue
A durable holding area for unprocessed captures.
The queue must remain available even when the PC is off.

### Processor
A workflow run on a PC that:
- fetches queued items
- generates Markdown notes per specs
- writes files into the repo
- commits and pushes changes to Git

### Canonical Store
The Git repository containing Markdown files.
The repo is the source of truth; the queue is not.

---

## Architectural Principles

1. **Queue is not the archive**
   - The queue stores inputs temporarily
   - The repo stores the canonical notes

2. **Processing is batch-oriented**
   - Captures are processed when the PC is available
   - Real-time processing is not required

3. **History is preserved**
   - Raw capture content is immutable once recorded
   - Processing only adds interpretation layers

4. **Automation is reversible**
   - No silent overwrites
   - Prefer appends and new files over edits-in-place

---

## Queue Requirements

A valid queue system must support:

- Durable storage of:
  - raw text
  - links
  - files (or references to files)
  - timestamps
  - minimal metadata (surface, optional mood/context)

- A reliable way to mark items as:
  - pending
  - processed
  - failed (optional)

- Export or retrieval that the PC can perform later

The queue may be implemented using:
- a messaging platform (e.g., Telegram Saved Messages/private channel)
- an issue tracker (e.g., GitHub Issues)
- a cloud folder (e.g., Drive folder)
- another durable inbox-like system

Implementation details are not defined here.

---

## Processing Trigger

Processing occurs when:
- the PC is turned on, and
- the user initiates a processing run manually or via scheduled local task

The system must not require the PC to be always on.

---

## Processing Stages (On PC)

The processor performs the following stages in order:

1. **Fetch**
   - Retrieve all pending queue items since last successful run

2. **Normalize**
   - Assign required metadata fields:
     - source
     - captured_at (from queue timestamp if available)
     - surface (if available, else unknown)
     - capture_mode (quick/deliberate/drafted if inferable, else unknown)
   - Preserve original capture verbatim

3. **Classify (Lightweight)**
   - Determine note destination folder:
     - `/inbox/` for raw or minimally processed
     - `/notes/` for processed time-bound notes
     - `/reflections/` for diary/subjective entries
     - `/sources/` for external material summaries
   - Classification must not imply importance or authority

4. **Process with Claude**
   - Use prompts in `/specs/`, especially:
     - `telegram-processing-prompt.md` (for Telegram captures)
     - `04-processing-spec.md`
     - `note-editing-safety.md`
     - `contradiction-handling.md`
   - Output must be Obsidian-compatible Markdown

5. **Link Suggestion**
   - Prefer hub links (broad canonical concepts)
   - Do not create micro-hubs
   - Hub promotion requires confirmation (see `hub-promotion-criteria.md`)

6. **Write Files**
   - Create new Markdown notes as needed
   - Avoid overwriting existing notes unless explicitly versioning
   - Preserve raw capture text in each note

7. **Commit**
   - Create a Git commit for the batch
   - Include meaningful commit message (see Git Policy below)

8. **Push**
   - Push to remote Git repository

9. **Acknowledge/Mark Processed**
   - Mark queue items as processed
   - Store a local record of the last processed queue timestamp/ID

---

## Git Policy (Hybrid)

### Branch Strategy (Recommended)
- Default: commit directly to main only if processing is trusted
- Safer: create a dated branch per batch:
  - `captures/YYYY-MM-DD` or `batch/YYYY-MM-DD-HHMM`

### Commit Message Convention
Use a consistent format, for example:
- `capture: <short topic> (N notes)`
- `process: batch YYYY-MM-DD (N items)`
- `sources: add summaries (N)`

### Overwrite Policy
- Do not overwrite existing notes without versioning
- Prefer:
  - new notes
  - appended “Later Reflection” sections
  - explicit revision notes with timestamps

---

## Failure Handling

Failure is acceptable and expected.

If any stage fails:
- do not mark queue items as processed
- do not delete or mutate queue items
- allow a later re-run

Partial processing is acceptable if:
- the repo remains consistent
- no history is erased

---

## Security and Secrets

- Queue credentials and Git credentials must not be stored in notes
- Automation tokens must not be written into the repo
- If a cloud runner is used only for queueing, it must not have repo write access unless explicitly intended

---

## Compatibility With Future Always-On Automation

This hybrid model remains compatible with future upgrades:

- If an always-on runner is added later, it may:
  - ingest captures into the queue
  - perform non-destructive pre-processing (optional)

But canonical writing to the repo should remain:
- reversible
- spec-governed
- history-preserving

---

## Summary

In the hybrid model:
- The queue is always available
- The PC does the intelligence work when online
- The repo remains the canonical, durable archive
- History and ambiguity are preserved
- Automation supports flow, not meaning

# Personal Knowledge, Thought, and Memory Archive

This repository contains a long-term personal knowledge system designed to capture thoughts, emotions, and information over time while preserving context, uncertainty, and change.

This is not a productivity system.
This is not a static knowledge base.

It is a living archive of attention.

> **Note:** This README provides an overview for newcomers. For technical specifications and system operators, see [`specs/00-overview.md`](specs/00-overview.md).

---

## How to read this repository

This system is organized around a core distinction:

- **Notes are events**
- **Hub notes are places**

If you treat all files the same, you will break the system.

---

## Core philosophy

This archive is:

- **Rhizomatic**  
  Non-hierarchical. Meaning emerges from links, not folders.

- **Temporal**  
  Notes are snapshots in time, not timeless truths.

- **Reflective**  
  Emotional tone, uncertainty, and subjectivity are preserved.

- **Durable**  
  Markdown-first, tool-agnostic, readable without automation.

- **AI-assisted, not AI-directed**  
  AI may suggest, but never finalize meaning.

Contradictions are expected.  
Dormancy is allowed.  
Change is recorded, not corrected.

---

## Folder overview

    /specs/        ← System design & rules (read first)
    /inbox/        ← Raw captures (immutable)
    /notes/        ← Time-bound processed notes
    /reflections/  ← Diary-style, emotional, subjective notes
    /hubs/         ← Long-lived conceptual gathering places
    /sources/      ← External materials (articles, PDFs, Wikipedia)
    /projects/     ← Active lines of inquiry or creation
    /archive/      ← Frozen snapshots of thinking

---

## Critical distinction: Notes vs hubs

### Notes (events)
- Represent a moment of attention
- Are time-bound
- May be messy or incomplete
- May contradict other notes
- Should not be rewritten to “resolve” meaning

Notes primarily link **outward** to hubs.

### Hub notes (places)
- Represent conceptual gathering points
- Are long-lived
- Are non-authoritative
- May contain contradictions
- Accumulate meaning over time

Hubs primarily link **inward** to notes.

Hubs must **not**:
- act as summaries
- enforce consensus
- collapse ambiguity
- replace notes

---

## Tags vs hubs

- **Tags** are historical signals  
  (“What did this note touch at the time?”)

- **Hubs** are structural navigation  
  (“Where does this belong conceptually?”)

Tags are optional and may decay.  
Hubs are persistent and structural.

Do not reorganize content based on tags.

---

## Specs directory (system authority)

The `/specs/` folder defines how this system works.

If there is a conflict between a note, a hub, or an automated suggestion, the specs take precedence.

Key files to read first:
- `00-overview.md`
- `02-system-architecture.md`
- `04-processing-spec.md`
- `06-tagging-ontology.md`
- `12-note-lifecycle.md`
- `hub-stub-generator.md`

---

## AI / Claude guidance

If you are an AI assistant (Claude or similar):

### You may
- Suggest links to hub notes
- Suggest new hub creation (sparingly)
- Preserve ambiguity and contradiction
- Add temporal context
- Propose structural changes with explanation

### You must not
- Rewrite notes to be definitive
- Remove emotional language
- Resolve contradictions
- Merge notes without explicit instruction
- Turn hubs into encyclopedic summaries
- Delete historical context

When uncertain:
- Do less
- Preserve openness
- Ask before enforcing structure

---

## How notes evolve

Notes follow a lifecycle:

1. Capture  
2. Context encoding  
3. Initial processing  
4. Linking to hubs  
5. Dormancy  
6. Re-emergence  
7. Possible hub formation  
8. Re-interpretation  
9. Archival  

Dormancy is not failure.  
Contradiction is not error.

---

## How hubs evolve

Hubs are discovered, not planned.

A hub exists because:
- multiple notes gravitate toward it
- it reduces wording drift
- it serves as a navigational landmark

Hub maintenance should:
- preserve history
- surface tensions
- track change over time

Use `hub-maintenance-prompt.md` for periodic review.

---

## Design intent (summary)

This system is optimized for:
- long-term self-understanding
- interpretability over years
- coexistence of multiple truths
- AI collaboration without cognitive takeover

It is intentionally slower, looser, and more humane than conventional PKM systems.

---

## If you are unsure what to do

Default actions:
- Preserve original text
- Add links rather than edits
- Create space rather than closure
- Let meaning emerge over time

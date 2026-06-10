# 03 — Organization: Hubs and Tags

Hubs are the connective tissue of the catalog; tags are lightweight historical
markers. Neither is required for a note to be valid.

## Hubs

A hub is a connector node for one broad concept: it gathers notes via backlinks
and carries a short regenerated summary of what its notes share.

### Creation rule (single threshold)

Create a hub when **either**:
- a concept is substantively present in **3 or more notes**, or
- the owner asks for it.

Below that threshold, do nothing — recurrence will surface real concepts. AI may
*propose* hub creation when the threshold is met; **creating, merging, renaming, or
archiving a hub always requires owner confirmation** (`05-ai-and-ops.md`).

### Naming rules

- Noun phrase, conceptually broad: `Memory`, `Internet Culture`, `Caregiving`
- No tense, metaphor, judgment, or phrased interpretation
  (not `Why Technology Feels Cold Now`)
- No near-synonyms of existing hubs — link to the existing hub instead

### Hub template

```markdown
---
type: hub
status: empty
created_at: <ISO date>
last_updated: <ISO date>
---

# <Concept Name>

## Summary
(regenerated — see below; empty until the hub has linked notes)

## Open Questions
- (optional, owner-maintained)

## Linked Notes
- (maintained by the linking pass)
```

### The Summary section

Each maintenance pass **regenerates** `## Summary`: 2–6 sentences describing what
the linked notes collectively touch on, including disagreements between notes
("notes from January treat X as energizing; March notes treat it as draining").
It is a navigational snapshot, dated by `last_updated` — not source material, not
an authority, and safe to regenerate because hubs are organization, not capture.
The Summary never quotes raw captures out of context and never resolves
disagreements between notes; it reports them.

### Backlink maintenance (resolves the old contradiction)

- A new hub starts with an **empty** `## Linked Notes` (status `empty`).
- The linking pass (`scripts/hub_analyzer.py`, or manual edits) adds
  `[[YYYY-MM-DD--slug]]` entries when notes reference the hub or clearly touch its
  concept, flips status to `active`, regenerates the Summary, and updates
  `last_updated`.
- Notes link outward with `[[Hub Name]]`; hubs link inward via Linked Notes. Both
  directions are maintained, neither is required at capture time.

### Lifecycle

`empty` → `active` (first linked note) → `archived` (concept retired; file and
links kept, summary frozen). Hubs are never deleted, only archived.

### Legacy hub names

The 17 stubs removed from the engine repo in Phase 0 are candidates to recreate
in the vault **only when notes actually reference them** (the creation rule
applies; no bulk regeneration): Aesthetics, Analysis, Change Over Time, Emotion,
Health and Illness, Internet Culture, Meaning, Media History, Memory, Music,
Performance, Persona, Relationships, Responsibility, Reviews, Storytelling,
Stress and Burnout.

## Tags

- Tags are optional, lowercase, free-form strings recording what a note touched
  at capture time.
- Tags are historical: old tags are never renamed, pruned, or "decayed" by
  tooling. (The old tag-decay mechanism is dropped — unused tags simply stop
  appearing in new notes.)
- Tags never drive structure or reorganization; navigation is hubs' job.
- Processing suggests at most a few broad tags; none is always acceptable.

## Division of labor

| Question | Mechanism |
|---|---|
| "What did this note touch at the time?" | Tags |
| "Where does this concept gather?" | Hubs |
| "What belongs together temporally?" | Filenames (dates) |

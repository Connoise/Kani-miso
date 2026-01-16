# Hierarchy and Rhizomatic Structure

## Purpose

This document resolves the apparent contradiction between the system's "rhizomatic (non-hierarchical)" philosophy and its use of directory folders.

---

## The Apparent Contradiction

**Claim**: The system is "rhizomatic (non-hierarchical)"

**Reality**: The repository uses folders:
```
/inbox/
/notes/
/reflections/
/hubs/
/sources/
/projects/
/archive/
```

**Question**: How can a system claim to be non-hierarchical while using a hierarchical folder structure?

---

## Resolution: Structural vs Semantic Hierarchy

### Structural Hierarchy (The Folders)

**Purpose**: Pragmatic file organization for human and machine navigation

**What It Is**:
- A filing system
- A convenience for tools
- A way to distinguish entity types at the filesystem level

**What It Is NOT**:
- A claim about conceptual relationships
- A constraint on meaning
- A taxonomy of importance

### Semantic Hierarchy (The Content)

**Purpose**: Networked, non-hierarchical relationships between ideas

**What It Is**:
- Notes link to hubs (non-hierarchical many-to-many)
- Hubs link to notes (non-hierarchical many-to-many)
- Notes link to notes (non-hierarchical peer relationships)
- Multiple valid traversal paths exist

**What It Is NOT**:
- Parent-child relationships
- Strict classification trees
- Single canonical organization

---

## Rhizomatic Principles

### 1. Principle of Connection

**Any note can link to any other note or hub regardless of folder location.**

Example:
- A reflection can link to a hub
- A source can reference a note
- A project can include notes from multiple folders

**Constraint**: Links are semantic, not structural

### 2. Principle of Heterogeneity

**Different entity types can coexist without merging.**

Example:
- Reflections remain distinct from notes
- Sources remain distinct from interpretations
- Hubs remain distinct from notes

**Constraint**: Type distinctions serve clarity, not hierarchy

### 3. Principle of Multiplicity

**A note can exist in multiple conceptual contexts simultaneously.**

Example:
- One note can link to multiple hubs
- One hub can contain notes from different time periods
- One project can reference notes without "owning" them

**Constraint**: No single organizing principle dominates

### 4. Principle of Asignifying Rupture

**The graph of meaning can be broken and reconnected at any point.**

Example:
- Dormant notes can re-emerge
- Hubs can become obsolete and replaced
- Links can be added retrospectively

**Constraint**: Structure is provisional and revisable

### 5. Principle of Cartography

**The system maps thinking rather than reproducing it.**

Example:
- Tags are signals, not categories
- Hubs are landmarks, not summaries
- Links are traces, not logical implications

**Constraint**: The map is descriptive, not prescriptive

### 6. Principle of Decalcomania

**The archive is not a copy of thought but an ongoing becoming.**

Example:
- Notes change meaning over time (re-interpretation)
- Contradictions coexist
- Multiple paths to understanding are valid

**Constraint**: There is no "correct" reading of the archive

---

## What Folders Actually Mean

### `/inbox/`
- **Structural Role**: Temporary holding area
- **Semantic Role**: None (pre-semantic content)

### `/notes/`
- **Structural Role**: Default location for processed notes
- **Semantic Role**: Time-bound events

### `/reflections/`
- **Structural Role**: Separate location for emotional/diary notes
- **Semantic Role**: Time-bound events (emotionally inflected)
- **Distinction from /notes/**: Capture mode and tone, NOT importance

### `/hubs/`
- **Structural Role**: Long-lived conceptual gathering points
- **Semantic Role**: Places outside time
- **Distinction from /notes/**: Longevity and function, NOT authority

### `/sources/`
- **Structural Role**: External material
- **Semantic Role**: Attribution anchors
- **Distinction from /notes/**: Origin (external vs internal)

### `/projects/`
- **Structural Role**: Active inquiry lenses
- **Semantic Role**: Temporary organizational overlays
- **Distinction from /notes/**: Scope and duration

### `/archive/`
- **Structural Role**: Frozen historical snapshots
- **Semantic Role**: End of active lifecycle
- **Distinction from /notes/**: Immutability and search exclusion

---

## Why Folders Don't Create Hierarchy

### 1. No Parent-Child Relationships
Folders do not imply that notes "belong to" or are "owned by" hubs.

### 2. No Inheritance
Being in `/notes/` doesn't give a note any properties beyond being a note.

### 3. No Ranking
Hubs are not "more important" than notes because they're in a separate folder.

### 4. No Traversal Constraint
You can read the archive chronologically, thematically, or randomly—folder structure doesn't dictate path.

### 5. Cross-Folder Links Are Primary
The semantic graph (links) is the real structure; folders are just filing.

---

## Practical Implications

### For Users
- Don't worry about which folder a note "should" be in beyond type distinctions
- Links matter more than location
- Reflections aren't "lesser" because they're separate

### For Tools
- Respect folder conventions for entity type detection
- Don't assume folder location = semantic importance
- Support cross-folder search and linking

### For AI Assistants
- Folder location is metadata, not meaning
- Don't suggest "moving" notes to "better" folders
- Respect type distinctions without imposing hierarchy

---

## The Archive as Rhizome

The archive is rhizomatic because:
- **It has multiple entrypoints** (chronological, thematic, search)
- **It has no center** (no master hub or index)
- **It resists totalization** (can't be reduced to a single outline)
- **It allows contradiction** (multiple truths coexist)
- **It evolves unpredictably** (structure emerges rather than being imposed)

The archive uses folders because:
- **Filesystems require them** (pragmatic constraint)
- **Entity types need distinction** (notes vs hubs vs sources)
- **Tools need conventions** (where to write files)

---

## Forbidden Hierarchies

### Do NOT Create:
- Nested hub folders (`/hubs/categories/`)
- Note subcategories (`/notes/work/`, `/notes/personal/`)
- Ranked importance levels
- Required classification paths

### Do NOT Assume:
- Hubs are more valuable than notes
- Older notes are less important
- Notes must "climb" to hub status
- Folder depth implies sophistication

---

## Success Criteria

This structure succeeds if:
- Folders serve as filing convenience only
- Semantic links define meaningful structure
- Multiple traversal paths remain valid
- No single organizing principle dominates
- Users feel free to link across boundaries

This structure fails if:
- Folders become gatekeepers
- Location implies worth
- Cross-folder linking feels wrong
- Users seek the "right" folder for notes
- The archive feels taxonomically rigid

---

## Summary

**Folders are filing cabinets.**
**Links are meaning.**

The system is rhizomatic in its semantic structure while using hierarchical filesystem conventions for pragmatic organization. There is no contradiction.

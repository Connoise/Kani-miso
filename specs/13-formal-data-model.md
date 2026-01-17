# Formal Data Model Specification

## Purpose

This document defines the formal data models, storage semantics, and graph structure for the archive system.

---

## Storage Architecture

### Storage Layer
- **Primary Format**: Markdown files with YAML frontmatter
- **No Database Backend**: The filesystem IS the database
- **Text-First**: All data must remain human-readable
- **Tool-Agnostic**: Must work without specialized software

### File System as Database
```
/inbox/         - Immutable raw captures
/notes/         - Processed notes (time-bound events)
/reflections/   - Emotional/diary notes (time-bound events)
/hubs/          - Conceptual gathering places (long-lived)
/sources/       - External material (immutable after capture)
/projects/      - Active inquiry lines (temporary)
/archive/       - Frozen snapshots (immutable)
```

---

## Core Entity Types

### 1. Note (Event Entity)

**Definition**: A time-bound snapshot of attention at a specific moment.

**File Location**: `/notes/` or `/reflections/`

**Naming Convention**: `YYYY-MM-DD--slug.md`

**Data Model**:
```yaml
---
type: note | reflection
status: raw | processed | evolving | evergreen | dormant | obsolete
created_at: ISO-8601 datetime
processed_at: ISO-8601 datetime (optional)
captured_from: mobile | desktop-work | desktop-home | telegram | unknown
capture_mode: quick | extended | voice | image (optional)
tags: [list of tags]
hubs: [list of hub references] (optional)
emotional_context: string (optional)
certainty: low | medium | high (optional)
---
```

**Required Sections**:
- Raw Capture (verbatim original)
- All other sections optional

**Lifecycle**: Created → Processed → Dormant/Evergreen → (potential) Archive

**Immutability**: Raw capture section MUST NOT be edited after processing

---

### 2. Hub (Place Entity)

**Definition**: A long-lived conceptual gathering point for related notes.

**File Location**: `/hubs/`

**Naming Convention**: `Title Case Concept.md` (no date prefix)

**Data Model**:
```yaml
---
type: hub
status: empty | active | dormant | obsolete
created_at: ISO-8601 datetime
last_updated: ISO-8601 datetime
note_count: integer (optional, for tooling)
---
```

**Required Sections**:
- "What This Hub Is"
- "What This Hub Is Not"
- "Open Questions"
- "Linked Notes"

**Lifecycle**: Stub → Active → Dormant → (rarely) Obsolete

**Immutability**: Hubs CAN be edited throughout their lifecycle

**Distinction from Notes**:
- Hubs have no date in filename
- Hubs can evolve continuously
- Hubs serve navigation, not capture
- Hubs exist "outside time" (not event-bound)

---

### 3. Source (External Entity)

**Definition**: External material imported into the archive with full content preservation.

**File Location**: `/sources/`

**Naming Convention**: `YYYY-MM-DD--source-title.md`

**Data Model**:
```yaml
---
type: source
source_type: article | blog | wikipedia | academic | documentation | social_media | pdf | book | video | conversation
url: string (original URL if applicable)
captured_at: ISO-8601 datetime
title: string (page/article title)
domain: string (source domain)
author: string (optional)
published_at: ISO-8601 date (optional, publication date)
word_count: integer (optional)
archive_method: auto | manual | hybrid (optional)
extraction_confidence: high | medium | low (optional)
tags: [list of tags] (optional)
---
```

**Content Preservation**:
- Full content MUST be preserved in markdown format
- Original URL preserved in frontmatter for reference
- Prevents information loss due to link rot
- Content extraction should remove navigation, ads, sidebars
- Main article content should be clean and readable

**Immutability**: Sources are immutable after initial capture

**Archival Principle**: Sources store complete external material, not just references. This ensures the archive remains meaningful even if external sources disappear.

**Further details**: See `specs/24-webpage-archival.md` for complete webpage archival specification

---

### 4. Project (Temporary Lens Entity)

**Definition**: An active line of inquiry that provides a temporary organizational lens over notes.

**File Location**: `/projects/`

**Naming Convention**: `project-name.md` (no date)

**Data Model**:
```yaml
---
type: project
status: active | paused | completed | abandoned
created_at: ISO-8601 datetime
completed_at: ISO-8601 datetime (optional)
related_hubs: [list of hub references]
---
```

**Lifecycle**: Active → Paused/Completed/Abandoned → Archive

**Distinction**: Projects reference notes; they do NOT own them

---

## Link Semantics

### Link Types

**1. Note → Hub (Outward Reference)**
- Direction: Note points to Hub
- Syntax: `[[Hub Name]]` in note body
- Meaning: "This note touches on this concept"
- Cardinality: One note → Many hubs (0..*)
- Required: No (but recommended during processing)

**2. Hub → Note (Backlink)**
- Direction: Hub lists Note
- Syntax: List item in "## Linked Notes" section
- Format: `- [[YYYY-MM-DD--slug]] - brief description`
- Meaning: "This hub gathers these notes"
- Maintenance: Manual or semi-automated
- Required: No automatic population in stubs

**3. Note → Note (Cross-reference)**
- Direction: Bidirectional semantic link
- Syntax: `[[YYYY-MM-DD--slug]]` in note body
- Meaning: "These thoughts connect"
- Cardinality: Many-to-many
- Required: No

**4. Note → Source (Attribution)**
- Direction: Note points to Source
- Syntax: `[[YYYY-MM-DD--source-title]]`
- Meaning: "This note responds to external material"
- Cardinality: One note → Many sources (0..*)
- Required: Only when note derives from source

**5. Project → Note (Inclusion)**
- Direction: Project points to Note
- Syntax: List item in project file
- Meaning: "This note is relevant to this inquiry"
- Distinction: Inclusion does NOT imply ownership
- Cardinality: One project → Many notes

---

## Graph Structure

### Graph Type: Directed Acyclic Graph (DAG) with Cycles Allowed

**Nodes**: Notes, Hubs, Sources, Projects

**Edges**: Links (typed by relationship)

**Properties**:
- **Directed**: Links have direction (note → hub, hub → note)
- **Typed**: Each edge has semantic meaning
- **Weighted**: No (all links equal)
- **Cycles Allowed**: Yes (notes can reference each other cyclically)
- **Disconnected Nodes Allowed**: Yes (not all notes must link to hubs)

### Traversal Semantics

**Forward Traversal (Note → Hub)**:
- Start at note
- Follow outward links to hubs
- Discover conceptual context

**Backward Traversal (Hub → Note)**:
- Start at hub
- Follow inward links to notes
- Discover temporal instances

**Temporal Traversal (Chronological)**:
- Navigate by date
- Independent of graph structure

**Thematic Traversal (Tag-based)**:
- Navigate by tag
- Independent of graph structure

### Constraints

**Hard Constraints**:
- Hub filenames MUST NOT contain dates
- Note filenames MUST contain dates
- Raw capture sections MUST NOT be edited
- Hub stubs MUST NOT pre-populate content

**Soft Constraints**:
- Most notes SHOULD link to at least one hub (but not required)
- Hubs SHOULD maintain backlinks (but not automatically)
- Contradictory notes SHOULD be cross-linked (but not required)

---

## Metadata Requirements

### Required Frontmatter (All Types)
```yaml
type: <entity-type>
created_at: <ISO-8601>
```

### Recommended Frontmatter (Notes)
```yaml
status: <status-value>
captured_from: <surface>
tags: [<tags>]
```

### Optional Frontmatter (Context-Dependent)
```yaml
processed_at: <ISO-8601>
capture_mode: <mode>
emotional_context: <string>
certainty: <level>
hubs: [<hub-list>]
```

---

## Validation Rules

### Filename Validation
- Notes/Reflections: Must match `YYYY-MM-DD--*.md`
- Hubs: Must NOT match date pattern
- Sources: Must match `YYYY-MM-DD--*.md`
- Projects: No date requirement

### Frontmatter Validation
- `type` field is required
- `created_at` field is required
- `status` values must be from defined ontology
- ISO-8601 dates must parse correctly

### Content Validation
- Notes must contain "## Raw Capture" section
- Hubs must contain required sections
- Markdown must be valid

### Link Validation
- Internal links should resolve to existing files
- Broken links are warnings, not errors
- Circular references are allowed

---

## Uniqueness and Identity

### Note Identity
- **Primary Key**: Filename (date + slug)
- **Stable**: Yes (filenames should not change)
- **Collisions**: Date + slug must be unique

### Hub Identity
- **Primary Key**: Filename (concept name)
- **Stable**: Yes (hub names should not change)
- **Collisions**: Concept names must be unique
- **Renaming**: Requires link updates across archive

### Tag Identity
- **Primary Key**: Tag string
- **Stable**: No (tags may evolve or decay)
- **Collisions**: Same tag string = same concept

---

## Success Criteria

This data model succeeds if:
- All entities can be parsed programmatically
- The archive remains human-readable
- Links can be validated and traversed
- Tools can be built without schema changes
- The system works with standard file tools

This data model fails if:
- Special software is required to read the archive
- Link semantics are ambiguous
- Entity types become confused
- The model constrains organic growth

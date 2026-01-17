# Note and Hub Lifecycle Specification

## Purpose

This document defines operational lifecycle states, transitions, and triggers for notes and hubs.

---

## Note Lifecycle

### 1. Capture

**State**: `status: raw`

**Entry**: Note is created in `/inbox/` or directly in `/notes/` or `/reflections/`

**Characteristics**:
- Contains raw capture text (verbatim)
- Minimal or no metadata
- May lack structure
- Immutable after initial save

**Duration**: Until processed (no time limit)

**Exit Trigger**: User or automation initiates processing

---

### 2. Context Encoding

**State**: Still `status: raw` (in-progress)

**Activities**:
- Add frontmatter metadata
- Record capture surface
- Record timestamp
- Record emotional context (if applicable)
- Record certainty level (if applicable)

**Constraints**:
- MUST NOT edit raw capture text
- MUST preserve original content

**Exit Trigger**: Context is encoded

---

### 3. Initial Processing

**State**: Transitions to `status: processed`

**Activities**:
- Add interpretation sections
- Identify themes
- Suggest related hubs (do not force)
- Add tags (optional)
- Cross-reference related notes (optional)

**Required Sections After Processing**:
- Raw Capture (unchanged)
- Context (optional but recommended)
- Initial Interpretation (optional but recommended)
- Themes (optional)
- Related Hub Notes (optional)

**Constraints**:
- Raw capture section remains verbatim
- Processing is additive, not substitutive
- Uncertainty is preserved
- Multiple interpretations allowed

**File Movement**: If in `/inbox/`, move to `/notes/` or `/reflections/`

**Exit Trigger**: Processing complete, note is readable

---

### 4. Linking to Existing Hubs

**State**: `status: processed` or `status: evolving`

**Activities**:
- Add `[[Hub Name]]` links in interpretation sections
- Optionally add to hub backlink lists
- Do NOT force hub attachment

**Timing**: During processing OR later retrospectively

**Exit Trigger**: Links added (or decision made not to link)

---

### 5. Active Evolution

**State**: `status: evolving`

**Entry Trigger**: Note is revisited and expanded

**Activities**:
- Add new interpretation sections (dated)
- Add cross-references to newer notes
- Expand context
- Add tags

**Constraints**:
- Raw capture MUST NOT change
- Original sections preserved
- New additions clearly marked with date

**Duration**: While note is being actively reconsidered

**Exit Trigger**: Evolution stops; note stabilizes

---

### 6. Dormancy

**State**: `status: dormant`

**Definition**: Note is no longer actively referenced or linked to, but remains in archive

**Entry Trigger**:
- Note hasn't been referenced in 12+ months (heuristic)
- Topic no longer active in recent captures
- User manually marks as dormant

**Characteristics**:
- Note is not deleted
- Note is findable by search
- Note may re-emerge

**Distinguishing Features**:
- Dormancy is NOT archival (remains in `/notes/`)
- Dormancy is NOT obsolete (still valid)
- Dormancy is temporal, not judgmental

**Exit Trigger**: Re-emergence

---

### 7. Re-emergence

**State**: Transitions from `dormant` back to `processed` or `evolving`

**Entry Trigger**:
- Note is referenced in new capture
- User searches for and revisits note
- Related concept becomes active again

**Activities**:
- Add re-emergence annotation (date)
- Link to new notes that prompted re-emergence
- Update hubs if needed

**Principle**: Re-emergence validates temporal architecture

---

### 8. Evergreen Status

**State**: `status: evergreen`

**Definition**: Note contains understanding that remains relevant across time

**Entry Trigger**:
- Note is referenced consistently over 12+ months
- Note forms foundation for other notes
- User manually designates as evergreen

**Characteristics**:
- Higher findability
- May be linked from hub "core references"
- Subject to periodic re-interpretation

**Distinguishing Features**:
- Evergreen ≠ unchanging (can still evolve)
- Evergreen ≠ authoritative (still interpretive)
- Evergreen = persistently relevant

---

### 9. Re-interpretation

**State**: `status: evolving` (re-entered)

**Entry Trigger**:
- User revisits old note with new perspective
- Contradictory new note prompts review
- Automated suggestion flags inconsistency

**Activities**:
- Add new dated section
- Cross-link contradictory notes
- Update hub links if needed
- DO NOT resolve contradiction

**Principle**: Contradictions are features, not bugs

---

### 10. Archival

**State**: Note moves to `/archive/` directory

**Definition**: Note is frozen as a historical snapshot of a time period

**Entry Trigger**:
- User explicitly archives a project's notes
- System-wide periodic archival (e.g., yearly)
- Note is part of completed project

**Characteristics**:
- Immutable
- No longer processed or linked
- Preserved for historical reading
- Not searchable in active archive (optional)

**Distinguishing Features**:
- Archival ≠ dormant (fully frozen)
- Archival ≠ deleted (preserved)
- Archival = end of active lifecycle

---

### 11. Obsolescence

**State**: `status: obsolete`

**Definition**: Note's content is no longer valid or relevant

**Entry Trigger**:
- Information is factually superseded
- User explicitly marks obsolete
- Interest permanently ended

**Activities**:
- Add obsolescence notice (date + reason)
- Maintain in archive (do not delete)
- Remove from active hub backlinks

**Principle**: Obsolete notes remain for history

---

## Hub Lifecycle

### 1. Stub Creation

**State**: `status: empty`

**Entry Trigger**:
- Multiple notes reference non-existent concept
- User explicitly creates hub
- Automation suggests hub (requires approval)

**Content**:
- Required sections (empty)
- No backlinks
- No questions
- No content

**Duration**: Until first note is linked

---

### 2. Initial Population

**State**: Transitions to `status: active`

**Entry Trigger**: First note is linked to hub

**Activities**:
- Add first backlink
- Begin open questions section (optional)
- Add brief description (optional)

**Constraints**:
- Do NOT summarize notes
- Do NOT assert single definition
- Keep open and incomplete

---

### 3. Active Growth

**State**: `status: active`

**Characteristics**:
- Notes are regularly added
- Backlinks list grows
- Open questions evolve
- Hub is referenced in new captures

**Activities**:
- Maintain backlinks
- Add new questions
- Organize backlinks (optional)
- Cross-link to related hubs

**Duration**: While concept remains active in captures

---

### 4. Hub Dormancy

**State**: `status: dormant`

**Entry Trigger**:
- No new notes linked in 12+ months
- Concept no longer appears in captures
- User manually marks dormant

**Characteristics**:
- Hub remains in `/hubs/`
- Backlinks preserved
- Still findable
- May re-emerge

**Distinguishing Features**:
- Dormancy ≠ obsolete (concept still valid)
- Dormancy = temporal gap in interest

---

### 5. Hub Re-emergence

**State**: Returns to `status: active`

**Entry Trigger**:
- Concept reappears in new notes
- Related concept becomes active
- User revisits and updates

---

### 6. Hub Obsolescence

**State**: `status: obsolete`

**Entry Trigger**:
- Concept merged into another hub
- Concept no longer valid
- Wording drift resolved

**Activities**:
- Add obsolescence notice
- Redirect to replacement hub (if applicable)
- Preserve historical backlinks

**Principle**: Hubs are rarely obsolete (very high bar)

---

## State Transition Diagram

### Note States
```
raw → processed → evolving ⇄ evergreen
         ↓            ↓
      dormant → re-emergence
         ↓
      obsolete / archival
```

### Hub States
```
empty → active ⇄ dormant → obsolete
```

---

## Hub Formation Rule

A hub is created only when multiple notes naturally converge around a shared conceptual gravity.

Hubs are discovered, not planned.

**Minimum Criteria** (see `hub-promotion-criteria.md`):
- Concept appears in 3+ notes, OR
- Concept is referenced but doesn't exist, OR
- User explicitly requests hub creation

---

## Automation Boundaries

**Automated Transitions Allowed**:
- raw → processed (with human review)
- active → dormant (time-based heuristic)

**Automated Transitions Prohibited**:
- dormant → obsolete (requires human judgment)
- Note creation without capture
- Hub creation without approval

---

## Success Criteria

This lifecycle spec succeeds if:
- State transitions have clear triggers
- Dormancy is operationally defined
- Re-emergence is supported
- Contradictions are preserved through transitions
- Tools can implement state management

This lifecycle spec fails if:
- States are still ambiguous
- Triggers are subjective
- Automation boundaries unclear

# User Interaction Model

## Purpose

This document defines how users interact with the archive system across different interfaces and tools.

---

## Interaction Surfaces

### 1. Mobile Capture (Primary)

**Interface**: Telegram Bot

**Use Case**: Quick captures on-the-go

**Actions**:
- Send text message → creates raw capture
- Send voice message → transcribed and captured
- Send image → stored and linked
- Send article link → fetched and captured as source

**Characteristics**:
- Zero friction
- Minimal formatting
- Immediate capture
- No processing required

**Output**: Creates file in `/inbox/` or directly in `/notes/`

---

### 2. Desktop Capture (Extended)

**Interface**: Text editor (VS Code, Obsidian, etc.)

**Use Case**: Longer reflections and extended thinking

**Actions**:
- Create markdown file directly
- Write in editor of choice
- Add frontmatter manually
- Save to repository

**Characteristics**:
- More deliberate
- Formatted writing
- Immediate control
- Full markdown support

**Output**: Creates file in `/notes/`, `/reflections/`, or `/hubs/`

---

### 3. Processing Interface

**Interface**: AI assistant (Claude via API or web)

**Use Case**: Process raw captures into structured notes

**Actions**:
- Review inbox captures
- Add structure and metadata
- Suggest tags and hubs
- Move to appropriate folder

**Characteristics**:
- Batch processing
- AI-assisted interpretation
- Metadata enrichment
- Link suggestion

**Output**: Moves files from `/inbox/` to `/notes/` or `/reflections/`

---

### 4. Navigation Interface

**Interface**: File browser, Obsidian graph, or custom tool

**Use Case**: Browse and explore archive

**Actions**:
- Navigate folder structure
- Follow links between notes
- Search by tag or keyword
- View chronologically or thematically

**Characteristics**:
- Read-only (mostly)
- Exploratory
- Graph visualization (optional)
- Multiple entry points

**Output**: Enhanced understanding of archive

---

### 5. Maintenance Interface

**Interface**: Scripts, AI assistant, or manual editing

**Use Case**: Hub maintenance, link updates, status changes

**Actions**:
- Update hub backlinks
- Mark dormant notes
- Detect broken links
- Archive old notes

**Characteristics**:
- Periodic (not daily)
- Semi-automated
- Structural work
- Bulk operations

**Output**: Updated metadata and links

---

## Capture Workflows

### Mobile Quick Capture

```
User → Telegram message
  ↓
Bot receives message
  ↓
Creates markdown file in /inbox/
  ↓
File waits for processing
```

**Latency**: < 1 second

**User Effort**: Minimal (type and send)

---

### Desktop Extended Capture

```
User → Opens text editor
  ↓
Writes markdown note
  ↓
Adds frontmatter
  ↓
Saves to /notes/ or /reflections/
  ↓
(Optional) Runs processing assistant
```

**Latency**: Immediate (user-controlled)

**User Effort**: Moderate (deliberate writing)

---

### Bulk Processing

```
User → Requests processing
  ↓
AI assistant reads /inbox/
  ↓
For each file:
  - Add structure
  - Suggest tags/hubs
  - Add metadata
  ↓
Move to /notes/ or /reflections/
  ↓
User reviews changes
```

**Latency**: Minutes (batch operation)

**User Effort**: Moderate (review and approval)

---

## Navigation Patterns

### Chronological Navigation

**Entry Point**: Browse `/notes/` by date

**Use Case**: "What was I thinking about last week?"

**Path**: Date → Note → Related Notes

**Tools**: File browser, file naming convention

---

### Thematic Navigation

**Entry Point**: Start at hub

**Use Case**: "What have I captured about memory?"

**Path**: Hub → Backlinked Notes → Cross-references

**Tools**: Hub files, backlinks list

---

### Tag-Based Navigation

**Entry Point**: Search by tag

**Use Case**: "What was I curious about?"

**Path**: Tag → Tagged Notes → Related Hubs

**Tools**: Grep, Obsidian search, custom script

---

### Search-Based Navigation

**Entry Point**: Keyword search

**Use Case**: "Where did I write about that idea?"

**Path**: Search → Results → Context → Related Notes

**Tools**: grep, ripgrep, Obsidian search

---

### Graph Navigation

**Entry Point**: Visual graph view

**Use Case**: "How do these concepts connect?"

**Path**: Node → Connected Nodes → Clusters

**Tools**: Obsidian graph, custom visualization

---

## CLI Commands (Proposed)

### Capture

```bash
# Quick capture
$ brain capture "thought goes here"

# Voice capture
$ brain voice record.m4a

# Link capture
$ brain link https://example.com
```

---

### Process

```bash
# Process inbox
$ brain process

# Process specific file
$ brain process inbox/2024-01-15-capture.md

# Batch process all
$ brain process --all
```

---

### Search

```bash
# Search by keyword
$ brain search "memory"

# Search by tag
$ brain search --tag nostalgia

# Search by hub
$ brain search --hub "Memory"

# Search by date range
$ brain search --since 2024-01-01
```

---

### Navigate

```bash
# List recent notes
$ brain recent

# Show note with context
$ brain show notes/2024-01-15--note.md

# Follow links from note
$ brain links notes/2024-01-15--note.md

# Show hub contents
$ brain hub "Memory"
```

---

### Maintain

```bash
# Detect broken links
$ brain lint

# Detect dormant notes
$ brain dormant

# Update hub backlinks
$ brain update-hubs

# Archive old notes
$ brain archive --before 2023-01-01
```

---

## API Endpoints (Proposed)

### Capture

```
POST /capture
Body: { "text": "...", "surface": "mobile", "mode": "quick" }
Response: { "file": "inbox/2024-01-15-slug.md" }
```

---

### Process

```
POST /process/:filename
Body: { "add_tags": true, "suggest_hubs": true }
Response: { "file": "notes/2024-01-15-slug.md", "suggestions": {...} }
```

---

### Search

```
GET /search?q=memory&type=note
Response: { "results": [...] }
```

---

### Navigate

```
GET /note/:filename
Response: { "content": "...", "links": [...], "backlinks": [...] }

GET /hub/:hubname
Response: { "content": "...", "backlinked_notes": [...] }
```

---

## UI Concepts (Proposed)

### Capture UI

**Mobile**:
- Telegram chat interface
- Single input field
- Immediate send
- No preview needed

**Desktop**:
- Markdown editor pane
- Frontmatter helper
- Tag autocomplete
- Hub link suggestions

---

### Processing UI

**Inbox View**:
- List of unprocessed captures
- Preview pane
- Metadata form
- Tag/hub suggestion panel
- Batch actions

---

### Navigation UI

**Note View**:
- Markdown rendering
- Metadata sidebar
- Backlinks list
- Related notes
- Hub breadcrumbs

**Hub View**:
- Hub description
- Backlinked notes (chronological or thematic)
- Related hubs
- Open questions
- Note count statistics

**Graph View**:
- Visual node-link diagram
- Filter by type (notes, hubs, sources)
- Filter by date range
- Filter by tag
- Click to navigate

---

## Interaction Modes

### 1. Capture Mode

**Goal**: Get thoughts out of head into system

**Principle**: Zero friction

**User Mindset**: Urgent, fleeting, immediate

**Tools**: Telegram, quick-capture CLI

---

### 2. Processing Mode

**Goal**: Structure and enrich raw captures

**Principle**: Thoughtful interpretation

**User Mindset**: Deliberate, reflective, patient

**Tools**: AI assistant, text editor, processing UI

---

### 3. Navigation Mode

**Goal**: Find and explore existing notes

**Principle**: Multiple paths to discovery

**User Mindset**: Curious, exploratory, meandering

**Tools**: Search, graph, chronological browse

---

### 4. Reflection Mode

**Goal**: Write extended, emotional, diary-style notes

**Principle**: Preserve subjective experience

**User Mindset**: Vulnerable, introspective, expressive

**Tools**: Desktop editor, private space

---

### 5. Maintenance Mode

**Goal**: Keep system healthy and navigable

**Principle**: Curate without controlling

**User Mindset**: Gardening, organizing, tidying

**Tools**: Scripts, bulk operations, hub maintenance

---

## Interaction Principles

### 1. Minimize Friction at Capture

Capture must be effortless. Any barrier reduces captures.

---

### 2. Maximize Thoughtfulness at Processing

Processing is where interpretation happens. Don't rush it.

---

### 3. Support Serendipity in Navigation

Discovery should feel exploratory, not deterministic.

---

### 4. Respect Privacy in Reflection

Emotional notes need safe, private space.

---

### 5. Automate Maintenance (With Oversight)

Structural work should be assisted but not fully automated.

---

## Keyboard Shortcuts (Proposed)

If building a UI:

```
Capture
- Cmd+N: New note
- Cmd+Shift+N: New reflection
- Cmd+K: Quick capture

Processing
- Cmd+P: Process current note
- Cmd+T: Add tags
- Cmd+H: Link to hub

Navigation
- Cmd+O: Open note
- Cmd+F: Search
- Cmd+G: Graph view
- Cmd+B: Show backlinks
- Cmd+L: Follow link
- Cmd+[: Back
- Cmd+]: Forward

Editing
- Cmd+S: Save
- Cmd+E: Edit metadata
- Cmd+D: Mark dormant
```

---

## Hooks and Integrations

### Git Hooks (Proposed)

```bash
# Pre-commit: Validate frontmatter
.git/hooks/pre-commit

# Post-commit: Update hub indices
.git/hooks/post-commit

# Pre-push: Run lint checks
.git/hooks/pre-push
```

---

### Telegram Integration (Current)

```
User message → Telegram API → Bot
  ↓
Bot creates markdown file
  ↓
File committed to git
  ↓
Processing triggered (optional)
```

---

### Obsidian Integration (Proposed)

- Use Obsidian as viewer/editor
- Respect folder structure
- Use standard markdown links
- Dataview queries for dynamic views

---

### VS Code Integration (Proposed)

- Markdown preview
- Frontmatter snippets
- Link autocomplete
- Tag autocomplete

---

## Success Criteria

This interaction model succeeds if:
- Capture feels effortless
- Processing feels thoughtful
- Navigation feels exploratory
- Tools feel invisible
- User stays in flow

This interaction model fails if:
- Capture has friction
- Processing feels obligatory
- Navigation feels prescriptive
- Tools dominate experience
- User fights the system

---

## Summary

**Capture should disappear.**
**Processing should assist.**
**Navigation should enable.**
**Tools should serve.**

The user's attention is primary; interfaces should never obstruct it.

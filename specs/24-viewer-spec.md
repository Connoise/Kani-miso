# Specification: Kani-miso Web Viewer

> **Version**: 1.0
> **Status**: Draft
> **Purpose**: Define a lightweight, read-only web viewer for the Kani-miso vault.

---

## 1. Overview

The **Web Viewer** is a Flask-based web application that provides browser-based access to the Kani-miso vault. It complements the existing Tauri desktop application by offering:

- **Zero-install access** via any modern browser
- **Lightweight deployment** (Python + Flask, no Node.js build step)
- **Wikipedia-style reading experience** optimized for navigating linked notes
- **Interactive graph visualization** using D3.js

### Design Principles

1. **Read-only by default** — Never modifies vault files
2. **Links are primary structure** — UI emphasizes navigation via wikilinks
3. **Notes are events, hubs are places** — Timeline for notes, atlas for hubs
4. **Graceful degradation** — Missing data handled, not hidden
5. **Minimal dependencies** — Flask, Jinja2, SQLite (all stdlib-friendly)

---

## 2. Wikipedia-Style UI Rationale

The interface draws inspiration from Wikipedia's design:

| Wikipedia Pattern | Application Here |
|-------------------|------------------|
| Clean content area with sidebar | Note content + hub navigation sidebar |
| Prominent internal links (blue) | Wikilinks styled distinctly |
| "See also" sections | Related notes via shared hubs |
| Table of contents | Auto-generated from headings |
| History/revisions | Timeline view of note changes |
| Categories | Hubs as conceptual categories |

**Why Wikipedia?**
- Users already understand the interaction model
- Link-heavy content benefits from clean typography
- Navigation patterns match Kani-miso philosophy

---

## 3. Data Model

The viewer reuses the vault structure defined in the main project. No new data formats are introduced.

### Entity Types (from CLAUDE.md)

| Type | Location | Filename Pattern | Description |
|------|----------|------------------|-------------|
| Note | `/notes/` | `YYYY-MM-DD--slug.md` | Time-bound observations |
| Reflection | `/reflections/` | `YYYY-MM-DD--slug.md` | Diary-style emotional/subjective entries |
| Hub | `/hubs/` | `Title Case.md` | Persistent conceptual anchors |
| Source | `/sources/` | `YYYY-MM-DD--source-title.md` | External materials |
| Project | `/projects/` | `project-name.md` | Active inquiry lines |
| Archive | `/archive/` | Various patterns | Frozen snapshots (immutable) |

### Entity Display Rules

**Reflections**:
- Displayed with same styling as notes in all views
- Distinguished only by `type: reflection` in metadata
- Can be filtered via type selector in timeline and search
- No special visual treatment (user preference for unified view)

**Projects**:
- Browsable via `/projects` route (Project Atlas view)
- Project detail page shows active/paused/completed status
- Lists linked notes and related hubs
- Project cards show status badge and note count

**Sources**:
- Browsable via `/sources` route (Source Atlas view)
- Filterable by `source_type` (article, pdf, book, video, etc.)
- Source detail page shows which notes reference it (backlinks)
- Display metadata: author, URL, captured date

**Archive**:
- Archived content included in main timeline
- Distinguished by `archived` badge on timeline cards
- Can be filtered out via "Hide archived" checkbox (default: shown)
- Search results include archived content but marked as [ARCHIVED]

### Frontmatter Schema

Viewer reads but never writes frontmatter. See `CLAUDE.md` for full schema. Key fields:

```yaml
type: note | reflection | hub | source | project
status: raw | processed | evolving | evergreen | dormant | obsolete
created_at: ISO-8601
hubs: []  # For notes: linked hub names
```

### Link Types

- `[[wikilink]]` — Internal vault link
- `[[target|alias]]` — Aliased link (display alias, navigate to target)
- `[[note#section]]` — Section anchor (see "Section Anchor Generation" below)
- `[text](url)` — External link (opens in new tab)

### Link Resolution Rules

**Case Sensitivity**:
- Wikilink matching is **case-insensitive**
- `[[Machine Learning]]` and `[[machine learning]]` resolve to same file
- Implementation: normalize both link target and filenames to lowercase for lookup
- Display uses original case from link text or filename

**Dead Link Detection**:
- A link is "dead" if no matching file exists in the vault after case-insensitive lookup
- Check all entity folders: `/notes/`, `/reflections/`, `/hubs/`, `/sources/`, `/projects/`, `/archive/`
- For date-based links, try both `YYYY-MM-DD--slug.md` pattern and title-only lookup
- Dead links rendered with:
  - CSS class: `dead-link`
  - Style: red text, dashed underline
  - No href (non-clickable)
  - Tooltip: "Target not found"

**Section Anchor Generation**:
- Markdown headings (`## Heading Text`) become anchors
- Slugification rules:
  1. Convert to lowercase
  2. Replace spaces with hyphens
  3. Remove punctuation except hyphens and underscores
  4. Example: `## What This Hub Is` → `#what-this-hub-is`
- Duplicate heading names get numeric suffix: `#heading-1`, `#heading-2`
- Section links `[[note#section]]` scroll to anchor on page load

### Graph Model

- **Directed edges** with arrows showing link direction
  - Note→Hub: Arrow points from note to hub (outward reference)
  - Hub→Note: Arrow points from hub to note (inward backlink)
  - Note→Note: Arrow shows reference direction
- **Edge rendering**: SVG arrows or D3.js markers, colored by source node type
- **Cycles allowed** (notes can link bidirectionally)
- **Disconnected nodes** rendered but visually distinct (lighter opacity)
- **Hub-centric clustering** — Hubs act as gravitational centers using stronger attractive force:
  - Hub nodes: `forceManyBody().strength(-400)` (stronger repulsion, keeps them spaced)
  - Regular link distance: 80px
  - Hub-connected links: 100px (gives hubs more space)
  - Hubs positioned with additional `forceRadial()` to spread evenly

---

## 4. UI Views

### 4.1 Timeline View (`/timeline`)

**Purpose**: Browse notes chronologically, filter by metadata.

**Features**:
- All time-bound entities ordered by `created_at` descending
- Entity types shown: notes, reflections, sources, archived content
- Filters:
  - **Type**: note, reflection, source (multi-select)
  - **Status**: raw, processed, evolving, evergreen, dormant, obsolete
  - **Hub**: dropdown of all hubs
  - **Date range**: from/to date pickers
  - **Show archived**: checkbox (default: checked)
- Pagination: 20 items per page or infinite scroll
- Compact preview: title, date, first 100 chars, hub badges, type indicator

**Rendering**:
```
[2024-01-15] [Note] Initial thoughts on project X
              Hubs: [project-management] [ideas]
              Status: raw
              "Started thinking about how to approach..."

[2023-12-10] [Reflection] Feeling overwhelmed today
              Status: processed
              "The weight of too many decisions..."

[2023-12-01] [Source] Article: The Nature of Time
              Author: Carlo Rovelli | Type: article
              "Captured from physics blog..."

[2022-05-15] [Note] [ARCHIVED] Old project notes
              Status: obsolete
              "Historical snapshot from old system..."
```

### 4.2 Hub Atlas (`/hubs`)

**Purpose**: Navigate the conceptual landscape via hubs.

**Features**:
- Grid/list of all hubs with note counts
- Sort by: name, note count, last updated
- Hub detail page shows:
  - Hub content (markdown rendered)
  - Linked notes grouped by time period
  - Related hubs (hubs that share notes)

**Hub Detail Layout**:
```
┌─────────────────────────────────────┐
│ Hub: Machine Learning               │
│ Status: active | 47 linked notes    │
├─────────────────────────────────────┤
│ [Hub content rendered as markdown]  │
├─────────────────────────────────────┤
│ Linked Notes:                       │
│   This Week (3)                     │
│   This Month (12)                   │
│   Older (32)                        │
├─────────────────────────────────────┤
│ Related Hubs: [AI] [Python] [Math]  │
└─────────────────────────────────────┘
```

**Temporal Grouping Algorithm**:
- **This Week**: Notes from last 7 days (inclusive of today)
- **This Month**: Notes from last 30 days, excluding "This Week"
- **Older**: All notes older than 30 days
- Within each group, sort by `created_at` descending
- Show count in parentheses for each group
- Collapse "Older" by default if count > 20

**Related Hubs Computation**:
- Two hubs are "related" if they share at least one note
- Algorithm:
  1. Get all notes linked to current hub
  2. For each note, find all other hubs it links to
  3. Count occurrences of each other hub
  4. Rank by count descending
  5. Display top 5 related hubs
- Threshold: Only show hubs with 2+ shared notes
- Display format: `[Hub Name (N shared)]` where N is count

### 4.3 Graph Explorer (`/graph`)

**Purpose**: Visualize note-hub relationships interactively.

**Technology**: D3.js force-directed graph

**Features**:
- **Full graph view**: All nodes, clustered by hub
- **Local neighborhood**: Start from a node, expand 1-3 hops
- **Node types visually distinct**:
  - Hubs: larger circles, bold color
  - Notes: smaller circles, colored by status
  - Sources: square nodes
  - Dead links: dashed outline
- **Interactions**:
  - Click node → open in reader pane
  - Hover → show tooltip with title/date
  - Drag → reposition nodes
  - Scroll → zoom
  - Double-click hub → filter to hub neighborhood
- **Controls**:
  - Depth slider (1-3 hops)
  - Filter by type/status
  - Search to center on node
  - Reset layout button

**D3.js Configuration**:
```javascript
// Force simulation parameters with hub-centric clustering
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links)
    .id(d => d.id)
    .distance(d => {
      // Hub-connected links get more space
      return (d.source.type === 'hub' || d.target.type === 'hub') ? 100 : 80;
    }))
  .force("charge", d3.forceManyBody()
    .strength(d => d.type === 'hub' ? -400 : -200))  // Stronger repulsion for hubs
  .force("center", d3.forceCenter(width/2, height/2))
  .force("collision", d3.forceCollide()
    .radius(d => d.type === 'hub' ? 25 : 15));  // Larger collision radius for hubs

// Optional: Radial force to spread hubs evenly
const hubNodes = nodes.filter(d => d.type === 'hub');
if (hubNodes.length > 0) {
  simulation.force("radial", d3.forceRadial()
    .radius(200)
    .strength(d => d.type === 'hub' ? 0.1 : 0));
}
```

**Performance Warning**:
- Display warning if graph contains >5,000 nodes
- Suggest using filters or local neighborhood view
- Warning text: "Large graph detected (N nodes). Consider filtering by hub or using local view for better performance."

### 4.4 Reader View (`/note/<path>`)

**Purpose**: Read individual notes with full formatting.

**Features**:
- Markdown rendered to HTML (CommonMark + extensions)
- Wikilinks converted to internal hrefs
- Auto-generated table of contents from headings (links to section anchors)
- Sidebar:
  - Metadata panel (type, status, created, hubs)
  - Backlinks (notes that link to this one)
  - "Open in Obsidian" button with obsidian:// URI
- Code blocks with syntax highlighting
- Images rendered inline (relative paths resolved)

**Image Path Resolution**:
- Relative image paths resolved relative to note's file location
- Example: Note at `/notes/2024-01-15--test.md` with `![img](../assets/photo.jpg)`
  - Resolves to: `/assets/photo.jpg` from vault root
- Absolute paths from vault root: `/assets/photo.jpg` → served from vault
- External URLs: `![img](https://...)` → passed through unchanged
- Security: All resolved paths validated to be within vault directory

**Obsidian URI Format**:
- Button text: "Open in Obsidian"
- URI format: `obsidian://open?vault={vault_name}&file={file_path}`
  - `vault_name`: URL-encoded vault name (from config or detected)
  - `file_path`: URL-encoded relative path from vault root
  - Example: `obsidian://open?vault=My%20Notes&file=notes%2F2024-01-15--test.md`
- Falls back to showing file path if vault name not configured
- Button opens link in new tab/window (browser handles obsidian:// protocol)

**Layout**:
```
┌──────────┬─────────────────────────────┐
│ Metadata │                             │
│ ──────── │  [Note Content]             │
│ Type:    │                             │
│ Status:  │  # Heading                  │
│ Created: │                             │
│ Hubs:    │  Paragraph with [[links]]   │
│          │  and regular text...        │
│ ──────── │                             │
│ Backlinks│                             │
│ ──────── │                             │
│ • Note A │                             │
│ • Note B │                             │
│          │                             │
│ [Obsidian]│                            │
└──────────┴─────────────────────────────┘
```

### 4.5 Project Atlas (`/projects`)

**Purpose**: Browse and navigate active inquiry projects.

**Features**:
- Grid/list view of all projects
- Filter by status: active, paused, completed, abandoned
- Sort by: name, created date, status
- Project cards show:
  - Project name and status badge
  - Created/completed dates
  - Note count (how many notes linked to project)
  - Related hubs (from frontmatter)

**Project Detail Page** (`/project/<project-name>`):
- Project content rendered as markdown
- Status indicator with visual badge
- **Linked Notes** section:
  - All notes referenced in project file
  - Grouped by time period (same as Hub detail)
  - Clicking note navigates to reader view
- **Related Hubs** section:
  - Hubs listed in `related_hubs` frontmatter field
  - Click to navigate to hub page
- **Timeline** section:
  - Project creation date
  - Completion date (if applicable)
  - Last note added date

### 4.6 Source Atlas (`/sources`)

**Purpose**: Browse external materials imported into the archive.

**Features**:
- List view of all sources ordered by `captured_at` descending
- Filter by `source_type`:
  - article, pdf, book, video, conversation, wikipedia
  - Multi-select allowed
- Source cards show:
  - Source title and type badge
  - Author (if available)
  - Captured date
  - URL (if available) as clickable external link
  - Reference count (how many notes link to this source)

**Source Detail Page** (`/source/<source-path>`):
- Source content rendered as markdown
- Metadata panel:
  - Type, author, URL, captured date
  - Tags from frontmatter
- **Backlinks** section:
  - All notes that reference this source
  - Grouped by time period
  - Preview snippet showing context of reference
- "Open External Link" button (if URL present)

### 4.7 Search (`/search`)

**Purpose**: Full-text search across all vault content.

**Technology**: SQLite FTS5

**Features**:
- Query syntax: simple terms, phrases, boolean operators
- Results ranked by relevance (BM25)
- Snippet preview with highlighted matches
- Filters: type, status, hub, date range
- Search-as-you-type with debouncing (300ms delay)

**Snippet Generation**:
- Length: 150 characters around first match
- Context: 50 characters before + match + remaining to 150 chars
- Multiple matches in same note: Show snippet for best-ranked match only
- Highlight format: `<mark class="search-highlight">matched text</mark>`
- Ellipsis: Add "..." at start/end if snippet doesn't include note boundaries
- Archived results: Prepend `[ARCHIVED]` tag to title
- Example: `"...discovered the concept of [[Machine Learning]] which connects to..."`

**Index Schema**:
```sql
CREATE VIRTUAL TABLE notes_fts USING fts5(
  title,
  content,
  path UNINDEXED,
  type UNINDEXED,
  created_at UNINDEXED,
  content='notes',
  content_rowid='id'
);
```

---

## 5. Read-Only Constraints

The viewer **must never**:

1. Write to vault files
2. Create new notes or hubs
3. Modify frontmatter
4. Delete or rename files
5. Alter folder structure

The viewer **may**:

1. Create/update SQLite index database (in separate location)
2. Cache rendered HTML (memory only)
3. Store user preferences (browser localStorage)

### File Access Pattern

```python
# All vault access is read-only
with open(note_path, 'r', encoding='utf-8') as f:
    content = f.read()
# Never: open(path, 'w'), os.remove(), shutil.move()
```

---

## 6. Configuration

The viewer reads the existing `config.yaml` from the Kani-miso system.

### Required Config Fields

```yaml
vault:
  path: "C:\\Users\\...\\Obsidian Notes"  # Vault root
  name: "My Kani-miso"  # Vault name for Obsidian URIs (optional)

viewer:  # Optional section for viewer-specific settings
  host: "127.0.0.1"      # Default: localhost only
  port: 5000             # Default: 5000
  debug: false           # Default: false
  index_path: "~/.kani-miso/viewer/index.db"  # Outside vault (read-only principle)
```

**Index Path Philosophy**:
- Default location: `~/.kani-miso/viewer/index.db` (user's home directory)
- Alternative: System temp directory
- **Never inside vault**: Preserves read-only vault principle
- Index is disposable cache, can be rebuilt anytime
- Per-vault index: Hash vault path into index filename for multi-vault support
  - Example: `~/.kani-miso/viewer/index-{vault_hash}.db`

### Config Loading

```python
def load_config():
    config_paths = [
        Path.home() / '.kani-miso' / 'config.yaml',
        Path.cwd() / 'config.yaml',
    ]
    for path in config_paths:
        if path.exists():
            return yaml.safe_load(path.read_text())
    raise ConfigError("No config.yaml found")
```

---

## 7. Error Handling

Following the project's graceful degradation philosophy:

| Error | Handling |
|-------|----------|
| Malformed YAML frontmatter | Parse what's valid, mark note as "parse warning" |
| Broken wikilink | Render as dead link (red, no href) |
| Missing vault path | Show config error page with instructions |
| File read permission denied | Skip file, log warning, continue |
| SQLite index corruption | Rebuild index on next start |
| D3.js graph too large (>5,000 nodes) | Warn user, suggest filtering or local view |

---

## 8. Security Considerations

Since this serves local files over HTTP:

1. **Bind to localhost only** by default
2. **No authentication** (assumes local user context)
3. **Sanitize markdown output** (prevent XSS in rendered HTML)
4. **Path traversal protection** (validate all file paths are within vault)
5. **No external network calls** from backend

```python
def safe_path(requested_path: str, vault_root: Path) -> Path:
    """Ensure path is within vault, prevent traversal attacks."""
    full_path = (vault_root / requested_path).resolve()
    if not str(full_path).startswith(str(vault_root.resolve())):
        raise SecurityError("Path traversal attempted")
    return full_path
```

---

## 9. Non-Goals

The web viewer intentionally **does not** support:

- Note editing or creation
- Real-time collaboration
- Cloud sync or remote vaults
- User accounts or multi-tenancy
- Mobile-optimized responsive design (desktop-focused)
- Plugin system or extensions
- Export to other formats

These features belong in the main Tauri application or Obsidian itself.

---

## 10. Success Criteria

**The viewer succeeds if**:
- Notes are findable via timeline, hub, graph, and search
- Navigation via wikilinks feels instant
- Graph visualization reveals structure not visible in linear reading
- User can quickly locate context around any note

**The viewer fails if**:
- It modifies any vault files
- Timeline/search performance degrades with <10,000 notes
- Graph becomes unusable with <5,000 nodes (warning threshold)
- Links are broken or lead to 404s for existing notes

**Performance Targets**:
- Timeline loading: <2 seconds for 10,000 notes
- Search query: <500ms for typical queries
- Graph rendering: Usable up to 5,000 nodes (with performance warning)
- Note rendering: <100ms per note

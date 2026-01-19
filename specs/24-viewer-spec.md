# Specification: Second Brain Web Viewer

> **Version**: 1.0
> **Status**: Draft
> **Purpose**: Define a lightweight, read-only web viewer for the Second Brain vault.

---

## 1. Overview

The **Web Viewer** is a Flask-based web application that provides browser-based access to the Second Brain vault. It complements the existing Tauri desktop application by offering:

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
- Navigation patterns match Second Brain philosophy

---

## 3. Data Model

The viewer reuses the vault structure defined in the main project. No new data formats are introduced.

### Entity Types (from CLAUDE.md)

| Type | Location | Filename Pattern | Description |
|------|----------|------------------|-------------|
| Note | `/notes/` | `YYYY-MM-DD--slug.md` | Time-bound observations |
| Reflection | `/reflections/` | `YYYY-MM-DD--slug.md` | Diary-style entries |
| Hub | `/hubs/` | `Title Case.md` | Persistent conceptual anchors |
| Source | `/sources/` | `YYYY-MM-DD--source-title.md` | External materials |
| Project | `/projects/` | `project-name.md` | Active inquiry lines |

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
- `[[note#section]]` — Section anchor
- `[text](url)` — External link (opens in new tab)

### Graph Model

- **Directed edges** from source note to target
- **Cycles allowed** (notes can link bidirectionally)
- **Disconnected nodes** rendered but visually distinct
- **Hub-centric clustering** — Hubs act as gravitational centers

---

## 4. UI Views

### 4.1 Timeline View (`/timeline`)

**Purpose**: Browse notes chronologically, filter by metadata.

**Features**:
- Notes ordered by `created_at` descending
- Filters: type, status, hub, date range
- Infinite scroll or pagination
- Compact preview: title, date, first 100 chars, hub badges

**Rendering**:
```
[2024-01-15] Note: Initial thoughts on project X
              Hubs: [project-management] [ideas]
              Status: raw
              "Started thinking about how to approach..."
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
// Force simulation parameters
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(80))
  .force("charge", d3.forceManyBody().strength(-200))
  .force("center", d3.forceCenter(width/2, height/2))
  .force("collision", d3.forceCollide().radius(20));
```

### 4.4 Reader View (`/note/<path>`)

**Purpose**: Read individual notes with full formatting.

**Features**:
- Markdown rendered to HTML (CommonMark + extensions)
- Wikilinks converted to internal hrefs
- Auto-generated table of contents from headings
- Sidebar:
  - Metadata panel (type, status, created, hubs)
  - Backlinks (notes that link to this one)
  - "Open in Obsidian" button (obsidian:// URI)
- Code blocks with syntax highlighting
- Images rendered inline (relative paths resolved)

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

### 4.5 Search (`/search`)

**Purpose**: Full-text search across all vault content.

**Technology**: SQLite FTS5

**Features**:
- Query syntax: simple terms, phrases, boolean operators
- Results ranked by relevance (BM25)
- Snippet preview with highlighted matches
- Filters: type, status, hub, date range
- Search-as-you-type with debouncing

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

The viewer reads the existing `config.yaml` from the Second-Brian system.

### Required Config Fields

```yaml
vault:
  path: "C:\\Users\\...\\Obsidian Notes"  # Vault root

viewer:  # Optional section for viewer-specific settings
  host: "127.0.0.1"      # Default: localhost only
  port: 5000             # Default: 5000
  debug: false           # Default: false
  index_path: ".viewer/index.db"  # Relative to vault
```

### Config Loading

```python
def load_config():
    config_paths = [
        Path.home() / '.second-brian' / 'config.yaml',
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
| D3.js graph too large | Warn user, suggest filtering |

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
- Performance degrades with >10,000 notes
- Graph becomes unusable with moderate-size vaults
- Links are broken or lead to 404s for existing notes

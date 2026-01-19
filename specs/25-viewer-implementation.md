# Implementation Guide: Second Brain Web Viewer

> **Version**: 1.0
> **Prerequisite**: Read `specs/24-viewer-spec.md` first.
> **Purpose**: Step-by-step guide for implementing the web viewer.

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Web Framework | **Flask** | Lightweight, Jinja2 built-in, Python stdlib friendly |
| Templates | **Jinja2** | Server-rendered, no build step, familiar syntax |
| Graph Visualization | **D3.js v7** | Industry standard, flexible force-directed graphs |
| Search Index | **SQLite FTS5** | Full-text search, single-file DB, proven performance |
| Markdown | **markdown-it** or **mistune** | Fast parsing, CommonMark compliant |
| YAML Parsing | **PyYAML** | Frontmatter extraction |
| CSS | **Vanilla CSS** | Wikipedia-inspired, no framework needed |

### Dependencies

```
# requirements.txt
flask>=3.0.0
pyyaml>=6.0
mistune>=3.0.0  # or markdown-it-py
watchdog>=4.0.0  # optional: file watching
```

---

## 2. Directory Structure

```
scripts/
  viewer.py              # Entry point: flask app runner
  viewer/
    __init__.py          # Flask app factory
    config.py            # Config loading from config.yaml
    routes.py            # All Flask routes
    indexer.py           # Markdown parsing, SQLite FTS indexing
    parser.py            # Frontmatter + wikilink extraction
    graph.py             # Graph data structures for D3.js
    templates/
      base.html          # Wikipedia-style layout, navigation
      timeline.html      # Chronological note listing
      hub.html           # Hub detail + linked notes
      hub_atlas.html     # All hubs overview
      note.html          # Individual note reader
      graph.html         # D3.js graph explorer
      search.html        # Search interface + results
      error.html         # Error pages (404, config error)
      _sidebar.html      # Reusable sidebar partial
      _note_card.html    # Note preview card partial
    static/
      style.css          # Wikipedia-inspired styles
      graph.js           # D3.js visualization code
      search.js          # Search-as-you-type logic
```

---

## 3. Implementation Order

Follow this sequence to build incrementally testable milestones:

### Phase 1: Foundation
1. **Config loader** (`config.py`)
   - Load `config.yaml` from standard paths
   - Validate vault path exists
   - Set defaults for viewer-specific options

2. **Basic Flask app** (`__init__.py`)
   - App factory pattern
   - Register blueprints
   - Error handlers

3. **Entry point** (`viewer.py`)
   - CLI argument parsing (--port, --debug)
   - Run Flask development server

**Milestone**: `python scripts/viewer.py` starts server, shows "Hello World"

### Phase 2: Markdown Parsing
4. **Frontmatter parser** (`parser.py`)
   - Extract YAML frontmatter from markdown
   - Handle malformed YAML gracefully
   - Parse wikilinks: `[[target]]`, `[[target|alias]]`, `[[note#section]]`

5. **Note model** (in `parser.py` or `models.py`)
   ```python
   @dataclass
   class Note:
       path: Path
       title: str
       content: str
       frontmatter: dict
       links: list[Link]
       created_at: datetime
       note_type: str
   ```

**Milestone**: Parse single note, print extracted metadata

### Phase 3: Indexing
6. **SQLite schema** (`indexer.py`)
   ```sql
   -- Core tables
   CREATE TABLE notes (
     id INTEGER PRIMARY KEY,
     path TEXT UNIQUE NOT NULL,
     title TEXT NOT NULL,
     content TEXT NOT NULL,
     type TEXT,
     status TEXT,
     created_at TEXT,
     indexed_at TEXT
   );

   CREATE TABLE links (
     id INTEGER PRIMARY KEY,
     source_id INTEGER REFERENCES notes(id),
     target_path TEXT NOT NULL,
     alias TEXT,
     is_resolved INTEGER DEFAULT 0
   );

   CREATE TABLE hubs (
     id INTEGER PRIMARY KEY,
     note_id INTEGER UNIQUE REFERENCES notes(id),
     note_count INTEGER DEFAULT 0
   );

   -- Full-text search
   CREATE VIRTUAL TABLE notes_fts USING fts5(
     title,
     content,
     content='notes',
     content_rowid='id'
   );

   -- Triggers to keep FTS in sync
   CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
     INSERT INTO notes_fts(rowid, title, content)
     VALUES (new.id, new.title, new.content);
   END;

   CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN
     INSERT INTO notes_fts(notes_fts, rowid, title, content)
     VALUES ('delete', old.id, old.title, old.content);
   END;

   CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
     INSERT INTO notes_fts(notes_fts, rowid, title, content)
     VALUES ('delete', old.id, old.title, old.content);
     INSERT INTO notes_fts(rowid, title, content)
     VALUES (new.id, new.title, new.content);
   END;
   ```

7. **Full vault scan** (`indexer.py`)
   - Walk vault directories
   - Parse each `.md` file
   - Insert into SQLite
   - Resolve links (mark which targets exist)

**Milestone**: Run indexer, query `SELECT COUNT(*) FROM notes`

### Phase 4: Core Views
8. **Base template** (`base.html`)
   - Wikipedia-style header with search box
   - Navigation: Timeline | Hubs | Graph | Search
   - Content area with optional sidebar
   - Footer with vault stats

9. **Timeline view** (`routes.py`, `timeline.html`)
   - Route: `GET /` and `GET /timeline`
   - Query notes ordered by `created_at DESC`
   - Pagination (20 per page)
   - Filter params: `?type=note&hub=machine-learning`

10. **Note reader** (`routes.py`, `note.html`)
    - Route: `GET /note/<path:note_path>`
    - Render markdown to HTML
    - Convert wikilinks to `<a href="/note/...">`
    - Sidebar: metadata, backlinks

**Milestone**: Browse timeline, click note, read content with working links

### Phase 5: Hub Navigation
11. **Hub atlas** (`routes.py`, `hub_atlas.html`)
    - Route: `GET /hubs`
    - List all hubs with note counts
    - Sort options: name, count, updated

12. **Hub detail** (`routes.py`, `hub.html`)
    - Route: `GET /hub/<hub_name>`
    - Hub content rendered
    - Linked notes grouped by time period
    - Related hubs

**Milestone**: Navigate hubs, see linked notes

### Phase 6: Search
13. **Search route** (`routes.py`, `search.html`)
    - Route: `GET /search?q=<query>`
    - FTS5 query with BM25 ranking
    - Snippet generation with highlights
    - Filters as query params

14. **Search JavaScript** (`search.js`)
    - Debounced search-as-you-type
    - Fetch API to `/search?q=...`
    - Update results dynamically

**Milestone**: Search works, results highlight matches

### Phase 7: Graph Visualization
15. **Graph data endpoint** (`routes.py`, `graph.py`)
    - Route: `GET /api/graph?center=<note>&depth=2`
    - Return JSON: `{nodes: [...], links: [...]}`
    - Node properties: id, title, type, status
    - Link properties: source, target

16. **D3.js visualization** (`graph.html`, `graph.js`)
    - Force-directed layout
    - Node styling by type
    - Click to navigate
    - Zoom and pan
    - Depth control slider

**Milestone**: Interactive graph renders, clicking nodes navigates

### Phase 8: Polish
17. **Error handling**
    - 404 for missing notes
    - Config error page
    - Graceful index rebuild

18. **Performance**
    - Index rebuild on startup (if stale)
    - Optional file watching with watchdog
    - Query optimization (EXPLAIN ANALYZE)

19. **Styles** (`style.css`)
    - Wikipedia-inspired typography
    - Link styling (internal vs external)
    - Responsive basics (desktop-focused)

---

## 4. Key Code Patterns

### Flask App Factory

```python
# viewer/__init__.py
from flask import Flask

def create_app(config_path=None):
    app = Flask(__name__)

    # Load config
    from .config import load_config
    app.config.update(load_config(config_path))

    # Register routes
    from .routes import bp
    app.register_blueprint(bp)

    # Initialize index
    from .indexer import init_index
    with app.app_context():
        init_index(app.config['VAULT_PATH'], app.config['INDEX_PATH'])

    return app
```

### Wikilink Parsing

```python
# viewer/parser.py
import re
from dataclasses import dataclass

WIKILINK_PATTERN = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]*)?(?\|([^\]]+))?\]\]')

@dataclass
class Link:
    target: str      # The linked note/hub name
    alias: str       # Display text (or None)
    section: str     # Section anchor (or None)

def extract_links(content: str) -> list[Link]:
    links = []
    for match in WIKILINK_PATTERN.finditer(content):
        target = match.group(1).strip()
        alias = match.group(2).strip() if match.group(2) else None
        links.append(Link(target=target, alias=alias, section=None))
    return links
```

### Markdown Rendering with Wikilink Conversion

```python
# viewer/parser.py
import mistune

def render_markdown(content: str, vault_notes: set[str]) -> str:
    """Render markdown, converting wikilinks to HTML links."""

    def replace_wikilink(match):
        target = match.group(1).strip()
        alias = match.group(2) or target

        # Check if target exists
        if target in vault_notes:
            href = f"/note/{target}"
            css_class = "internal-link"
        else:
            href = "#"
            css_class = "dead-link"

        return f'<a href="{href}" class="{css_class}">{alias}</a>'

    # Replace wikilinks before markdown processing
    content = WIKILINK_PATTERN.sub(replace_wikilink, content)

    # Render markdown
    return mistune.html(content)
```

### Graph Data Generation

```python
# viewer/graph.py
from dataclasses import dataclass, asdict

@dataclass
class GraphNode:
    id: str
    title: str
    type: str
    status: str

@dataclass
class GraphLink:
    source: str
    target: str

def build_graph(db, center_path: str = None, depth: int = 2) -> dict:
    """Build graph data for D3.js visualization."""
    nodes = {}
    links = []

    if center_path:
        # BFS from center node
        visited = set()
        queue = [(center_path, 0)]

        while queue:
            path, d = queue.pop(0)
            if path in visited or d > depth:
                continue
            visited.add(path)

            note = db.get_note(path)
            if note:
                nodes[path] = GraphNode(
                    id=path,
                    title=note.title,
                    type=note.note_type,
                    status=note.frontmatter.get('status', 'unknown')
                )

                for link in note.links:
                    links.append(GraphLink(source=path, target=link.target))
                    if link.target not in visited:
                        queue.append((link.target, d + 1))
    else:
        # Full graph - load all nodes
        for note in db.get_all_notes():
            nodes[note.path] = GraphNode(...)
            # ... add all links

    return {
        'nodes': [asdict(n) for n in nodes.values()],
        'links': [asdict(l) for l in links]
    }
```

### D3.js Force Graph

```javascript
// static/graph.js
function initGraph(containerId, dataUrl) {
  const width = document.getElementById(containerId).clientWidth;
  const height = 600;

  const svg = d3.select(`#${containerId}`)
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  // Zoom behavior
  const g = svg.append('g');
  svg.call(d3.zoom().on('zoom', (event) => {
    g.attr('transform', event.transform);
  }));

  // Load data
  d3.json(dataUrl).then(data => {
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links)
        .id(d => d.id)
        .distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(25));

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('class', 'graph-link');

    // Nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .join('circle')
      .attr('r', d => d.type === 'hub' ? 12 : 8)
      .attr('class', d => `graph-node node-${d.type}`)
      .call(drag(simulation))
      .on('click', (event, d) => {
        window.location.href = `/note/${d.id}`;
      });

    // Labels
    const label = g.append('g')
      .selectAll('text')
      .data(data.nodes)
      .join('text')
      .text(d => d.title.substring(0, 20))
      .attr('class', 'graph-label');

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      label
        .attr('x', d => d.x + 15)
        .attr('y', d => d.y + 4);
    });
  });

  function drag(simulation) {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }
}
```

---

## 5. SQLite Indexing Strategy

Learned from the Wikiois project:

### Index on Startup
```python
def init_index(vault_path: Path, index_path: Path):
    """Initialize or update the search index."""
    db = sqlite3.connect(index_path)

    # Check if rebuild needed
    last_indexed = get_last_indexed_time(db)
    vault_modified = get_vault_modified_time(vault_path)

    if last_indexed is None or vault_modified > last_indexed:
        rebuild_index(db, vault_path)

    return db
```

### Incremental Updates (Optional)
```python
def watch_vault(vault_path: Path, db):
    """Watch for file changes and update index."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class VaultHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.md'):
                reindex_file(db, Path(event.src_path))

    observer = Observer()
    observer.schedule(VaultHandler(), str(vault_path), recursive=True)
    observer.start()
```

### Query Performance
```sql
-- For timeline: index on created_at
CREATE INDEX idx_notes_created ON notes(created_at DESC);

-- For hub queries: index on type
CREATE INDEX idx_notes_type ON notes(type);

-- For link resolution
CREATE INDEX idx_links_target ON links(target_path);
CREATE INDEX idx_links_source ON links(source_id);
```

---

## 6. CLI Interface

```python
# scripts/viewer.py
#!/usr/bin/env python3
"""Second Brain Web Viewer - Flask-based vault browser."""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Start the Second Brain web viewer'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port to run server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Path to config.yaml'
    )
    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Force rebuild of search index'
    )

    args = parser.parse_args()

    # Import here to avoid slow startup for --help
    from viewer import create_app

    app = create_app(config_path=args.config)

    if args.reindex:
        from viewer.indexer import rebuild_index
        rebuild_index(app.config['VAULT_PATH'], app.config['INDEX_PATH'])
        print("Index rebuilt successfully")
        return

    print(f"Starting viewer at http://{args.host}:{args.port}")
    print(f"Vault: {app.config['VAULT_PATH']}")
    print("Press Ctrl+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
```

---

## 7. Testing Approach

### Unit Tests

```python
# tests/test_parser.py
def test_extract_wikilinks():
    content = "See [[Machine Learning]] and [[AI|Artificial Intelligence]]"
    links = extract_links(content)
    assert len(links) == 2
    assert links[0].target == "Machine Learning"
    assert links[1].target == "AI"
    assert links[1].alias == "Artificial Intelligence"

def test_malformed_frontmatter():
    content = """---
    title: Test
    invalid yaml: [unclosed
    ---
    Content here"""
    note = parse_note(content)
    assert note.title == "Test"  # Partial parse succeeds
```

### Integration Tests

```python
# tests/test_routes.py
def test_timeline(client, indexed_vault):
    response = client.get('/timeline')
    assert response.status_code == 200
    assert b'Note Title' in response.data

def test_note_reader(client, indexed_vault):
    response = client.get('/note/notes/2024-01-15--test-note')
    assert response.status_code == 200
    assert b'wikilink' in response.data  # Links rendered

def test_search(client, indexed_vault):
    response = client.get('/search?q=machine+learning')
    assert response.status_code == 200
```

### Manual Testing Checklist

- [ ] Start server, see timeline
- [ ] Click note, see rendered markdown
- [ ] Wikilinks navigate correctly
- [ ] Dead links styled differently
- [ ] Search returns relevant results
- [ ] Hub atlas shows all hubs
- [ ] Hub detail shows linked notes
- [ ] Graph renders without errors
- [ ] Graph nodes clickable
- [ ] Zoom and pan work
- [ ] No errors in browser console
- [ ] No vault files modified after session

---

## 8. Common Pitfalls

1. **Path handling on Windows**
   - Always use `Path` objects, not string concatenation
   - Normalize paths before comparison

2. **Unicode in filenames**
   - Use `encoding='utf-8'` for all file operations
   - Handle BOM in markdown files

3. **Large vaults**
   - Don't load all notes into memory
   - Use pagination in queries
   - Limit graph to neighborhood view for >1000 nodes

4. **Frontmatter edge cases**
   - Missing `---` delimiters
   - YAML arrays vs strings
   - Dates as strings vs datetime objects

5. **Wikilink variations**
   - `[[Note]]` vs `[[note]]` (case sensitivity)
   - `[[Folder/Note]]` (paths in links)
   - `[[Note#Section]]` (anchors)

---

## 9. Future Enhancements (Not in Scope)

Documented for future sessions if requested:

- **Dark mode toggle** - CSS variables for themes
- **Export view to PDF** - Print stylesheet
- **Recent notes sidebar** - LocalStorage history
- **Keyboard navigation** - vim-style shortcuts
- **Embed preview** - Hover over links for popup
- **Tag cloud** - Visualize tag frequency

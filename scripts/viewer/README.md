# Second Brain Viewer

A read-only web interface for browsing and exploring your Second Brain knowledge archive.

## Features

- **Timeline View**: Browse notes chronologically with filters
- **Hub Atlas**: Explore conceptual gathering places and their linked notes
- **Project Atlas**: View active inquiry projects
- **Source Atlas**: Browse external materials
- **Graph Visualization**: Interactive D3.js force-directed graph
- **Full-Text Search**: Fast SQLite FTS5-powered search
- **Wikilink Navigation**: Case-insensitive wikilink resolution
- **Obsidian Integration**: Open notes directly in Obsidian

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your `config/config.yaml` has a vault path configured:
```yaml
notes_root: "/path/to/your/vault"
# or
vault:
  path: "/path/to/your/vault"
  name: "My Vault"  # Optional, for Obsidian URIs
```

3. Start the viewer:
```bash
python scripts/start_viewer.py
```

4. Open your browser to http://127.0.0.1:5000

## Architecture

- **Parser**: Extracts frontmatter, wikilinks, and renders markdown
- **Indexer**: SQLite database with FTS5 for full-text search
- **Flask App**: Read-only web interface with multiple views
- **Templates**: Jinja2 templates for all views
- **Static Assets**: CSS styling and D3.js graph visualization

## Index Location

The SQLite index is stored outside the vault at:
```
~/.second-brian/viewer/index-{vault_hash}.db
```

This preserves the read-only principle - the vault is never modified.

## Performance

- Timeline: Designed for 10,000+ notes
- Search: Sub-500ms queries
- Graph: Warning at 5,000+ nodes

## Specification

See the complete specification:
- `specs/24-viewer-spec.md` - UI/UX design
- `specs/25-viewer-implementation.md` - Implementation details

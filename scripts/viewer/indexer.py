"""
SQLite indexer for Second-Brain viewer.
Handles index creation, updates, and queries with FTS5 support.
"""

import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from .parser import parse_note, extract_frontmatter


def get_index_path(vault_path: Path) -> Path:
    """
    Get the index database path for a vault.
    Uses vault path hash to support multiple vaults.

    Args:
        vault_path: Path to vault root

    Returns:
        Path to index database
    """
    # Create hash of vault path for unique index filename
    vault_hash = hashlib.md5(str(vault_path).encode()).hexdigest()[:8]

    # Use user's home directory
    index_dir = Path.home() / '.second-brian' / 'viewer'
    index_dir.mkdir(parents=True, exist_ok=True)

    return index_dir / f'index-{vault_hash}.db'


def init_index(vault_path: Path) -> sqlite3.Connection:
    """
    Initialize or update the search index.

    Args:
        vault_path: Path to vault root

    Returns:
        SQLite connection
    """
    index_path = get_index_path(vault_path)
    db = sqlite3.connect(str(index_path))
    db.row_factory = sqlite3.Row

    # Create metadata table
    db.execute("""
        CREATE TABLE IF NOT EXISTS _index_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Create notes table
    db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT,
            created_at TEXT NOT NULL,
            body TEXT NOT NULL,
            preview TEXT
        )
    """)

    # Create links table
    db.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL,
            target TEXT NOT NULL,
            section TEXT,
            FOREIGN KEY (source_path) REFERENCES notes(path)
        )
    """)

    # Create FTS5 virtual table for full-text search
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
            title,
            body,
            content='notes',
            content_rowid='id'
        )
    """)

    # Create indexes for performance
    db.execute("CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(type)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_notes_status ON notes(status)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_path)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_links_target ON links(target)")

    db.commit()

    # Check if rebuild needed
    last_indexed = get_last_indexed_time(db)
    vault_modified = get_vault_modified_time(vault_path)

    if last_indexed is None or vault_modified > last_indexed:
        print(f"Index stale or missing. Rebuilding...")
        rebuild_index(db, vault_path)
        # Store new timestamp
        db.execute("""
            INSERT OR REPLACE INTO _index_metadata (key, value)
            VALUES ('last_indexed', ?)
        """, (datetime.now().isoformat(),))
        db.commit()
        print(f"Index rebuilt successfully.")

    return db


def get_last_indexed_time(db: sqlite3.Connection) -> Optional[datetime]:
    """Get the last indexed timestamp from metadata."""
    cursor = db.execute(
        "SELECT value FROM _index_metadata WHERE key = 'last_indexed'"
    )
    row = cursor.fetchone()
    if row:
        return datetime.fromisoformat(row[0])
    return None


def get_vault_modified_time(vault_path: Path) -> datetime:
    """
    Get the most recent modification time of any .md file in vault.

    Args:
        vault_path: Path to vault root

    Returns:
        Most recent modification datetime
    """
    max_mtime = 0
    for md_file in vault_path.rglob('*.md'):
        max_mtime = max(max_mtime, md_file.stat().st_mtime)
    return datetime.fromtimestamp(max_mtime) if max_mtime > 0 else datetime.min


def rebuild_index(db: sqlite3.Connection, vault_path: Path):
    """
    Rebuild the entire index from scratch.

    Args:
        db: SQLite connection
        vault_path: Path to vault root
    """
    # Clear existing data
    db.execute("DELETE FROM links")
    db.execute("DELETE FROM notes")
    db.execute("DELETE FROM notes_fts")

    # Index all markdown files
    md_files = list(vault_path.rglob('*.md'))
    print(f"Indexing {len(md_files)} files...")

    for i, md_file in enumerate(md_files):
        if i % 100 == 0:
            print(f"  Indexed {i}/{len(md_files)} files...")

        try:
            index_file(db, md_file, vault_path)
        except Exception as e:
            print(f"  Warning: Failed to index {md_file}: {e}")
            continue

    db.commit()


def index_file(db: sqlite3.Connection, file_path: Path, vault_path: Path):
    """
    Index a single file.

    Args:
        db: SQLite connection
        file_path: Path to file
        vault_path: Path to vault root
    """
    try:
        parsed = parse_note(file_path)
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return

    frontmatter = parsed['frontmatter']

    # Determine relative path from vault (use forward slashes for portability)
    rel_path = file_path.relative_to(vault_path)
    # Convert to POSIX path (forward slashes) for storage
    path_str = rel_path.as_posix()

    # Extract metadata
    title = frontmatter.get('title', file_path.stem)
    note_type = frontmatter.get('type', 'note')
    status = frontmatter.get('status', 'raw')
    created_at = frontmatter.get('created_at', '')

    # Insert note
    db.execute("""
        INSERT OR REPLACE INTO notes
        (path, filename, title, type, status, created_at, body, preview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        path_str,
        file_path.name,
        title,
        note_type,
        status,
        created_at,
        parsed['body'],
        parsed['preview']
    ))

    # Get the note ID
    note_id = db.execute("SELECT id FROM notes WHERE path = ?", (str(rel_path),)).fetchone()[0]

    # Insert into FTS
    db.execute("""
        INSERT INTO notes_fts(rowid, title, body)
        VALUES (?, ?, ?)
    """, (note_id, title, parsed['body']))

    # Insert links
    for link in parsed['links']:
        db.execute("""
            INSERT INTO links (source_path, target, section)
            VALUES (?, ?, ?)
        """, (str(rel_path), link.target, link.section))


def search_notes(db: sqlite3.Connection, query: str, limit: int = 50) -> list[dict]:
    """
    Full-text search across notes.

    Args:
        db: SQLite connection
        query: Search query
        limit: Maximum results

    Returns:
        List of note dicts with snippets
    """
    cursor = db.execute("""
        SELECT
            notes.path,
            notes.filename,
            notes.title,
            notes.type,
            notes.created_at,
            snippet(notes_fts, 1, '<mark>', '</mark>', '...', 30) as snippet
        FROM notes_fts
        JOIN notes ON notes.id = notes_fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    results = []
    for row in cursor:
        results.append({
            'path': row['path'],
            'filename': row['filename'],
            'title': row['title'],
            'type': row['type'],
            'created_at': row['created_at'],
            'snippet': row['snippet']
        })

    return results


def get_timeline(db: sqlite3.Connection, filters: dict = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """
    Get notes for timeline view.

    Args:
        db: SQLite connection
        filters: Dict of filter criteria (type, status, hub, date_range, show_archived)
        limit: Maximum results
        offset: Offset for pagination

    Returns:
        List of note dicts
    """
    where_clauses = []
    params = []

    filters = filters or {}

    # Type filter
    if filters.get('type'):
        types = filters['type'] if isinstance(filters['type'], list) else [filters['type']]
        placeholders = ','.join('?' * len(types))
        where_clauses.append(f"type IN ({placeholders})")
        params.extend(types)

    # Status filter
    if filters.get('status'):
        where_clauses.append("status = ?")
        params.append(filters['status'])

    # Date range filter
    if filters.get('date_from'):
        where_clauses.append("created_at >= ?")
        params.append(filters['date_from'])

    if filters.get('date_to'):
        where_clauses.append("created_at <= ?")
        params.append(filters['date_to'])

    # Build query
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    cursor = db.execute(f"""
        SELECT path, filename, title, type, status, created_at, preview
        FROM notes
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (*params, limit, offset))

    return [dict(row) for row in cursor]


def get_all_hubs(db: sqlite3.Connection) -> list[dict]:
    """Get all hub notes."""
    cursor = db.execute("""
        SELECT path, filename, title, status
        FROM notes
        WHERE type = 'hub'
        ORDER BY title
    """)
    return [dict(row) for row in cursor]


def get_note_by_path(db: sqlite3.Connection, path: str) -> Optional[dict]:
    """Get a note by its relative path."""
    cursor = db.execute("""
        SELECT *
        FROM notes
        WHERE path = ?
    """, (path,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_backlinks(db: sqlite3.Connection, note_title: str) -> list[dict]:
    """Get all notes that link to a given note title."""
    cursor = db.execute("""
        SELECT DISTINCT notes.*
        FROM notes
        JOIN links ON notes.path = links.source_path
        WHERE LOWER(links.target) = LOWER(?)
        ORDER BY notes.created_at DESC
    """, (note_title,))
    return [dict(row) for row in cursor]


def get_graph_data(db: sqlite3.Connection) -> dict:
    """
    Get nodes and edges for graph visualization.

    Returns:
        Dict with 'nodes' and 'links' lists
    """
    # Get all notes as nodes
    cursor = db.execute("""
        SELECT path, title, type, status, filename
        FROM notes
    """)
    nodes = []
    # Create lookup maps for resolving wikilinks to paths
    title_to_path = {}  # Case-insensitive title lookup
    filename_to_path = {}  # Case-insensitive filename lookup

    for row in cursor:
        path = row['path']
        title = row['title']
        filename = row['filename']

        nodes.append({
            'id': path,
            'title': title,
            'type': row['type'],
            'status': row['status']
        })

        # Build lookup maps (case-insensitive)
        if title:
            title_to_path[title.lower()] = path
        if filename:
            # Also store without extension
            filename_to_path[filename.lower()] = path
            name_no_ext = filename.replace('.md', '')
            filename_to_path[name_no_ext.lower()] = path

    # Get all links as edges and resolve targets to paths
    cursor = db.execute("""
        SELECT DISTINCT source_path, target
        FROM links
    """)
    links = []

    for row in cursor:
        source_path = row['source_path']
        target = row['target']

        # Try to resolve target to a node id (path)
        target_lower = target.lower()
        target_path = None

        # Try exact title match first
        if target_lower in title_to_path:
            target_path = title_to_path[target_lower]
        # Try filename match
        elif target_lower in filename_to_path:
            target_path = filename_to_path[target_lower]
        # Try with .md extension
        elif f"{target_lower}.md" in filename_to_path:
            target_path = filename_to_path[f"{target_lower}.md"]

        # Only add link if we found a matching target node
        if target_path:
            links.append({
                'source': source_path,
                'target': target_path
            })

    return {'nodes': nodes, 'links': links}

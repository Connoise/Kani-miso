"""
Flask web application for Second-Brain viewer.
Provides read-only web interface to browse notes, hubs, and graph.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, current_app
from pathlib import Path
import yaml
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from .indexer import init_index, get_timeline, get_all_hubs, get_note_by_path, get_backlinks, search_notes, get_graph_data
from .parser import render_markdown, extract_frontmatter


def create_app(vault_path: Path, config: dict = None):
    """
    Create and configure the Flask app.

    Args:
        vault_path: Path to vault root
        config: Optional config dict

    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.config['VAULT_PATH'] = vault_path
    app.config['VAULT_NAME'] = config.get('vault', {}).get('name', 'My Vault') if config else 'My Vault'

    # Initialize index
    print(f"Initializing index for vault: {vault_path}")
    db = init_index(vault_path)
    app.config['DB'] = db

    # Build known files set for dead link detection
    known_files = set()
    for md_file in vault_path.rglob('*.md'):
        known_files.add(md_file.stem.lower())
        known_files.add(md_file.name.lower())
    app.config['KNOWN_FILES'] = known_files

    def get_db():
        """Helper to get database connection."""
        return current_app.config['DB']

    def get_vault_path():
        """Helper to get vault path."""
        return current_app.config['VAULT_PATH']

    @app.route('/')
    def index():
        """Redirect to timeline view."""
        return render_template('index.html')

    @app.route('/timeline')
    def timeline():
        """Timeline view with filters."""
        # Get filter parameters
        filters = {
            'type': request.args.getlist('type'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'show_archived': request.args.get('show_archived', 'true') == 'true'
        }

        # Get pagination parameters
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        # Get timeline data
        notes = get_timeline(current_app.config['DB'], filters, limit, offset)

        return render_template('timeline.html', notes=notes, filters=filters, offset=offset, limit=limit)

    @app.route('/hubs')
    def hubs():
        """Hub atlas view."""
        hubs = get_all_hubs(get_db())
        return render_template('hubs.html', hubs=hubs)

    @app.route('/hub/<path:hub_name>')
    def hub_detail(hub_name):
        """Hub detail page."""
        # Find hub file
        hub_name_decoded = unquote(hub_name)

        # Try to find the hub file
        hub_file = None
        for candidate in get_vault_path().rglob('*.md'):
            if candidate.stem.lower() == hub_name_decoded.lower() and 'hubs' in str(candidate):
                hub_file = candidate
                break

        if not hub_file:
            return render_template('404.html', message=f"Hub '{hub_name_decoded}' not found"), 404

        # Load hub content
        with open(hub_file, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter, body = extract_frontmatter(content)

        # Render markdown
        html = render_markdown(body, get_vault_path(), hub_file, current_app.config['KNOWN_FILES'])

        # Get backlinks (notes that link to this hub)
        backlinks = get_backlinks(get_db(), hub_name_decoded)

        # Group backlinks by time period
        now = datetime.now()
        this_week = now - timedelta(days=7)
        this_month = now - timedelta(days=30)

        groups = {
            'this_week': [],
            'this_month': [],
            'older': []
        }

        for note in backlinks:
            try:
                created_at = datetime.fromisoformat(note['created_at'])
                if created_at >= this_week:
                    groups['this_week'].append(note)
                elif created_at >= this_month:
                    groups['this_month'].append(note)
                else:
                    groups['older'].append(note)
            except (ValueError, KeyError):
                groups['older'].append(note)

        # Calculate related hubs (hubs that share notes with this hub)
        related_hubs = calculate_related_hubs(get_db(), backlinks)

        return render_template('hub_detail.html',
                               hub_name=hub_name_decoded,
                               frontmatter=frontmatter,
                               content_html=html,
                               groups=groups,
                               related_hubs=related_hubs)

    @app.route('/projects')
    def projects():
        """Project atlas view."""
        cursor = get_db().execute("""
            SELECT path, filename, title, status, created_at
            FROM notes
            WHERE type = 'project'
            ORDER BY status, title
        """)
        projects = [dict(row) for row in cursor]
        return render_template('projects.html', projects=projects)

    @app.route('/sources')
    def sources():
        """Source atlas view."""
        source_type = request.args.get('source_type')

        where_clause = "type = 'source'"
        params = []

        if source_type:
            where_clause += " AND frontmatter LIKE ?"
            params.append(f'%source_type: {source_type}%')

        cursor = get_db().execute(f"""
            SELECT path, filename, title, created_at, preview
            FROM notes
            WHERE {where_clause}
            ORDER BY created_at DESC
        """, params)

        sources = [dict(row) for row in cursor]
        return render_template('sources.html', sources=sources, current_filter=source_type)

    @app.route('/note/<path:note_path>')
    def note_detail(note_path):
        """Note reader view."""
        note_path_decoded = unquote(note_path)

        # Try to find the note file
        note_file = None
        for candidate in get_vault_path().rglob('*.md'):
            rel_path = candidate.relative_to(get_vault_path())
            if str(rel_path) == note_path_decoded or candidate.stem.lower() == note_path_decoded.lower():
                note_file = candidate
                break

        if not note_file:
            return render_template('404.html', message=f"Note '{note_path_decoded}' not found"), 404

        # Load note content
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter, body = extract_frontmatter(content)

        # Render markdown
        html = render_markdown(body, get_vault_path(), note_file, current_app.config['KNOWN_FILES'])

        # Get backlinks
        note_title = frontmatter.get('title', note_file.stem)
        backlinks = get_backlinks(get_db(), note_title)

        # Build Obsidian URI
        rel_path = note_file.relative_to(get_vault_path())
        obsidian_uri = f"obsidian://open?vault={quote(current_app.config['VAULT_NAME'])}&file={quote(str(rel_path))}"

        return render_template('note_detail.html',
                               note_title=note_title,
                               frontmatter=frontmatter,
                               content_html=html,
                               backlinks=backlinks,
                               obsidian_uri=obsidian_uri)

    @app.route('/graph')
    def graph():
        """Graph visualization view."""
        return render_template('graph.html')

    @app.route('/api/graph')
    def api_graph():
        """API endpoint for graph data."""
        data = get_graph_data(get_db())
        return jsonify(data)

    @app.route('/search')
    def search():
        """Search view."""
        query = request.args.get('q', '')
        results = []

        if query:
            results = search_notes(get_db(), query, limit=50)

        return render_template('search.html', query=query, results=results)

    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files."""
        return send_from_directory('static', filename)

    @app.template_filter('format_date')
    def format_date(date_str):
        """Template filter to format ISO dates."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str

    return app


def calculate_related_hubs(db, backlinks: list[dict]) -> list[dict]:
    """
    Calculate related hubs based on shared notes.

    Args:
        db: SQLite connection
        backlinks: List of notes that link to current hub

    Returns:
        List of related hubs with share counts
    """
    if not backlinks:
        return []

    # Get all hubs that these notes link to
    note_paths = [note['path'] for note in backlinks]
    placeholders = ','.join('?' * len(note_paths))

    cursor = db.execute(f"""
        SELECT links.target, COUNT(*) as share_count
        FROM links
        JOIN notes ON notes.path = links.target || '.md' OR notes.title = links.target
        WHERE links.source_path IN ({placeholders})
        AND notes.type = 'hub'
        GROUP BY links.target
        HAVING share_count >= 2
        ORDER BY share_count DESC
        LIMIT 5
    """, note_paths)

    related = []
    for row in cursor:
        related.append({
            'name': row[0],
            'count': row[1]
        })

    return related

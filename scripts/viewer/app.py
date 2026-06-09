"""
Flask web application for Kani-miso viewer.
Provides read-only web interface to browse notes, hubs, and graph.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, current_app, g
from pathlib import Path
import yaml
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from .indexer import init_index, get_index_path, get_timeline, get_all_hubs, get_note_by_path, get_backlinks, search_notes, get_graph_data
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
    # Get the directory where this module is located
    module_dir = Path(__file__).parent
    template_folder = module_dir / 'templates'
    static_folder = module_dir / 'static'

    app = Flask(__name__,
                template_folder=str(template_folder),
                static_folder=str(static_folder))
    app.config['VAULT_PATH'] = vault_path
    app.config['VAULT_NAME'] = config.get('vault', {}).get('name', 'My Vault') if config else 'My Vault'

    # Initialize index (this ensures index exists and is up-to-date)
    print(f"Initializing index for vault: {vault_path}")
    _ = init_index(vault_path)  # Creates/updates index, returns connection we don't store

    # Store index path for per-request connections
    app.config['INDEX_PATH'] = get_index_path(vault_path)

    # Build known files set for dead link detection
    known_files = set()
    for md_file in vault_path.rglob('*.md'):
        known_files.add(md_file.stem.lower())
        known_files.add(md_file.name.lower())
    app.config['KNOWN_FILES'] = known_files

    def get_db():
        """Get database connection for current request (thread-safe)."""
        if 'db' not in g:
            # Create a new connection for this request/thread
            g.db = sqlite3.connect(str(current_app.config['INDEX_PATH']))
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        """Close database connection at end of request."""
        db = g.pop('db', None)
        if db is not None:
            db.close()

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

        # Get sort and pagination parameters
        sort_order = request.args.get('sort', 'desc')  # desc = newest first, asc = oldest first
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        # Get timeline data
        notes = get_timeline(get_db(), filters, limit, offset, sort_order)

        return render_template('timeline.html', notes=notes, filters=filters, offset=offset, limit=limit, sort_order=sort_order)

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
        cursor = get_db().execute("""
            SELECT path, filename, title, created_at, preview, type
            FROM notes
            WHERE type = 'source'
            ORDER BY created_at DESC
        """)

        sources = [dict(row) for row in cursor]
        return render_template('sources.html', sources=sources)

    @app.route('/tweets')
    def tweets():
        """Tweets atlas view."""
        cursor = get_db().execute("""
            SELECT path, filename, title, created_at, preview, status
            FROM notes
            WHERE type = 'tweet'
            ORDER BY created_at DESC
        """)

        tweets = [dict(row) for row in cursor]
        return render_template('tweets.html', tweets=tweets)

    @app.route('/note/<path:note_path>')
    def note_detail(note_path):
        """Note reader view."""
        note_path_decoded = unquote(note_path)

        # Try to find the note file
        # Normalize path for comparison (use forward slashes)
        note_path_normalized = note_path_decoded.replace('\\', '/')

        note_file = None
        for candidate in get_vault_path().rglob('*.md'):
            rel_path = candidate.relative_to(get_vault_path())
            # Use POSIX path (forward slashes) for comparison
            candidate_path = rel_path.as_posix()

            if candidate_path == note_path_normalized or candidate.stem.lower() == note_path_normalized.lower():
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

        # Build Obsidian URI (use forward slashes)
        rel_path = note_file.relative_to(get_vault_path())
        obsidian_uri = f"obsidian://open?vault={quote(current_app.config['VAULT_NAME'])}&file={quote(rel_path.as_posix())}"

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

    @app.route('/vault-image/<path:image_path>')
    def vault_image(image_path):
        """
        Serve images from the vault directory.

        This route handles Obsidian-style image embeds like ![[images/2026/01/21/image-001.jpg]]
        """
        # Normalize path separators
        image_path = image_path.replace('\\', '/')

        # Security: prevent directory traversal
        if '..' in image_path:
            return "Invalid path", 403

        # Build full path
        full_path = get_vault_path() / image_path

        if not full_path.exists():
            return f"Image not found: {image_path}", 404

        # Ensure the path is within the vault
        try:
            full_path.resolve().relative_to(get_vault_path().resolve())
        except ValueError:
            return "Access denied", 403

        # Serve the file
        return send_from_directory(
            str(full_path.parent),
            full_path.name,
            mimetype=None  # Let Flask guess based on extension
        )

    @app.route('/images')
    def images_gallery():
        """Image gallery view - browse all images in the vault."""
        images = []
        images_dir = get_vault_path() / 'images'

        if images_dir.exists():
            # Find all images organized by date
            for image_file in sorted(images_dir.rglob('*'), reverse=True):
                if image_file.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
                    rel_path = image_file.relative_to(get_vault_path())
                    images.append({
                        'path': str(rel_path).replace('\\', '/'),
                        'name': image_file.name,
                        'date': image_file.parent.name if image_file.parent != images_dir else 'Unsorted',
                    })

        return render_template('images.html', images=images)

    @app.template_filter('format_date')
    def format_date(date_str):
        """Template filter to format ISO dates."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str

    @app.errorhandler(Exception)
    def handle_error(e):
        """Error handler to show actual errors for debugging."""
        import traceback
        error_msg = f"""
        <html>
        <head><title>Error</title></head>
        <body>
        <h1>Error Details</h1>
        <pre>{traceback.format_exc()}</pre>
        <p><strong>Error:</strong> {str(e)}</p>
        </body>
        </html>
        """
        return error_msg, 500

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

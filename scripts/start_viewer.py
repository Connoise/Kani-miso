#!/usr/bin/env python3
"""
Launcher script for Kani-miso viewer.
Reads configuration and starts the Flask web server.
"""

import sys
import yaml
from pathlib import Path
from viewer import create_app


def load_config(config_path: Path = None) -> dict:
    """Load configuration from config.yaml"""
    if config_path is None:
        # Try to find config.yaml in config directory
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'config.yaml'

        # Fallback to project root
        if not config_path.exists():
            config_path = project_root / 'config.yaml'

    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        print("Please create a config.yaml file with your vault path.")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def main():
    """Main entry point"""
    # Load configuration
    config = load_config()

    # Get vault path (support both vault.path and notes_root)
    vault_path_str = config.get('vault', {}).get('path') or config.get('notes_root')

    if not vault_path_str:
        print("Error: vault.path or notes_root not found in config.yaml")
        sys.exit(1)

    # If notes_root is ".", use the project root
    if vault_path_str == ".":
        vault_path = Path(__file__).parent.parent
    else:
        vault_path = Path(vault_path_str).expanduser()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    print(f"Starting viewer for vault: {vault_path}")

    # Get viewer configuration
    viewer_config = config.get('viewer', {})
    host = viewer_config.get('host', '127.0.0.1')
    port = viewer_config.get('port', 5000)
    debug = viewer_config.get('debug', True)  # Enable debug mode by default for troubleshooting

    # Create Flask app
    app = create_app(vault_path, config)

    # Start server
    print(f"Starting web server at http://{host}:{port}")
    print("Press Ctrl+C to stop")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

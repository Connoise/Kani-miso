#!/bin/bash
# Quick test script for viewer in container environment

cd /home/user/Second-Brian

echo "Starting Second Brain Viewer on http://127.0.0.1:5000"
echo "Using repo as test vault (70 markdown files found)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -c "
import sys
sys.path.insert(0, 'scripts')
from pathlib import Path
from viewer import create_app

# Use repo as test vault
vault_path = Path('.')
config = {'vault': {'name': 'Second Brain Dev'}}

app = create_app(vault_path, config)
app.run(host='127.0.0.1', port=5000, debug=True)
"

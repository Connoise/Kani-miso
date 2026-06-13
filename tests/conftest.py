"""Pytest path setup: make scripts/ importable the same way the code does it."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures"

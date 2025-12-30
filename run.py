#!/usr/bin/env python3
"""
Launcher script for CMAT UI.

Usage:
    python run.py
    OR
    ./run.py  (after chmod +x run.py)
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Run the application
from ui.main import main

if __name__ == "__main__":
    main()

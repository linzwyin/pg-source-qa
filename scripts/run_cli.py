#!/usr/bin/env python3
"""Run CLI directly for testing."""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"Python: {sys.executable}")
print(f"Project root: {project_root}")
print(f"Src path: {src_path}")
print(f"Path exists: {src_path.exists()}")
print()

print("Importing cli module...")
try:
    from source_qa.cli import app
    print("✓ Import successful")
    print(f"App type: {type(app)}")
    print()
    
    # 运行 --help
    print("Running CLI with --help...")
    print("-" * 60)
    sys.argv = ["pg-qa", "--help"]
    app()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""Check if all required dependencies are properly installed."""

import importlib
import sys
from typing import List, Tuple


def check_module(module_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a module can be imported.
    
    Args:
        module_name: Display name of the module
        import_name: Actual import name (if different from display name)
        
    Returns:
        Tuple of (success, message)
    """
    if import_name is None:
        import_name = module_name.lower().replace("-", "_")
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"✓ {module_name} ({version})"
    except ImportError as e:
        return False, f"✗ {module_name} - {e}"


def check_dependencies() -> List[Tuple[bool, str]]:
    """Check all required dependencies."""
    
    dependencies = [
        ("openai", "openai"),
        ("llama-index", "llama_index"),
        ("chromadb", "chromadb"),
        ("sentence-transformers", "sentence_transformers"),
        ("FlagEmbedding", "FlagEmbedding"),
        ("tree-sitter", "tree_sitter"),
        ("tree-sitter-c", "tree_sitter_c"),
        ("PyMuPDF", "fitz"),
        ("pdfplumber", "pdfplumber"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("networkx", "networkx"),
        ("rank-bm25", "rank_bm25"),
        ("scikit-learn", "sklearn"),
        ("GitPython", "git"),
        ("pydantic", "pydantic"),
        ("typer", "typer"),
        ("rich", "rich"),
        ("streamlit", "streamlit"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
    ]
    
    results = []
    for display_name, import_name in dependencies:
        results.append(check_module(display_name, import_name))
    
    return results


def main():
    print("=" * 60)
    print("PostgreSQL Source Code QA System - Dependency Check")
    print("=" * 60)
    print()
    
    results = check_dependencies()
    
    success_count = 0
    fail_count = 0
    
    for success, message in results:
        print(message)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print()
    print("=" * 60)
    print(f"Summary: {success_count} OK, {fail_count} Missing")
    print("=" * 60)
    
    if fail_count > 0:
        print()
        print("To install missing dependencies, run:")
        print("  pip install -e \".[dev]\"")
        sys.exit(1)
    else:
        print()
        print("✓ All dependencies are installed correctly!")
        
        # Additional checks
        print()
        print("Additional Checks:")
        
        # Check Python version
        py_version = sys.version_info
        if py_version >= (3, 10):
            print(f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
        else:
            print(f"✗ Python {py_version.major}.{py_version.minor} (requires >= 3.10)")
        
        # Check for git
        import shutil
        if shutil.which("git"):
            print("✓ Git is available")
        else:
            print("✗ Git not found (required for downloading PostgreSQL source)")
        
        sys.exit(0)


if __name__ == "__main__":
    main()

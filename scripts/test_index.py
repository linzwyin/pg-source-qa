#!/usr/bin/env python3
"""Test script for indexing functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from source_qa.indexer import CodeIndexer
from rich.console import Console

console = Console()

def test_index():
    """Test indexing with a simple directory."""
    test_dir = Path("./data/postgres")
    
    if not test_dir.exists():
        console.print(f"[red]Directory not found: {test_dir}[/red]")
        console.print("Please run: python scripts/download_postgres.py")
        return 1
    
    console.print("[bold blue]Testing Indexer...[/bold blue]")
    console.print(f"Directory: {test_dir.absolute()}")
    console.print("")
    
    try:
        indexer = CodeIndexer()
        console.print("[green]✓ CodeIndexer initialized[/green]")
        
        result = indexer.index_directory(test_dir, clear_existing=True)
        console.print("")
        console.print("[green]✓ Indexing complete![/green]")
        console.print(f"Result: {result}")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return 1

if __name__ == "__main__":
    sys.exit(test_index())

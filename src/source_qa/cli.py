"""Command-line interface for Source Code QA System."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from source_qa import __version__
from source_qa.config import get_settings
from source_qa.qa_engine import CodeQASystem

app = typer.Typer(
    name="source-qa",
    help="Source Code QA System - Ask questions about your codebase",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Source Code QA System v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Source Code QA System."""
    pass


@app.command(name="index-code")
def index_code(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing source code to index",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        "-c",
        help="Clear existing index before indexing",
    ),
) -> None:
    """Index source code directory."""
    # Immediate output to diagnose if command is being invoked
    import sys
    sys.stderr.write("[DEBUG] Command invoked\n")
    sys.stderr.flush()
    
    try:
        # Use CodeIndexer directly - doesn't require API key
        sys.stderr.write("[DEBUG] Importing CodeIndexer...\n")
        sys.stderr.flush()
        from source_qa.indexer import CodeIndexer
        
        sys.stderr.write("[DEBUG] Import successful, creating indexer...\n")
        sys.stderr.flush()
        
        console.print("[bold blue]PostgreSQL Source Code Indexer[/bold blue]")
        console.print("")
        
        indexer = CodeIndexer()
        
        sys.stderr.write("[DEBUG] Indexer created, starting indexing...\n")
        sys.stderr.flush()
        
        result = indexer.index_directory(str(directory), clear_existing=clear)
        
        table = Table(title="Indexing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in result.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print("")
        console.print(table)
        console.print("")
        console.print("[green]✓ Indexing complete![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command()
def query(
    question: str = typer.Argument(
        ...,
        help="Question to ask about the codebase",
    ),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of relevant chunks to retrieve",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
) -> None:
    """Ask a single question about the indexed codebase."""
    try:
        qa = CodeQASystem()
        answer = qa.query(question, top_k=top_k, stream=True, verbose=verbose)
        
        if not verbose:
            # Print the streamed response
            pass  # Already printed during streaming
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def chat(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output",
    ),
) -> None:
    """Start an interactive chat session."""
    try:
        qa = CodeQASystem()
        qa.chat(verbose=verbose)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """Show index statistics."""
    try:
        qa = CodeQASystem()
        stats_data = qa.indexer.get_stats()
        
        table = Table(title="Index Statistics")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in stats_data.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()
    
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Moonshot settings
    table.add_row("Moonshot Model", settings.moonshot_model)
    table.add_row("Moonshot Base URL", settings.moonshot_base_url)
    table.add_row(
        "API Key",
        "✓ Configured" if settings.moonshot_api_key else "✗ Not configured",
    )
    
    # Vector store settings
    table.add_row("Vector Store Path", settings.vector_store_path)
    table.add_row("Collection Name", settings.collection_name)
    
    # Embedding settings
    table.add_row("Embedding Model", settings.embedding_model)
    table.add_row("Embedding Device", settings.embedding_device)
    
    # Indexing settings
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Chunk Overlap", str(settings.chunk_overlap))
    table.add_row("Top K", str(settings.top_k))
    
    console.print(table)


def main_entry() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_entry()

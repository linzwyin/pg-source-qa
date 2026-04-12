"""Code indexing module for building vector store."""

import fnmatch
import time
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from source_qa.config import get_settings
from source_qa.embeddings import CodeEmbedder
from source_qa.parser import CodeChunk, CodeParser

console = Console()


class CodeIndexer:
    """Indexes source code files into a vector store."""

    def __init__(
        self,
        vector_store_path: str | None = None,
        collection_name: str | None = None,
    ):
        settings = get_settings()
        self.vector_store_path = vector_store_path or settings.vector_store_path
        self.collection_name = collection_name or settings.collection_name
        
        self.parser = CodeParser(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedder = CodeEmbedder()
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.vector_store_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def should_index(self, file_path: Path, exclude_patterns: list[str]) -> bool:
        """Check if a file should be indexed based on patterns."""
        str_path = str(file_path)
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return False
            # Check if any parent directory matches
            for parent in file_path.parents:
                if fnmatch.fnmatch(str(parent) + "/", pattern):
                    return False
        
        return True

    def iter_files(
        self, directory: Path, extensions: list[str], exclude_patterns: list[str]
    ) -> Iterator[Path]:
        """Iterate over files matching criteria."""
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in extensions:
                continue
            
            if not self.should_index(file_path, exclude_patterns):
                continue
            
            yield file_path

    def index_directory(self, directory: str | Path, clear_existing: bool = False) -> dict:
        """Index all supported files in a directory."""
        directory = Path(directory)
        start_time = time.time()
        
        console.print(Panel.fit(
            f"[bold blue]Source Code Indexer[/bold blue]\n"
            f"[dim]Target: {directory.absolute()}[/dim]",
            title="🚀 Starting",
            border_style="blue"
        ))
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        settings = get_settings()
        
        if clear_existing:
            console.print("[yellow]🗑️  Clearing existing index...[/yellow]")
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        # Phase 1: Scan for files
        console.print("\n[bold cyan]Phase 1/3:[/bold cyan] Scanning for files...")
        files = list(self.iter_files(
            directory,
            settings.supported_extensions,
            settings.exclude_patterns,
        ))
        
        if not files:
            console.print("[yellow]⚠️  No files found to index.[/yellow]")
            return {"indexed_files": 0, "chunks": 0}

        console.print(f"[green]✓ Found {len(files)} files to index[/green]")

        # Phase 2: Parse files and collect chunks
        console.print("\n[bold cyan]Phase 2/3:[/bold cyan] Parsing files and generating chunks...")
        all_chunks: list[CodeChunk] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="bright_green"),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[files_per_sec]:.1f} files/s[/cyan]"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Parsing files...",
                total=len(files),
                files_per_sec=0.0,
            )
            
            parse_start = time.time()
            for idx, file_path in enumerate(files):
                chunks = self.parser.parse_file(file_path)
                all_chunks.extend(chunks)
                
                elapsed = time.time() - parse_start
                files_per_sec = (idx + 1) / elapsed if elapsed > 0 else 0
                progress.update(task, advance=1, files_per_sec=files_per_sec)

        if not all_chunks:
            console.print("[yellow]⚠️  No chunks generated from files.[/yellow]")
            return {"indexed_files": len(files), "chunks": 0}

        console.print(f"[green]✓ Generated {len(all_chunks)} chunks[/green]")

        # Phase 3: Generate embeddings and add to collection
        console.print("\n[bold cyan]Phase 3/3:[/bold cyan] Generating embeddings and indexing...")
        batch_size = 100
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="bright_green"),
            TaskProgressColumn(),
            TextColumn("[cyan]{task.fields[chunks_per_sec]:.1f} chunks/s[/cyan]"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            total_batches = (len(all_chunks) + batch_size - 1) // batch_size
            task = progress.add_task(
                "[cyan]Indexing chunks...",
                total=total_batches,
                chunks_per_sec=0.0,
            )
            
            index_start = time.time()
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                texts = [chunk.content for chunk in batch]
                embeddings = self.embedder.embed_texts(texts)
                
                ids = [f"chunk_{i + j}" for j in range(len(batch))]
                metadatas = [
                    {
                        "file_path": chunk.file_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language,
                        "chunk_type": chunk.chunk_type,
                    }
                    for chunk in batch
                ]
                
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                )
                
                elapsed = time.time() - index_start
                chunks_processed = i + len(batch)
                chunks_per_sec = chunks_processed / elapsed if elapsed > 0 else 0
                progress.update(task, advance=1, chunks_per_sec=chunks_per_sec)

        # Final summary
        total_time = time.time() - start_time
        result = {
            "indexed_files": len(files),
            "chunks": len(all_chunks),
            "collection_size": self.collection.count(),
            "time_seconds": round(total_time, 2),
        }
        
        # Create summary table
        summary_table = Table(
            title="[bold green]🎉 Indexing Complete![/bold green]",
            show_header=True,
            header_style="bold cyan",
        )
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green", justify="right")
        
        summary_table.add_row("Files Indexed", str(result["indexed_files"]))
        summary_table.add_row("Total Chunks", str(result["chunks"]))
        summary_table.add_row("Collection Size", str(result["collection_size"]))
        summary_table.add_row("Time Elapsed", f"{result['time_seconds']:.2f}s")
        summary_table.add_row("Processing Rate", f"{result['chunks'] / total_time:.1f} chunks/s")
        
        console.print("")
        console.print(summary_table)
        
        return result

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "vector_store_path": self.vector_store_path,
        }

"""Document indexing module for building vector store from PDFs."""

import time
from pathlib import Path
from typing import Iterator, List

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
from source_qa.models import DocChunk
from source_qa.parsers import PostgreSQLDocParser

console = Console()


class DocIndexer:
    """Indexes PDF documents into a vector store."""

    def __init__(
        self,
        vector_store_path: str | None = None,
        collection_name: str | None = None,
    ):
        settings = get_settings()
        self.vector_store_path = vector_store_path or settings.vector_store_path
        # Use different collection for docs
        self.collection_name = (collection_name or settings.collection_name) + "_docs"
        
        self.embedder = CodeEmbedder()
        self.parser = PostgreSQLDocParser()
        
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

    def iter_pdfs(self, directory: Path) -> Iterator[Path]:
        """Iterate over PDF files in directory."""
        for pdf_path in directory.rglob("*.pdf"):
            if pdf_path.is_file():
                yield pdf_path

    def index_pdf(self, pdf_path: Path, pages_per_chunk: int = 3) -> dict:
        """Index a single PDF file."""
        chunks_parsed = 0
        
        with self.parser.open(pdf_path) as parser:
            for doc_chunk in parser.parse_document(chunk_size=pages_per_chunk):
                chunks_parsed += 1
                yield doc_chunk
        
        return {"chunks": chunks_parsed}

    def index_directory(
        self, 
        directory: str | Path, 
        clear_existing: bool = False,
        pages_per_chunk: int = 3,
    ) -> dict:
        """Index all PDF files in a directory."""
        directory = Path(directory)
        start_time = time.time()
        
        # Handle both file and directory
        if directory.is_file() and directory.suffix.lower() == '.pdf':
            pdf_files = [directory]
            source_desc = f"PDF: {directory.name}"
        else:
            pdf_files = list(self.iter_pdfs(directory))
            source_desc = f"Directory: {directory.absolute()}"
        
        console.print(Panel.fit(
            f"[bold blue]PDF Document Indexer[/bold blue]\n"
            f"[dim]{source_desc}[/dim]",
            title="🚀 Starting",
            border_style="blue"
        ))
        
        if not pdf_files:
            console.print("[yellow]⚠️  No PDF files found.[/yellow]")
            return {"indexed_pdfs": 0, "chunks": 0}

        console.print(f"[green]✓ Found {len(pdf_files)} PDF file(s)[/green]")

        if clear_existing:
            console.print("[yellow]🗑️  Clearing existing document index...[/yellow]")
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                pass  # Collection might not exist

        # Pre-load model
        console.print("[dim]Loading embedding model...[/dim]")
        _ = self.embedder.model

        # Phase 1: Parse all PDFs and collect chunks
        console.print(f"\n[bold cyan]Phase 1/2:[/bold cyan] Parsing PDFs (pages_per_chunk={pages_per_chunk})...")
        
        all_chunks: List[DocChunk] = []
        
        for pdf_path in pdf_files:
            console.print(f"[dim]Opening: {pdf_path.name}...[/dim]")
            
            try:
                with self.parser.open(pdf_path) as parser:
                    page_count = parser.page_count
                    console.print(f"[dim]  Total pages: {page_count}[/dim]")
                    
                    # Parse with page-level progress
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(complete_style="green", finished_style="bright_green"),
                        TaskProgressColumn(),
                        console=console,
                    ) as page_progress:
                        page_task = page_progress.add_task(
                            f"[cyan]Parsing {pdf_path.name}...", 
                            total=page_count
                        )
                        
                        for doc_chunk in parser.parse_document(chunk_size=pages_per_chunk, fast_mode=True):
                            all_chunks.append(doc_chunk)
                            # Update progress by pages_per_chunk
                            page_progress.advance(page_task, pages_per_chunk)
                            
            except Exception as e:
                console.print(f"[red]Error parsing {pdf_path}: {e}[/red]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")

        if not all_chunks:
            console.print("[yellow]⚠️  No chunks generated from PDFs.[/yellow]")
            return {"indexed_pdfs": len(pdf_files), "chunks": 0}

        console.print(f"[green]✓ Generated {len(all_chunks)} chunks[/green]")

        # Phase 2: Generate embeddings and index
        console.print("\n[bold cyan]Phase 2/2:[/bold cyan] Generating embeddings and indexing...")
        
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
            task = progress.add_task(
                "[cyan]Indexing chunks...",
                total=len(all_chunks),
                chunks_per_sec=0.0,
            )
            
            index_start = time.time()
            total_processed = 0
            
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                texts = [chunk.content for chunk in batch]
                
                # Generate embeddings
                embeddings = self.embedder.embed_texts(texts)
                
                # Prepare metadata
                ids = [chunk.id for chunk in batch]
                metadatas = [
                    {
                        "source_pdf": chunk.source_pdf,
                        "chapter": chunk.chapter,
                        "section": chunk.section or "",
                        "page_number": chunk.page_number,
                        "has_tables": len(chunk.tables) > 0,
                        "has_code": len(chunk.code_examples) > 0,
                    }
                    for chunk in batch
                ]
                
                # Add to collection
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                )
                
                total_processed += len(batch)
                elapsed = time.time() - index_start
                chunks_per_sec = total_processed / elapsed if elapsed > 0 else 0
                progress.update(task, completed=total_processed, chunks_per_sec=chunks_per_sec)

        # Final summary
        total_time = time.time() - start_time
        result = {
            "indexed_pdfs": len(pdf_files),
            "chunks": len(all_chunks),
            "collection_size": self.collection.count(),
            "time_seconds": round(total_time, 2),
        }
        
        summary_table = Table(
            title="[bold green]🎉 Document Indexing Complete![/bold green]",
            show_header=True,
            header_style="bold cyan",
        )
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green", justify="right")
        
        summary_table.add_row("PDFs Indexed", str(result["indexed_pdfs"]))
        summary_table.add_row("Total Chunks", str(result["chunks"]))
        summary_table.add_row("Collection Size", str(result["collection_size"]))
        summary_table.add_row("Time Elapsed", f"{result['time_seconds']:.2f}s")
        if total_time > 0:
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

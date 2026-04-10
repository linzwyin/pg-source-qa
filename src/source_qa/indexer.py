"""Code indexing module for building vector store."""

import fnmatch
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from tqdm import tqdm

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
        console.print(f"[blue]Starting indexing...[/blue]")
        console.print(f"[dim]Directory: {directory.absolute()}[/dim]")
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        settings = get_settings()
        
        if clear_existing:
            console.print("[yellow]Clearing existing index...[/yellow]")
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        # Collect all files
        console.print("[dim]Scanning for files...[/dim]")
        files = list(self.iter_files(
            directory,
            settings.supported_extensions,
            settings.exclude_patterns,
        ))
        
        if not files:
            console.print("[yellow]No files found to index.[/yellow]")
            return {"indexed_files": 0, "chunks": 0}

        console.print(f"[green]Found {len(files)} files to index[/green]")

        # Process files and collect chunks
        all_chunks: list[CodeChunk] = []
        for file_path in tqdm(files, desc="Parsing files"):
            chunks = self.parser.parse_file(file_path)
            all_chunks.extend(chunks)

        if not all_chunks:
            console.print("[yellow]No chunks generated from files.[/yellow]")
            return {"indexed_files": len(files), "chunks": 0}

        console.print(f"[green]Generated {len(all_chunks)} chunks[/green]")

        # Generate embeddings and add to collection
        batch_size = 100
        for i in tqdm(range(0, len(all_chunks), batch_size), desc="Indexing chunks"):
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

        result = {
            "indexed_files": len(files),
            "chunks": len(all_chunks),
            "collection_size": self.collection.count(),
        }
        
        console.print(f"[green]Indexing complete: {result}[/green]")
        return result

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "vector_store_path": self.vector_store_path,
        }

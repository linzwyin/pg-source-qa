"""Knowledge graph builder for code and documentation relationships."""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from source_qa.config import get_settings
from source_qa.embeddings import CodeEmbedder
from source_qa.models import KnowledgeEdge, RelationType

console = Console()


class KnowledgeGraphBuilder:
    """Builds knowledge graph from indexed code and docs."""

    def __init__(self, vector_store_path: str | None = None):
        settings = get_settings()
        self.vector_store_path = vector_store_path or settings.vector_store_path
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.vector_store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        self.embedder = CodeEmbedder()
        self.edges: List[KnowledgeEdge] = []
        
    def get_collection(self, name: str):
        """Get a collection by name."""
        try:
            return self.client.get_collection(name)
        except Exception:
            return None
    
    def build_semantic_edges(self, max_edges: int = 1000) -> int:
        """Build semantic similarity edges between code and docs."""
        code_collection = self.get_collection("source_code")
        doc_collection = self.get_collection("source_code_docs")
        
        if not code_collection or not doc_collection:
            console.print("[yellow]Warning: Collections not found. Run index-code and index-docs first.[/yellow]")
            return 0
        
        # Get all code chunks
        code_result = code_collection.get(include=["documents", "metadatas"])
        if not code_result or not code_result["ids"]:
            console.print("[yellow]No code chunks found.[/yellow]")
            return 0
        
        code_ids = code_result["ids"]
        code_docs = code_result["documents"]
        code_metas = code_result["metadatas"]
        
        console.print(f"[dim]Found {len(code_ids)} code chunks[/dim]")
        
        # Get all doc chunks
        doc_result = doc_collection.get(include=["documents", "metadatas"])
        if not doc_result or not doc_result["ids"]:
            console.print("[yellow]No doc chunks found.[/yellow]")
            return 0
        
        doc_ids = doc_result["ids"]
        doc_docs = doc_result["documents"]
        doc_metas = doc_result["metadatas"]
        
        console.print(f"[dim]Found {len(doc_ids)} doc chunks[/dim]")
        
        edge_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Building semantic edges...", total=min(len(code_ids), max_edges))
            
            # For each code chunk, find similar doc chunks
            for i, (code_id, code_text, code_meta) in enumerate(zip(code_ids[:max_edges], code_docs[:max_edges], code_metas[:max_edges])):
                # Query doc collection with code content
                try:
                    results = doc_collection.query(
                        query_texts=[code_text[:1000]],  # Limit text length
                        n_results=3,  # Top 3 matches
                    )
                    
                    if results and results["ids"] and results["ids"][0]:
                        for j, (doc_id, distance) in enumerate(zip(results["ids"][0], results["distances"][0])):
                            # Convert distance to similarity (cosine distance)
                            similarity = 1.0 - distance
                            
                            if similarity > 0.7:  # Threshold
                                edge = KnowledgeEdge(
                                    source=code_id,
                                    target=doc_id,
                                    relation=RelationType.DOCUMENTED_IN,
                                    weight=similarity,
                                    evidence=f"Semantic similarity: {similarity:.3f}",
                                    metadata={
                                        "code_file": code_meta.get("file_path", ""),
                                        "doc_source": doc_metas[doc_ids.index(doc_id)].get("source_pdf", ""),
                                    }
                                )
                                self.edges.append(edge)
                                edge_count += 1
                
                except Exception as e:
                    console.print(f"[dim]Error querying: {e}[/dim]")
                
                progress.advance(task)
        
        return edge_count
    
    def build_code_edges(self) -> int:
        """Build edges between related code chunks."""
        collection = self.get_collection("source_code")
        if not collection:
            return 0
        
        result = collection.get(include=["metadatas"])
        if not result or not result["ids"]:
            return 0
        
        ids = result["ids"]
        metas = result["metadatas"]
        
        edge_count = 0
        
        # Group by file
        file_chunks: Dict[str, List[Tuple[str, Dict]]] = {}
        for chunk_id, meta in zip(ids, metas):
            file_path = meta.get("file_path", "")
            if file_path:
                if file_path not in file_chunks:
                    file_chunks[file_path] = []
                file_chunks[file_path].append((chunk_id, meta))
        
        # Create PART_OF edges for chunks in same file
        for file_path, chunks in file_chunks.items():
            if len(chunks) > 1:
                # Sort by line number
                chunks.sort(key=lambda x: x[1].get("start_line", 0))
                
                # Link consecutive chunks
                for i in range(len(chunks) - 1):
                    edge = KnowledgeEdge(
                        source=chunks[i][0],
                        target=chunks[i + 1][0],
                        relation=RelationType.RELATED_TO,
                        weight=0.8,
                        evidence=f"Consecutive chunks in {file_path}",
                    )
                    self.edges.append(edge)
                    edge_count += 1
        
        return edge_count
    
    def build_graph(self) -> dict:
        """Build complete knowledge graph."""
        console.print(Panel.fit(
            "[bold blue]Knowledge Graph Builder[/bold blue]",
            title="🕸️  Building",
            border_style="blue"
        ))
        
        self.edges = []
        
        # Build code-to-code edges
        console.print("\n[bold cyan]Phase 1/2:[/bold cyan] Building code relationships...")
        code_edges = self.build_code_edges()
        console.print(f"[green]✓ Created {code_edges} code edges[/green]")
        
        # Build code-to-doc edges
        console.print("\n[bold cyan]Phase 2/2:[/bold cyan] Building code-doc relationships...")
        semantic_edges = self.build_semantic_edges()
        console.print(f"[green]✓ Created {semantic_edges} semantic edges[/green]")
        
        return {
            "total_edges": len(self.edges),
            "code_edges": code_edges,
            "semantic_edges": semantic_edges,
        }
    
    def export_graph(self, output_path: str | Path) -> None:
        """Export graph to JSON file."""
        output_path = Path(output_path)
        
        graph_data = {
            "nodes": list(set(
                [e.source for e in self.edges] + [e.target for e in self.edges]
            )),
            "edges": [e.to_dict() for e in self.edges],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✓ Graph exported to {output_path}[/green]")
    
    def print_stats(self) -> None:
        """Print graph statistics."""
        table = Table(title="Knowledge Graph Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Count by relation type
        relation_counts: Dict[str, int] = {}
        for edge in self.edges:
            rel = edge.relation.value
            relation_counts[rel] = relation_counts.get(rel, 0) + 1
        
        table.add_row("Total Edges", str(len(self.edges)))
        table.add_row("Unique Nodes", str(len(set(
            [e.source for e in self.edges] + [e.target for e in self.edges]
        ))))
        
        for rel, count in sorted(relation_counts.items()):
            table.add_row(f"  {rel}", str(count))
        
        console.print(table)

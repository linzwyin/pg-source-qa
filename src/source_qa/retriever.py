"""Retrieval module for searching code chunks."""

from dataclasses import dataclass

from source_qa.config import get_settings
from source_qa.embeddings import CodeEmbedder


@dataclass
class RetrievedChunk:
    """A retrieved code chunk with similarity score."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    score: float


class CodeRetriever:
    """Retrieve relevant code chunks based on query."""

    def __init__(
        self,
        vector_store_path: str | None = None,
        collection_name: str | None = None,
    ):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        settings = get_settings()
        self.vector_store_path = vector_store_path or settings.vector_store_path
        self.collection_name = collection_name or settings.collection_name
        self.top_k = settings.top_k
        self.min_score = settings.min_similarity_score
        
        self.embedder = CodeEmbedder()
        
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.vector_store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = None

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Retrieve relevant chunks for a query."""
        if self.collection is None:
            return []

        top_k = top_k or self.top_k
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        
        chunks = []
        if results["documents"] and results["documents"][0]:
            for doc, metadata, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # Convert cosine distance to similarity score
                score = 1 - distance
                
                if score >= self.min_score:
                    chunks.append(
                        RetrievedChunk(
                            content=doc,
                            file_path=metadata["file_path"],
                            start_line=metadata["start_line"],
                            end_line=metadata["end_line"],
                            language=metadata["language"],
                            score=score,
                        )
                    )
        
        return chunks

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks into context string."""
        if not chunks:
            return "No relevant code found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}] {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})\n"
                f"```{chunk.language}\n{chunk.content}\n```\n"
            )
        
        return "\n".join(context_parts)

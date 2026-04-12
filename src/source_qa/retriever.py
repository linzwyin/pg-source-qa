"""Retrieval module for searching code chunks and documentation."""

from dataclasses import dataclass
from typing import Literal

from source_qa.config import get_settings
from source_qa.embeddings import CodeEmbedder


@dataclass
class RetrievedChunk:
    """A retrieved chunk with similarity score."""

    content: str
    source: str  # file_path for code, pdf name for docs
    source_type: Literal["code", "doc"]
    score: float
    # Code-specific fields
    file_path: str = ""
    start_line: int = 0
    end_line: int = 0
    language: str = ""
    # Doc-specific fields
    chapter: str = ""
    section: str = ""
    page_number: int = 0


class CodeRetriever:
    """Retrieve relevant chunks from both code and documentation."""

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
        self.doc_collection_name = (collection_name or settings.collection_name) + "_docs"
        self.top_k = settings.top_k
        self.min_score = settings.min_similarity_score
        
        self.embedder = CodeEmbedder()
        
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.vector_store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        # Code collection
        try:
            self.code_collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.code_collection = None
        
        # Doc collection
        try:
            self.doc_collection = self.client.get_collection(self.doc_collection_name)
        except Exception:
            self.doc_collection = None

    def retrieve(self, query: str, top_k: int | None = None, include_docs: bool = True) -> list[RetrievedChunk]:
        """Retrieve relevant chunks from code and optionally docs."""
        top_k = top_k or self.top_k
        
        # Generate query embedding once
        query_embedding = self.embedder.embed_query(query)
        query_embedding_list = [query_embedding.tolist()]
        
        all_chunks = []
        
        # 1. Search code collection
        if self.code_collection:
            code_results = self.code_collection.query(
                query_embeddings=query_embedding_list,
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            
            if code_results["documents"] and code_results["documents"][0]:
                for doc, metadata, distance in zip(
                    code_results["documents"][0],
                    code_results["metadatas"][0],
                    code_results["distances"][0],
                ):
                    score = 1 - distance
                    if score >= self.min_score:
                        all_chunks.append(
                            RetrievedChunk(
                                content=doc,
                                source=metadata.get("file_path", "unknown"),
                                source_type="code",
                                score=score,
                                file_path=metadata.get("file_path", ""),
                                start_line=metadata.get("start_line", 0),
                                end_line=metadata.get("end_line", 0),
                                language=metadata.get("language", "text"),
                            )
                        )
        
        # 2. Search doc collection (if enabled)
        if include_docs and self.doc_collection:
            doc_results = self.doc_collection.query(
                query_embeddings=query_embedding_list,
                n_results=top_k // 2,  # Fewer docs than code
                include=["documents", "metadatas", "distances"],
            )
            
            if doc_results["documents"] and doc_results["documents"][0]:
                for doc, metadata, distance in zip(
                    doc_results["documents"][0],
                    doc_results["metadatas"][0],
                    doc_results["distances"][0],
                ):
                    score = 1 - distance
                    if score >= self.min_score:
                        all_chunks.append(
                            RetrievedChunk(
                                content=doc,
                                source=metadata.get("source_pdf", "unknown.pdf"),
                                source_type="doc",
                                score=score,
                                chapter=metadata.get("chapter", ""),
                                section=metadata.get("section", ""),
                                page_number=metadata.get("page_number", 0),
                            )
                        )
        
        # Sort by score descending
        all_chunks.sort(key=lambda x: x.score, reverse=True)
        
        # Return top_k combined results
        return all_chunks[:top_k]

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks into context string."""
        if not chunks:
            return "No relevant information found."
        
        code_parts = []
        doc_parts = []
        
        for chunk in chunks:
            if chunk.source_type == "code":
                code_parts.append(
                    f"[Code] {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})\n"
                    f"```{chunk.language}\n{chunk.content[:2000]}\n```\n"
                )
            else:
                section_info = f" > {chunk.section}" if chunk.section else ""
                doc_parts.append(
                    f"[Documentation] {chunk.source} - Page {chunk.page_number}\n"
                    f"Chapter: {chunk.chapter}{section_info}\n"
                    f"{chunk.content[:2000]}\n"
                )
        
        context = []
        if code_parts:
            context.append("## Source Code Context:\n" + "\n".join(code_parts))
        if doc_parts:
            context.append("## Documentation Context:\n" + "\n".join(doc_parts))
        
        return "\n\n".join(context)

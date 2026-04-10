"""Tests for retriever module."""

import tempfile
from pathlib import Path

import pytest

from source_qa.indexer import CodeIndexer
from source_qa.retriever import CodeRetriever, RetrievedChunk


class TestCodeRetriever:
    """Test cases for CodeRetriever."""

    def test_retriever_init_no_collection(self):
        """Test retriever initialization without existing collection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            retriever = CodeRetriever(
                vector_store_path=tmpdir,
                collection_name="test_collection",
            )
            assert retriever.collection is None

    def test_retrieve_empty_index(self):
        """Test retrieval from empty index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            retriever = CodeRetriever(
                vector_store_path=tmpdir,
                collection_name="test_collection",
            )
            results = retriever.retrieve("test query")
            assert results == []

    def test_format_context_empty(self):
        """Test formatting empty context."""
        retriever = CodeRetriever()
        context = retriever.format_context([])
        assert "No relevant code found" in context

    def test_format_context_with_chunks(self):
        """Test formatting context with chunks."""
        retriever = CodeRetriever()
        chunks = [
            RetrievedChunk(
                content="def test(): pass",
                file_path="/test/file.py",
                start_line=1,
                end_line=2,
                language="python",
                score=0.9,
            )
        ]
        context = retriever.format_context(chunks)
        assert "Source 1" in context
        assert "/test/file.py" in context
        assert "def test(): pass" in context


class TestRetrieverIntegration:
    """Integration tests for retriever with indexer."""

    def test_end_to_end_retrieval(self):
        """Test end-to-end indexing and retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_dir = Path(tmpdir) / "code"
            test_dir.mkdir()
            test_file = test_dir / "test.py"
            test_file.write_text("def hello():\n    return 'Hello World'\n")
            
            # Index
            indexer = CodeIndexer(
                vector_store_path=str(Path(tmpdir) / "db"),
                collection_name="test",
            )
            indexer.index_directory(test_dir)
            
            # Retrieve
            retriever = CodeRetriever(
                vector_store_path=str(Path(tmpdir) / "db"),
                collection_name="test",
            )
            results = retriever.retrieve("hello function", top_k=3)
            
            assert len(results) > 0
            assert any("hello" in r.content.lower() for r in results)

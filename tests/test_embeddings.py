"""Tests for embeddings module."""

import numpy as np
import pytest

from source_qa.embeddings import CodeEmbedder


class TestCodeEmbedder:
    """Test cases for CodeEmbedder."""

    def test_init_default(self):
        """Test default initialization."""
        embedder = CodeEmbedder()
        assert embedder._model is None  # Lazy loading

    def test_embed_single_text(self):
        """Test embedding a single text."""
        embedder = CodeEmbedder()
        embedding = embedder.embed_query("def hello(): pass")
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1
        assert embedding.shape[0] > 0

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        embedder = CodeEmbedder()
        texts = [
            "def hello(): pass",
            "class MyClass:",
            "import os",
        ]
        embeddings = embedder.embed_texts(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        assert embeddings.ndim == 2

    def test_embed_empty_list(self):
        """Test embedding empty list."""
        embedder = CodeEmbedder()
        embeddings = embedder.embed_texts([])
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.size == 0

    def test_get_dimension(self):
        """Test getting embedding dimension."""
        embedder = CodeEmbedder()
        dim = embedder.get_dimension()
        
        assert isinstance(dim, int)
        assert dim > 0
        
        # Verify consistency
        embedding = embedder.embed_query("test")
        assert embedding.shape[0] == dim

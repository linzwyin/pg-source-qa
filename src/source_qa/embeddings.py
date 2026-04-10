"""Embedding generation for code chunks."""

from pathlib import Path
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from source_qa.config import get_settings


class CodeEmbedder:
    """Generate embeddings for code and text."""

    def __init__(self, model_name: str | None = None, device: str | None = None, local_files_only: bool = False):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.local_files_only = local_files_only
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading of the embedding model."""
        if self._model is None:
            # Check if model_name is a local path
            if self.model_name.startswith("./") or self.model_name.startswith("/") or Path(self.model_name).exists():
                print(f"Loading local model from: {self.model_name}")
                self._model = SentenceTransformer(
                    self.model_name, 
                    device=self.device,
                    local_files_only=True
                )
            else:
                # Download from HuggingFace
                self._model = SentenceTransformer(
                    self.model_name, 
                    device=self.device,
                    local_files_only=self.local_files_only
                )
        return self._model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not texts:
            return np.array([])
        
        # Normalize and encode
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 10,
        )
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query."""
        return self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.model.get_sentence_embedding_dimension()

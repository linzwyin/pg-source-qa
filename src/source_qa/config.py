"""Configuration management for Source Code QA System."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Moonshot AI API Configuration
    moonshot_api_key: str = Field(
        default="",
        description="Moonshot AI API Key",
        alias="MOONSHOT_API_KEY",
    )
    moonshot_base_url: str = Field(
        default="https://api.moonshot.cn/v1",
        description="Moonshot API Base URL",
        alias="MOONSHOT_BASE_URL",
    )
    moonshot_model: str = Field(
        default="kimi-k2-0711-preview",
        description="Default Moonshot model to use",
        alias="MOONSHOT_MODEL",
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
        alias="EMBEDDING_MODEL",
    )
    embedding_device: str = Field(
        default="cpu",
        description="Device for embedding model (cpu/cuda)",
        alias="EMBEDDING_DEVICE",
    )

    # Vector Store Configuration
    vector_store_path: str = Field(
        default="./chroma_db",
        description="Path to store ChromaDB data",
        alias="VECTOR_STORE_PATH",
    )
    collection_name: str = Field(
        default="source_code",
        description="ChromaDB collection name",
        alias="COLLECTION_NAME",
    )

    # Indexing Configuration
    chunk_size: int = Field(
        default=1000,
        description="Maximum chunk size for code splitting",
        alias="CHUNK_SIZE",
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks",
        alias="CHUNK_OVERLAP",
    )
    supported_extensions: list[str] = Field(
        default=[
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".md",
            ".rst",
            ".txt",
        ],
        description="File extensions to index",
        alias="SUPPORTED_EXTENSIONS",
    )
    exclude_patterns: list[str] = Field(
        default=[
            "node_modules/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            ".pytest_cache/",
            "*.min.js",
            "*.min.css",
            "dist/",
            "build/",
        ],
        description="Patterns to exclude from indexing",
        alias="EXCLUDE_PATTERNS",
    )

    # Query Configuration
    top_k: int = Field(
        default=5,
        description="Number of top results to retrieve",
        alias="TOP_K",
    )
    min_similarity_score: float = Field(
        default=0.5,
        description="Minimum similarity score for results",
        alias="MIN_SIMILARITY_SCORE",
    )

    @classmethod
    def from_toml(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from TOML config file."""
        import toml

        if config_path is None:
            config_path = Path(".kimi.toml")

        if not config_path.exists():
            return cls()

        config = toml.load(config_path)
        moonshot_config = config.get("moonshot", {})

        return cls(
            moonshot_api_key=moonshot_config.get("api_key", ""),
            moonshot_base_url=moonshot_config.get("base_url", "https://api.moonshot.cn/v1"),
            moonshot_model=moonshot_config.get("model", "kimi-k2-0711-preview"),
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Try to load from TOML first, then fall back to env vars
    settings = Settings.from_toml()
    
    # Override with environment variables if set
    if os.getenv("MOONSHOT_API_KEY"):
        settings.moonshot_api_key = os.getenv("MOONSHOT_API_KEY")
    
    return settings

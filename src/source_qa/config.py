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
            config_path = Path(".kimi.toml").resolve()
        else:
            config_path = Path(config_path).resolve()

        if not config_path.exists():
            print(f"[Config] Config file not found: {config_path}")
            return cls()

        print(f"[Config] Loading from: {config_path}")
        
        try:
            config = toml.load(config_path)
        except Exception as e:
            print(f"[Config] Error parsing TOML: {e}")
            return cls()
        
        # Parse sections
        moonshot_config = config.get("moonshot", {})
        embedding_config = config.get("embedding", {})
        indexing_config = config.get("indexing", {})
        
        print(f"[Config] Parsed sections: {list(config.keys())}")
        print(f"[Config] embedding_config: {embedding_config}")
        
        # Build kwargs
        kwargs = {}
        
        # Moonshot settings
        if "api_key" in moonshot_config:
            kwargs["moonshot_api_key"] = moonshot_config["api_key"]
        if "base_url" in moonshot_config:
            kwargs["moonshot_base_url"] = moonshot_config["base_url"]
        if "model" in moonshot_config:
            kwargs["moonshot_model"] = moonshot_config["model"]
            
        # Embedding settings
        if "model" in embedding_config:
            kwargs["embedding_model"] = embedding_config["model"]
            print(f"[Config] Setting embedding_model to: {embedding_config['model']}")
        if "device" in embedding_config:
            kwargs["embedding_device"] = embedding_config["device"]
            
        # Indexing settings
        if "chunk_size" in indexing_config:
            kwargs["chunk_size"] = indexing_config["chunk_size"]
        if "chunk_overlap" in indexing_config:
            kwargs["chunk_overlap"] = indexing_config["chunk_overlap"]
        
        print(f"[Config] Creating Settings with kwargs: {kwargs}")
        
        # Create instance - note: BaseSettings may override kwargs with env vars
        instance = cls(**kwargs)
        
        # Force override with TOML values to ensure TOML config takes priority
        # This handles cases where env vars exist but are empty strings
        if "moonshot_api_key" in kwargs:
            instance.moonshot_api_key = kwargs["moonshot_api_key"]
        if "moonshot_base_url" in kwargs:
            instance.moonshot_base_url = kwargs["moonshot_base_url"]
        if "moonshot_model" in kwargs:
            instance.moonshot_model = kwargs["moonshot_model"]
        if "embedding_model" in kwargs:
            instance.embedding_model = kwargs["embedding_model"]
        if "embedding_device" in kwargs:
            instance.embedding_device = kwargs["embedding_device"]
        if "chunk_size" in kwargs:
            instance.chunk_size = kwargs["chunk_size"]
        if "chunk_overlap" in kwargs:
            instance.chunk_overlap = kwargs["chunk_overlap"]
        
        print(f"[Config] Created instance with embedding_model: {instance.embedding_model}")
        return instance


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings.from_toml()
    
    # Override with environment variables if set
    if os.getenv("MOONSHOT_API_KEY"):
        settings.moonshot_api_key = os.getenv("MOONSHOT_API_KEY")
    if os.getenv("EMBEDDING_MODEL"):
        settings.embedding_model = os.getenv("EMBEDDING_MODEL")
    if os.getenv("EMBEDDING_DEVICE"):
        settings.embedding_device = os.getenv("EMBEDDING_DEVICE")
    
    print(f"[get_settings] Final embedding_model: {settings.embedding_model}")
    return settings

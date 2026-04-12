#!/usr/bin/env python3
"""Debug Settings loading."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import toml

# Step 1: Load TOML directly
print("Step 1: Load TOML")
config = toml.load(".kimi.toml")
print(f"  config: {config}")
print(f"  embedding: {config.get('embedding', {})}")

# Step 2: Get values
embedding_config = config.get("embedding", {})
model_value = embedding_config.get("model", "DEFAULT")
print(f"  model_value from TOML: {model_value}")

# Step 3: Create Settings manually
print("\nStep 2: Create Settings")
from source_qa.config import Settings

# Direct instantiation
s = Settings(
    moonshot_api_key="test",
    embedding_model=model_value,
)
print(f"  Created with embedding_model={model_value}")
print(f"  s.embedding_model: {s.embedding_model}")

# Step 4: Use from_toml
print("\nStep 3: Use from_toml")
Settings.from_toml.cache_clear()  # Clear cache if any
s2 = Settings.from_toml()
print(f"  s2.embedding_model: {s2.embedding_model}")

# Step 5: Check default values
print("\nStep 4: Check default values")
s3 = Settings()
print(f"  s3 (defaults).embedding_model: {s3.embedding_model}")

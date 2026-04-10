#!/usr/bin/env python3
"""Verify configuration loading."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("Configuration Verification")
print("=" * 60)
print()

# Clear cache and reload
print("Step 1: Checking .kimi.toml exists...")
config_file = Path(".kimi.toml")
if config_file.exists():
    print(f"✓ Found: {config_file.absolute()}")
    content = config_file.read_text()
    print("\nFile content:")
    print("-" * 40)
    print(content)
    print("-" * 40)
else:
    print(f"✗ Not found: {config_file.absolute()}")
    sys.exit(1)

print("\nStep 2: Parsing TOML...")
try:
    import toml
    config = toml.load(".kimi.toml")
    print(f"✓ Parsed successfully")
    print(f"Sections: {list(config.keys())}")
    
    if "embedding" in config:
        print(f"\n[embedding] section:")
        for k, v in config["embedding"].items():
            print(f"  {k} = {v}")
    else:
        print("\n✗ [embedding] section not found!")
        
except Exception as e:
    print(f"✗ Failed to parse: {e}")
    sys.exit(1)

print("\nStep 3: Loading with Settings class...")
try:
    # Clear any cached settings
    from source_qa.config import get_settings, Settings
    
    # Force reload by clearing cache
    get_settings.cache_clear()
    
    # Create fresh instance
    settings = Settings.from_toml()
    
    print(f"✓ Settings loaded")
    print(f"\nValues:")
    print(f"  embedding_model: {settings.embedding_model}")
    print(f"  embedding_device: {settings.embedding_device}")
    print(f"  moonshot_api_key: {'✓ set' if settings.moonshot_api_key else '✗ empty'}")
    
    # Verify it matches TOML
    expected_model = config.get("embedding", {}).get("model", "")
    if settings.embedding_model == expected_model:
        print(f"\n✓ Config matches! Model: {settings.embedding_model}")
    else:
        print(f"\n✗ Config mismatch!")
        print(f"  Expected: {expected_model}")
        print(f"  Got: {settings.embedding_model}")
        print(f"\nTroubleshooting:")
        print(f"  1. Make sure you reinstalled: pip install -e '.[dev]' --force-reinstall")
        print(f"  2. Check if .kimi.toml is in the correct location")
        
except Exception as e:
    print(f"✗ Failed to load settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Done")
print("=" * 60)

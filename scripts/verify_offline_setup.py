#!/usr/bin/env python3
"""Verify offline setup on server."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_model():
    """Check if model is available locally."""
    print("=" * 60)
    print("Offline Setup Verification")
    print("=" * 60)
    print()
    
    # 1. Check for models directory
    models_dir = Path("./models")
    if models_dir.exists():
        print(f"✓ Models directory exists: {models_dir.absolute()}")
        
        # List models
        model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
        if model_dirs:
            print(f"  Found {len(model_dirs)} model(s):")
            for m in model_dirs:
                print(f"    - {m.name}")
        else:
            print("  ✗ No models found in directory")
            return False
    else:
        print(f"✗ Models directory not found: {models_dir.absolute()}")
        return False
    
    # 2. Try to load model
    print()
    print("Testing model loading...")
    
    try:
        from source_qa.config import get_settings
        settings = get_settings()
        
        print(f"Model path from config: {settings.embedding_model}")
        
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(
            settings.embedding_model,
            device="cpu",
            local_files_only=True
        )
        
        # Test encoding
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        
        print(f"✓ Model loaded successfully!")
        print(f"  Dimension: {len(embedding)}")
        print(f"  Sample values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure model files are in ./models/")
        print("2. Update .kimi.toml with correct model path")
        print("3. Ensure model was downloaded completely")
        return False

def check_config():
    """Check configuration."""
    print()
    print("Checking configuration...")
    
    config_file = Path(".kimi.toml")
    if config_file.exists():
        print(f"✓ Config file exists: {config_file.absolute()}")
        
        # Read and display
        content = config_file.read_text()
        print("  Content:")
        for line in content.split("\n"):
            if "api_key" in line and "=" in line:
                # Hide API key
                key_part = line.split("=")[0]
                print(f"    {key_part}= ***")
            else:
                print(f"    {line}")
    else:
        print(f"✗ Config file not found: {config_file.absolute()}")
        print("  Create one with: cp .kimi.toml.example .kimi.toml")
        return False
    
    return True

def main():
    success = True
    
    if not check_model():
        success = False
    
    if not check_config():
        success = False
    
    print()
    print("=" * 60)
    if success:
        print("✓ All checks passed! Ready for offline use.")
        print()
        print("You can now run:")
        print("  pg-qa index-code ./data/postgres")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()

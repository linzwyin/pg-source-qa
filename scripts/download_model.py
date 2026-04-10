#!/usr/bin/env python3
"""Download embedding model for offline use."""

import argparse
import sys
from pathlib import Path

def download_model(model_name: str, output_dir: str):
    """Download a sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        sys.exit(1)
    
    output_path = Path(output_dir) / model_name.replace("/", "--")
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading model: {model_name}")
    print(f"Output directory: {output_path.absolute()}")
    print("")
    
    # Download model
    model = SentenceTransformer(model_name)
    
    # Save to local directory
    model.save(str(output_path))
    
    print("")
    print(f"✓ Model saved to: {output_path.absolute()}")
    print("")
    print("To use on offline server:")
    print(f"1. Copy this directory to your server:")
    print(f"   scp -r {output_path} user@server:/path/to/pg-source-qa/models/")
    print(f"")
    print(f"2. Update .kimi.toml:")
    print(f"   [embedding]")
    print(f'   model = "./models/{model_name.replace("/", "--")}"')
    print(f"   device = \"cpu\"")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Download embedding model for offline use")
    parser.add_argument(
        "--model",
        "-m",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Model name to download (default: sentence-transformers/all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./models",
        help="Output directory (default: ./models)"
    )
    
    args = parser.parse_args()
    
    download_model(args.model, args.output)

if __name__ == "__main__":
    main()

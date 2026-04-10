#!/usr/bin/env python3
"""Script to download PostgreSQL source code."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def download_postgres(version: str, output_dir: Path, shallow: bool = True) -> Path:
    """Download PostgreSQL source code from GitHub.
    
    Args:
        version: PostgreSQL version (e.g., "16.3", "master", "REL_16_STABLE")
        output_dir: Directory to clone into
        shallow: Whether to do a shallow clone (faster)
        
    Returns:
        Path to cloned repository
    """
    repo_url = "https://github.com/postgres/postgres.git"
    
    target_dir = output_dir / "postgres"
    
    # Check if git is available
    if not shutil.which("git"):
        print("Error: git is not installed or not in PATH")
        sys.exit(1)
    
    # Clone repository
    if target_dir.exists():
        print(f"Directory {target_dir} already exists. Pulling latest changes...")
        subprocess.run(["git", "-C", str(target_dir), "pull"], check=True)
    else:
        print(f"Cloning PostgreSQL repository to {target_dir}...")
        
        cmd = ["git", "clone"]
        if shallow:
            cmd.extend(["--depth", "1"])
        cmd.extend(["--branch", version, repo_url, str(target_dir)])
        
        subprocess.run(cmd, check=True)
    
    print(f"PostgreSQL source downloaded to: {target_dir}")
    
    # Print some stats
    result = subprocess.run(
        ["git", "-C", str(target_dir), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"Commit: {result.stdout.strip()}")
    
    # Count source files
    c_files = list(target_dir.rglob("*.c"))
    h_files = list(target_dir.rglob("*.h"))
    print(f"C source files: {len(c_files)}")
    print(f"Header files: {len(h_files)}")
    
    return target_dir


def main():
    parser = argparse.ArgumentParser(
        description="Download PostgreSQL source code"
    )
    parser.add_argument(
        "--version",
        "-v",
        default="REL_16_STABLE",
        help="PostgreSQL version to download (default: REL_16_STABLE)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./data"),
        help="Output directory (default: ./data)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Do a full clone instead of shallow clone",
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    try:
        download_postgres(
            version=args.version,
            output_dir=args.output,
            shallow=not args.full,
        )
        print("\nDownload complete!")
        print(f"Next steps:")
        print(f"  1. Download PostgreSQL documentation PDF from:")
        print(f"     https://www.postgresql.org/files/documentation/pdf/16/postgresql-16-A4.pdf")
        print(f"  2. Place the PDF in: {args.output / 'docs'}")
        print(f"  3. Run: pg-qa index-code {args.output / 'postgres'}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDownload cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()

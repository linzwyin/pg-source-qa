#!/bin/bash
# Setup script for Source Code QA System
# Run this script to set up the development environment

set -e

echo "Setting up Source Code QA System..."

# Check Python version
python --version

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Create .kimi.toml from example if it doesn't exist
if [ ! -f ".kimi.toml" ]; then
    echo "Creating .kimi.toml from example..."
    cp .kimi.toml.example .kimi.toml
    echo "Please edit .kimi.toml and add your Moonshot API key"
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .kimi.toml and add your Moonshot API key"
echo "2. Run 'source-qa --help' to see available commands"
echo "3. Run 'source-qa index <directory>' to index your code"

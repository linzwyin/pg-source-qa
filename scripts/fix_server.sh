#!/bin/bash
# Fix CLI on server - Run this on your server

set -e

echo "=============================================="
echo "  Fixing pg-qa CLI"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo ""
echo "Project root: $PROJECT_ROOT"

# Step 1: Check Python
echo ""
echo -e "${YELLOW}Step 1: Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}python3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "Python: $PYTHON_VERSION"

# Step 2: Activate virtual environment
echo ""
echo -e "${YELLOW}Step 2: Activating virtual environment...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated .venv"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated venv"
else
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Creating new venv..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

which python
echo "Pip: $(which pip)"

# Step 3: Uninstall old version
echo ""
echo -e "${YELLOW}Step 3: Uninstalling old version...${NC}"
pip uninstall pg-source-qa -y 2>/dev/null || true

# Step 4: Reinstall
echo ""
echo -e "${YELLOW}Step 4: Reinstalling package...${NC}"
pip install -e ".[dev]"

# Step 5: Check generated scripts
echo ""
echo -e "${YELLOW}Step 5: Checking generated scripts...${NC}"
VENV_BIN=".venv/bin"
if [ -f "$VENV_BIN/pg-qa" ]; then
    echo -e "${GREEN}✓ pg-qa script found${NC}"
    head -5 "$VENV_BIN/pg-qa"
else
    echo -e "${RED}✗ pg-qa script not found${NC}"
fi

# Step 6: Test import
echo ""
echo -e "${YELLOW}Step 6: Testing import...${NC}"
if python -c "from source_qa.cli import app; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ Import successful${NC}"
else
    echo -e "${RED}✗ Import failed${NC}"
    echo "Trying with PYTHONPATH..."
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    if python -c "from source_qa.cli import app; print('OK')" 2>/dev/null; then
        echo -e "${GREEN}✓ Import successful with PYTHONPATH${NC}"
    else
        echo -e "${RED}✗ Still failing${NC}"
    fi
fi

# Step 7: Test CLI
echo ""
echo -e "${YELLOW}Step 7: Testing CLI...${NC}"
if command -v pg-qa &> /dev/null; then
    echo -e "${GREEN}✓ pg-qa in PATH${NC}"
    echo "Running: pg-qa --help"
    pg-qa --help && echo -e "${GREEN}✓ CLI working!${NC}" || echo -e "${RED}✗ CLI failed${NC}"
else
    echo -e "${RED}✗ pg-qa not in PATH${NC}"
    echo "Trying direct path..."
    if [ -f "$VENV_BIN/pg-qa" ]; then
        "$VENV_BIN/pg-qa" --help && echo -e "${GREEN}✓ CLI working (direct path)!${NC}" || echo -e "${RED}✗ CLI failed${NC}"
    fi
fi

# Step 8: Alternative test
echo ""
echo -e "${YELLOW}Step 8: Alternative test (python -m)...${NC}"
python -m source_qa.cli --help && echo -e "${GREEN}✓ Module execution working!${NC}" || echo -e "${RED}✗ Module execution failed${NC}"

echo ""
echo "=============================================="
echo "  Fix script complete"
echo "=============================================="
echo ""
echo "If CLI still not working, try:"
echo "  1. export PYTHONPATH=$PROJECT_ROOT/src:\$PYTHONPATH"
echo "  2. python -m source_qa.cli --help"
echo ""

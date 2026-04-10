#!/usr/bin/env pwsh
# upload_to_github.ps1 - Upload PostgreSQL Source QA System to GitHub

param(
    [Parameter(Mandatory=$true, HelpMessage="Your GitHub username")]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "pg-source-qa",
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "PostgreSQL Source Code & Documentation QA System"
)

$ErrorActionPreference = "Stop"

function Write-Header($text) {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success($text) {
    Write-Host "✓ $text" -ForegroundColor Green
}

function Write-Warning($text) {
    Write-Host "⚠ $text" -ForegroundColor Yellow
}

function Write-Error($text) {
    Write-Host "✗ $text" -ForegroundColor Red
}

Write-Header "GitHub Upload Script"

# Check git installation
Write-Host "Checking Git installation..." -ForegroundColor Yellow
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed!"
    Write-Host ""
    Write-Host "Please install Git first:" -ForegroundColor Cyan
    Write-Host "  https://git-scm.com/download/win" -ForegroundColor White
    Write-Host ""
    exit 1
}

$gitVersion = git --version
Write-Success "Git found: $gitVersion"

# Check if in correct directory
$currentDir = Get-Location
Write-Host ""
Write-Host "Current directory: $currentDir" -ForegroundColor Gray

if (!(Test-Path "pyproject.toml")) {
    Write-Error "Not in project root directory!"
    Write-Host "Please run this script from the project root." -ForegroundColor Yellow
    exit 1
}

Write-Success "In project directory"

# Initialize git if needed
Write-Host ""
Write-Host "Checking Git repository..." -ForegroundColor Yellow
if (!(Test-Path ".git")) {
    Write-Warning "Git repository not found. Initializing..."
    git init
    
    # Configure git user if not set
    $gitName = git config user.name
    $gitEmail = git config user.email
    
    if (!$gitName) {
        git config user.name "Developer"
        Write-Success "Set git user.name"
    }
    if (!$gitEmail) {
        git config user.email "dev@example.com"
        Write-Success "Set git user.email"
    }
} else {
    Write-Success "Git repository already initialized"
}

# Check remote
Write-Host ""
Write-Host "Checking remote repository..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/$Username/$RepoName.git"
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    Write-Warning "Remote 'origin' already exists: $existingRemote"
    $changeRemote = Read-Host "Do you want to change it to $remoteUrl ? (y/n)"
    if ($changeRemote -eq "y") {
        git remote set-url origin $remoteUrl
        Write-Success "Updated remote URL"
    }
} else {
    git remote add origin $remoteUrl
    Write-Success "Added remote: $remoteUrl"
}

# Check for .gitignore
Write-Host ""
Write-Host "Checking .gitignore..." -ForegroundColor Yellow
if (!(Test-Path ".gitignore")) {
    Write-Warning ".gitignore not found! Creating default..."
    @"
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
.kimi.toml
chroma_db/
vector_store/
*.sqlite3
*.db
data/
logs/
cache/

# OS
.DS_Store
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding utf8
    Write-Success "Created .gitignore"
}

# Add all files
Write-Host ""
Write-Host "Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Success "Added files to staging area"

# Check status
$status = git status --porcelain
if (!$status) {
    Write-Warning "No changes to commit. Everything is already tracked."
} else {
    Write-Host ""
    Write-Host "Files to be committed:" -ForegroundColor Gray
    git status --short | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    # Commit
    Write-Host ""
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m "Initial commit: PostgreSQL Source Code QA System

Core Features:
- Tree-sitter based C code parser for PostgreSQL
- PDF documentation parser with layout preservation
- Vector indexing with ChromaDB and BGE embeddings
- Hybrid retrieval (Dense + BM25 + Reranking)
- CLI tool with Typer and Rich
- Web interface with Streamlit
- FastAPI backend

Documentation:
- Development plan and architecture design
- Dependency documentation
- Index command guide"
    
    Write-Success "Changes committed"
}

# Rename branch to main
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host ""
    Write-Host "Renaming branch to 'main'..." -ForegroundColor Yellow
    git branch -M main
    Write-Success "Branch renamed to 'main'"
}

# Push
Write-Host ""
Write-Header "Pushing to GitHub"
Write-Host "Repository: $remoteUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "You may be prompted to authenticate with GitHub." -ForegroundColor Yellow
Write-Host ""

try {
    git push -u origin main
    
    Write-Header "Upload Complete!"
    Write-Success "Project successfully uploaded to GitHub"
    Write-Host ""
    Write-Host "Repository URL: " -NoNewline
    Write-Host $remoteUrl -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Visit your repository: $remoteUrl" -ForegroundColor White
    Write-Host "  2. Add a description and topics" -ForegroundColor White
    Write-Host "  3. Create a README badge" -ForegroundColor White
    Write-Host "  4. Share with others!" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Error "Failed to push to GitHub"
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "  1. Create the repository on GitHub first:" -ForegroundColor White
    Write-Host "     https://github.com/new" -ForegroundColor Cyan
    Write-Host "  2. Check your authentication:" -ForegroundColor White
    Write-Host "     - Use Git Credential Manager" -ForegroundColor Gray
    Write-Host "     - Or create a Personal Access Token" -ForegroundColor Gray
    Write-Host "  3. Check your internet connection" -ForegroundColor White
    Write-Host ""
    Write-Host "For detailed instructions, see: GITHUB_UPLOAD_GUIDE.md" -ForegroundColor Cyan
}

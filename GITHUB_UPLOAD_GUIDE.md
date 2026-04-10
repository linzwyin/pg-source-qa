# 上传项目到 GitHub 完整指南

## 步骤 1: 安装 Git

### Windows
1. 下载 Git: https://git-scm.com/download/win
2. 运行安装程序，使用默认选项
3. 重启终端或 VS Code

验证安装:
```powershell
git --version
```

### 配置 Git
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 步骤 2: 初始化 Git 仓库

在项目根目录执行:

```powershell
cd f:\Source_code_QA_system

# 初始化 git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: PostgreSQL Source Code QA System

- Add core architecture for code and document parsing
- Implement Tree-sitter based C code parser
- Implement PDF parser for documentation
- Add vector indexing with ChromaDB
- Setup CLI with Typer
- Add development documentation"
```

---

## 步骤 3: 创建 GitHub 仓库

### 方式 A: 通过 GitHub 网站创建

1. 访问 https://github.com/new
2. 填写信息:
   - **Repository name**: `pg-source-qa` (或你喜欢的名字)
   - **Description**: `PostgreSQL Source Code & Documentation QA System`
   - **Visibility**: Public 或 Private
   - **Initialize**: 不要勾选 "Add a README" (我们已经有了)
3. 点击 "Create repository"

### 方式 B: 通过 GitHub CLI (可选)

```powershell
# 安装 GitHub CLI: https://cli.github.com/
# 登录
gh auth login

# 创建仓库
gh repo create pg-source-qa --public --source=. --push
```

---

## 步骤 4: 推送到 GitHub

创建仓库后，GitHub 会显示类似以下的命令:

```powershell
# 添加远程仓库 (替换为你的用户名)
git remote add origin https://github.com/YOUR_USERNAME/pg-source-qa.git

# 推送代码
git branch -M main
git push -u origin main
```

---

## 完整命令脚本

以下是完整的 PowerShell 脚本，保存为 `upload_to_github.ps1`:

```powershell
#!/usr/bin/env pwsh
# upload_to_github.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$RepoName,
    
    [string]$Description = "PostgreSQL Source Code & Documentation QA System"
)

$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Uploading to GitHub" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 git
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed. Please install Git first: https://git-scm.com/download/win"
    exit 1
}

# 检查是否在 git 仓库中
if (!(Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git config user.name "Developer"
    git config user.email "dev@example.com"
}

# 添加所有文件
Write-Host "Adding files to git..." -ForegroundColor Yellow
git add .

# 检查是否有变更要提交
$status = git status --porcelain
if ($status) {
    Write-Host "Committing changes..." -ForegroundColor Yellow
    git commit -m "Initial commit: PostgreSQL Source Code QA System`n`n- Add core architecture`n- Implement code and PDF parsers`n- Add vector indexing`n- Setup CLI"
} else {
    Write-Host "No changes to commit" -ForegroundColor Green
}

# 添加远程仓库
Write-Host "Setting up remote repository..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/$Username/$RepoName.git"

# 检查是否已有 remote
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
}

# 重命名分支为 main
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch to 'main'..." -ForegroundColor Yellow
    git branch -M main
}

# 推送
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host "  Successfully uploaded to GitHub!" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository URL: $remoteUrl" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Error "Failed to push. Make sure:`n1. You have created the repository on GitHub`n2. You have the correct permissions`n3. You are authenticated (run: git login or use SSH)"
}
```

使用方式:
```powershell
.\upload_to_github.ps1 -Username "your-github-username" -RepoName "pg-source-qa"
```

---

## 步骤 5: 验证上传

推送完成后，检查 GitHub 仓库:

```powershell
# 查看远程仓库
$remoteUrl = git remote get-url origin
Write-Host "Remote URL: $remoteUrl"

# 浏览器打开仓库
Start-Process $remoteUrl
```

---

## 常见问题

### Q1: 身份验证失败

**症状:**
```
fatal: Authentication failed for 'https://github.com/...'
```

**解决方案:**

方式 A - 使用 Git Credential Manager:
```powershell
# Git 会弹出窗口让你登录 GitHub
```

方式 B - 使用 Personal Access Token:
1. 访问 https://github.com/settings/tokens
2. 生成 Token (勾选 repo 权限)
3. 使用 Token 作为密码:
```powershell
git push
# Username: your-username
# Password: ghp_xxxxxxxx (你的 token)
```

方式 C - 使用 SSH:
```powershell
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 添加公钥到 GitHub: https://github.com/settings/keys
# 修改 remote 为 SSH
git remote set-url origin git@github.com:USERNAME/REPO.git
```

### Q2: 推送被拒绝

**症状:**
```
! [rejected]        main -> main (fetch first)
```

**解决方案:**
```powershell
# 先拉取远程变更
git pull origin main --rebase

# 然后再推送
git push origin main
```

### Q3: 文件太大推送失败

**症状:**
```
remote: error: File xxx is too large
```

**解决方案:**
```powershell
# 检查大文件
find . -type f -size +10M

# 添加到 .gitignore
echo "*.pdf" >> .gitignore
echo "chroma_db/" >> .gitignore
echo "*.sqlite3" >> .gitignore

# 移除已跟踪的大文件
git rm --cached path/to/large/file
git commit -m "Remove large files"
git push
```

---

## 文件结构预览

上传后，你的 GitHub 仓库应该包含:

```
pg-source-qa/
├── .env.example
├── .gitignore
├── .kimi.toml.example
├── GITHUB_UPLOAD_GUIDE.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── docs/
│   ├── DEVELOPMENT_PLAN.md
│   ├── DEPENDENCIES.md
│   └── INDEX_COMMAND_GUIDE.md
├── scripts/
│   ├── check_deps.py
│   ├── download_postgres.py
│   ├── setup.ps1
│   └── setup.sh
├── src/
│   └── source_qa/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── embeddings.py
│       ├── indexer.py
│       ├── models/
│       ├── parser.py
│       ├── parsers/
│       ├── qa_engine.py
│       └── retriever.py
└── tests/
```

---

## 后续操作

上传后建议:

1. **设置分支保护** (如果是团队项目)
   - Settings → Branches → Add rule
   - 要求 Pull Request 审查

2. **启用 GitHub Actions** (CI/CD)
   - 创建 `.github/workflows/test.yml`

3. **添加 Topics**
   - 点击仓库页面的齿轮图标
   - 添加: `postgresql`, `rag`, `ai`, `code-analysis`

4. **创建 Release**
   - 版本号从 v0.1.0 开始

# 故障排除指南

## 问题: 执行 `pg-qa index-code ./data/postgres` 没有反应

### 可能的原因和解决方案

#### 1. 命令名不匹配 (已修复)

**问题**: 第一版代码中命令定义为 `index`，但文档写的是 `index-code`

**解决**: 
```bash
# 使用正确的命令名
pg-qa index ./data/postgres

# 或更新代码后使用
pg-qa index-code ./data/postgres
```

#### 2. 虚拟环境未激活

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 验证
which pg-qa  # 应该显示虚拟环境路径
```

#### 3. 目录不存在

```bash
# 检查目录是否存在
ls ./data/postgres

# 如果不存在，先下载
python scripts/download_postgres.py
```

#### 4. 缺少依赖

```bash
# 重新安装依赖
pip install -e ".[dev]"

# 检查依赖
python scripts/check_deps.py
```

#### 5. 查看详细错误信息

修改命令，添加 `--verbose` 参数：

```python
# cli.py 中添加调试输出
@app.command(name="index-code")
def index_code(..., verbose: bool = typer.Option(False, "--verbose", "-v")):
    if verbose:
        console.print(f"[dim]Directory: {directory}[/dim]")
        console.print(f"[dim]Exists: {directory.exists()}[/dim]")
    ...
```

#### 6. 直接运行 Python 调试

```bash
# 绕过 CLI，直接运行
python -c "
from source_qa.indexer import CodeIndexer
from pathlib import Path

indexer = CodeIndexer()
result = indexer.index_directory(Path('./data/postgres'))
print(result)
"
```

---

## 如何验证命令是否注册

```bash
# 列出所有可用命令
pg-qa --help

# 应该显示:
# Commands:
#   chat         Start an interactive chat session
#   config       Show current configuration
#   index-code   Index source code directory
#   query        Ask a single question
#   stats        Show index statistics
```

如果 `index-code` 没有列出，说明命令没有正确注册。

---

## 重新安装以应用修复

```bash
# 1. 确保在虚拟环境中
.venv\Scripts\activate

# 2. 重新安装 (可编辑模式)
pip install -e ".[dev]" --force-reinstall

# 3. 验证命令
pg-qa --help
```

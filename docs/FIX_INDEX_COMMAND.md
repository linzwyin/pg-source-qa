# 修复 `pg-qa index-code` 无响应问题

## 问题描述

执行 `pg-qa index-code ./data/postgres` 后没有反应/输出。

## 根本原因

### 1. 命令名不匹配 ❌

**问题**: CLI 中定义的命令名是 `index`，但文档和用户执行的是 `index-code`

```python
# cli.py 中原代码
@app.command()
def index(...):  # ← 这生成的命令是 `pg-qa index`，不是 `index-code`
```

**修复**:
```python
@app.command(name="index-code")  # ← 显式指定命令名
def index_code(...):  # ← 函数名也改为 index_code 更清晰
```

### 2. 初始化时检查 API Key ❌

**问题**: `CodeQASystem.__init__` 在初始化时就检查 API Key，但索引操作并不需要它

```python
# qa_engine.py
class CodeQASystem:
    def __init__(self):
        if not settings.moonshot_api_key:
            raise ValueError("Moonshot API key not configured...")  # ← 这里会报错
```

**修复**: 在 `index-code` 命令中直接使用 `CodeIndexer`，不通过 `CodeQASystem`

```python
# cli.py
from source_qa.indexer import CodeIndexer  # 直接导入

indexer = CodeIndexer()  # 不需要 API Key
result = indexer.index_directory(...)
```

### 3. 缺少启动输出

**问题**: 开始处理前没有输出，用户不知道程序是否在运行

**修复**: 添加明确的启动信息

```python
console.print("[bold blue]PostgreSQL Source Code Indexer[/bold blue]")
console.print(f"[dim]Directory: {directory.absolute()}[/dim]")
```

---

## 修复步骤

### 步骤 1: 更新代码

确保以下修改已应用到 `src/source_qa/cli.py`:

```python
@app.command(name="index-code")  # 明确指定命令名
def index_code(
    directory: Path = typer.Argument(...),
    clear: bool = typer.Option(False, "--clear", "-c"),
) -> None:
    """Index source code directory."""
    try:
        # 直接导入 CodeIndexer，不通过 CodeQASystem
        from source_qa.indexer import CodeIndexer
        
        console.print("[bold blue]PostgreSQL Source Code Indexer[/bold blue]")
        console.print("")
        
        indexer = CodeIndexer()
        result = indexer.index_directory(str(directory), clear_existing=clear)
        
        # 显示结果...
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
```

### 步骤 2: 重新安装

```bash
# 确保在虚拟环境中
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 重新安装以应用更改
pip install -e ".[dev]" --force-reinstall
```

### 步骤 3: 验证命令

```bash
# 查看帮助，确认 index-code 命令存在
pg-qa --help

# 应该显示:
# Commands:
#   index-code   Index source code directory
```

### 步骤 4: 测试运行

```bash
# 先创建测试目录（如果没有）
mkdir -p data/postgres

# 或者直接运行
pg-qa index-code ./data/postgres
```

**预期输出**:
```
PostgreSQL Source Code Indexer

Starting indexing...
Directory: F:\Source_code_QA_system\data\postgres
Scanning for files...
Found 3247 files to index
Generated 12547 chunks
...
✓ Indexing complete!
```

---

## 调试方法

### 方法 1: 直接运行测试脚本

```bash
python scripts/test_index.py
```

### 方法 2: 使用 Python -m 运行

```bash
python -m source_qa.cli index-code ./data/postgres
```

### 方法 3: 添加 --verbose 标志（可选）

修改 cli.py 添加详细输出:

```python
@app.command(name="index-code")
def index_code(
    directory: Path = ...,
    verbose: bool = typer.Option(False, "--verbose", "-v"),  # 添加 verbose 选项
):
    if verbose:
        console.print(f"[dim]Arguments: {directory}[/dim]")
        console.print(f"[dim]Directory exists: {directory.exists()}[/dim]")
```

---

## 常见问题

### Q: 为什么修改后还是需要 API Key？

**A**: 确认你修改的是 `index_code` 函数，使用了 `from source_qa.indexer import CodeIndexer`，而不是 `CodeQASystem`。

### Q: 为什么还是没有输出？

**A**: 检查：
1. 是否重新安装了？`pip install -e ".[dev]" --force-reinstall`
2. 是否在正确的虚拟环境中？`which pg-qa`
3. 目录是否存在？`ls ./data/postgres`

### Q: 如何确认命令已注册？

**A**: 
```bash
pg-qa --help
# 查看 Commands 列表中是否有 index-code
```

---

## 完整修复后的 cli.py 关键部分

```python
from source_qa.indexer import CodeIndexer  # 顶部导入

@app.command(name="index-code")
def index_code(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing source code to index",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        "-c",
        help="Clear existing index before indexing",
    ),
) -> None:
    """Index source code directory."""
    try:
        from source_qa.indexer import CodeIndexer
        
        console.print("[bold blue]PostgreSQL Source Code Indexer[/bold blue]")
        console.print("")
        
        indexer = CodeIndexer()
        result = indexer.index_directory(str(directory), clear_existing=clear)
        
        table = Table(title="Indexing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in result.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print("")
        console.print(table)
        console.print("")
        console.print("[green]✓ Indexing complete![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
```

---

## 验证清单

- [ ] 修改了 `@app.command()` 为 `@app.command(name="index-code")`
- [ ] 修改了函数名为 `def index_code(...)`
- [ ] 使用 `from source_qa.indexer import CodeIndexer` 直接导入
- [ ] 添加了启动输出 `console.print("[bold blue]PostgreSQL Source Code Indexer[/bold blue]")`
- [ ] 添加了错误堆栈输出 `console.print(f"[dim]{traceback.format_exc()}[/dim]")`
- [ ] 运行了 `pip install -e ".[dev]" --force-reinstall`
- [ ] 运行 `pg-qa --help` 确认 `index-code` 命令存在
- [ ] 测试运行 `pg-qa index-code ./data/postgres` 有输出

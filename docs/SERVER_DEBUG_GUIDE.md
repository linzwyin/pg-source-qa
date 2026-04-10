# 服务器调试指南

如果你在服务器上运行 `pg-qa` 没有输出，请按以下步骤排查。

---

## 第 1 步：检查基本环境

```bash
# 1. 检查 Python
python --version
which python

# 2. 检查是否在虚拟环境中
which python
# 应该显示类似: /path/to/project/.venv/bin/python

# 3. 检查 pg-qa 位置
which pg-qa
# 或
where pg-qa  # Windows
```

**如果 `which pg-qa` 没有输出**，说明命令不在 PATH 中。

---

## 第 2 步：重新安装（确保正确）

```bash
# 1. 进入项目目录
cd /path/to/pg-source-qa

# 2. 确保虚拟环境已激活
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 3. 验证 pip 路径
which pip
# 应该显示 .venv 中的 pip

# 4. 完全重新安装
pip uninstall pg-source-qa -y
pip install -e ".[dev]"

# 5. 验证安装
pip show pg-source-qa
```

---

## 第 3 步：检查生成的脚本

```bash
# 查找生成的脚本
ls -la .venv/bin/pg*  # Linux/Mac
# 或
dir .venv\Scripts\pg*  # Windows

# 查看脚本内容
cat .venv/bin/pg-qa  # Linux/Mac
# 或
type .venv\Scripts\pg-qa-script.py  # Windows
```

**脚本内容应该类似**:
```python
#!/path/to/.venv/bin/python
# -*- coding: utf-8 -*-
import re
import sys
from source_qa.cli import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
```

---

## 第 4 步：直接运行 Python 模块

绕过 `pg-qa` 命令，直接运行 Python 模块：

```bash
# 方法 1: 使用 -m 运行
cd /path/to/pg-source-qa
python -m source_qa.cli --help

# 方法 2: 直接导入运行
python -c "from source_qa.cli import app; app(['--help'])"
```

**如果有输出**，说明 CLI 代码本身没问题，问题在入口脚本生成。

**如果没有输出或报错**，说明代码有问题，查看错误信息。

---

## 第 5 步：运行诊断脚本

将以下脚本保存为 `diagnose.py` 并运行：

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print("="*60)
print("Diagnostics")
print("="*60)
print(f"\nPython: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Project: {project_root}")
print(f"Src: {src_path} (exists: {src_path.exists()})")

print("\n--- Testing Import ---")
try:
    from source_qa.cli import app
    print("✓ Import successful")
    print(f"App: {app}")
    
    print("\n--- Testing --help ---")
    try:
        app(["--help"])
    except SystemExit:
        pass  # --help 会调用 sys.exit()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
```

运行:
```bash
python diagnose.py
```

---

## 第 6 步：检查常见错误

### 错误 1: ImportError

```
ModuleNotFoundError: No module named 'source_qa'
```

**解决**:
```bash
# 确保在项目根目录
export PYTHONPATH=/path/to/pg-source-qa/src:$PYTHONPATH
python -m source_qa.cli --help
```

### 错误 2: 没有写入权限

**解决**:
```bash
# 检查目录权限
ls -la .venv/bin/

# 可能需要使用 --user 或检查虚拟环境所有权
```

### 错误 3: 多个 Python 版本冲突

```bash
# 明确使用虚拟环境的 Python
.venv/bin/python -m source_qa.cli --help
```

---

## 第 7 步：手动创建入口脚本

如果 pip 没有正确生成脚本，手动创建：

### Linux/Mac

创建 `.venv/bin/pg-qa`:
```bash
cat > .venv/bin/pg-qa << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/python" -m source_qa.cli "$@"
EOF

chmod +x .venv/bin/pg-qa
```

### Windows

创建 `.venv/Scripts/pg-qa.bat`:
```batch
@echo off
"%~dp0python.exe" -m source_qa.cli %*
```

---

## 第 8 步：验证修复

```bash
# 1. 验证命令存在
which pg-qa

# 2. 测试帮助
pg-qa --help

# 3. 测试索引
pg-qa index-code ./data/postgres --clear
```

---

## 快速修复脚本

在服务器上运行以下脚本：

```bash
#!/bin/bash
# fix_cli.sh

cd /path/to/pg-source-qa

echo "=== Step 1: Check environment ==="
which python
python --version

echo "=== Step 2: Activate venv ==="
source .venv/bin/activate

echo "=== Step 3: Reinstall ==="
pip uninstall pg-source-qa -y
pip install -e ".[dev]"

echo "=== Step 4: Test direct import ==="
python -c "from source_qa.cli import app; print('Import OK')"

echo "=== Step 5: Test CLI ==="
pg-qa --help

echo "=== Done ==="
```

---

## 仍然有问题？

如果以上步骤都无法解决，请提供以下信息：

1. **操作系统和版本**: `uname -a` 或 `cat /etc/os-release`
2. **Python 版本**: `python --version`
3. **pip 版本**: `pip --version`
4. **诊断脚本输出**: `python scripts/diagnose_cli.py`
5. **直接运行结果**: `python -m source_qa.cli --help 2>&1`

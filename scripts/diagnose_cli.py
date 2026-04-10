#!/usr/bin/env python3
"""Diagnose CLI issues."""

import sys
import os
from pathlib import Path
from subprocess import run, PIPE

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_python():
    print_section("Python Environment")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")

def check_path():
    print_section("PATH Environment")
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for i, p in enumerate(path_dirs[:10]):  # 只显示前10个
        print(f"  {i+1}. {p}")
    if len(path_dirs) > 10:
        print(f"  ... and {len(path_dirs) - 10} more")

def find_pg_qa():
    print_section("Looking for pg-qa")
    
    # 方法1: 使用 where/which
    result = run(["where", "pg-qa"], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print(f"Found via 'where': {result.stdout.strip()}")
    else:
        print("'where pg-qa' failed")
    
    # 方法2: 检查 Scripts 目录
    venv_scripts = Path(sys.executable).parent / "Scripts"
    if venv_scripts.exists():
        print(f"\nChecking {venv_scripts}:")
        pg_qa_exe = venv_scripts / "pg-qa.exe"
        pg_qa_script = venv_scripts / "pg-qa-script.py"
        
        if pg_qa_exe.exists():
            print(f"  ✓ Found: {pg_qa_exe}")
        else:
            print(f"  ✗ Not found: {pg_qa_exe}")
            
        if pg_qa_script.exists():
            print(f"  ✓ Found: {pg_qa_script}")
        else:
            print(f"  ✗ Not found: {pg_qa_script}")

def check_package():
    print_section("Package Installation")
    
    # 检查 pip list
    result = run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
    lines = result.stdout.split("\n")
    for line in lines:
        if "pg-source" in line.lower() or "source-qa" in line.lower():
            print(f"  Installed: {line}")

def test_import():
    print_section("Testing Imports")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        print("✓ Added src to path")
        
        import source_qa
        print(f"✓ import source_qa: OK (version: {source_qa.__version__})")
        
        from source_qa import cli
        print("✓ from source_qa import cli: OK")
        
        from source_qa.cli import app
        print("✓ from source_qa.cli import app: OK")
        
        # 尝试调用 --help
        print("\n  Testing CLI --help:")
        import typer
        from io import StringIO
        
        # 重定向 stdout 捕获输出
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            app(["--help"])
        except SystemExit:
            pass
        
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        if output:
            print(f"  ✓ CLI --help output captured ({len(output)} chars)")
            print(f"\n  First 500 chars:\n{output[:500]}...")
        else:
            print("  ✗ No output from --help")
            
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()

def test_entry_point():
    print_section("Testing Entry Point")
    
    try:
        from source_qa.cli import main_entry
        print("✓ main_entry imported")
        
        # 不真正调用，只检查是否存在
        print(f"  main_entry type: {type(main_entry)}")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def check_pyproject():
    print_section("pyproject.toml Configuration")
    
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject.exists():
        print(f"✓ Found: {pyproject}")
        
        content = pyproject.read_text()
        if "[project.scripts]" in content:
            print("✓ [project.scripts] section found")
            
            # 提取 scripts 部分
            lines = content.split("\n")
            in_scripts = False
            for line in lines:
                if "[project.scripts]" in line:
                    in_scripts = True
                    print("\n  Scripts defined:")
                elif in_scripts:
                    if line.strip().startswith("["):
                        break
                    if line.strip():
                        print(f"    {line}")
        else:
            print("✗ [project.scripts] section NOT found")
    else:
        print(f"✗ Not found: {pyproject}")

def run_pg_qa_directly():
    print_section("Running pg-qa directly")
    
    # 尝试多种方式运行
    
    # 方式1: 使用当前 Python 解释器运行模块
    print("\n1. Running: python -m source_qa.cli --help")
    result = run([sys.executable, "-m", "source_qa.cli", "--help"], 
                 capture_output=True, text=True, 
                 cwd=Path(__file__).parent.parent)
    print(f"   Return code: {result.returncode}")
    if result.stdout:
        print(f"   stdout: {result.stdout[:500]}")
    if result.stderr:
        print(f"   stderr: {result.stderr[:500]}")

def main():
    print("="*60)
    print("  CLI Diagnostics Tool")
    print("="*60)
    
    check_python()
    check_path()
    find_pg_qa()
    check_package()
    check_pyproject()
    test_import()
    test_entry_point()
    run_pg_qa_directly()
    
    print_section("Diagnostics Complete")
    print("If you see errors above, please share the output.")

if __name__ == "__main__":
    main()

# pg-qa index-code 命令详解

本文档详细说明 `pg-qa index-code ./data/postgres` 命令的完整执行流程、依赖交互和输出结果。

## 命令概述

```bash
pg-qa index-code ./data/postgres [OPTIONS]
```

该命令用于索引 PostgreSQL 源代码目录，提取其中的函数、结构体、宏定义等代码实体，生成向量嵌入并存储到向量数据库中。

---

## 执行流程图

```
用户执行: pg-qa index-code ./data/postgres
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: CLI 参数解析 (Typer)                                     │
│ ├── 解析命令行参数                                               │
│ ├── 验证目录存在性                                               │
│ └── 加载配置文件 (.kimi.toml)                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  --clear        │ │  --workers      │ │  --batch-size   │
│  清空现有索引   │ │  并行工作线程   │ │  批处理大小     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: 初始化组件                                               │
│ ├── 创建 PostgreSQLCodeParser (Tree-sitter)                      │
│ ├── 初始化 CodeEmbedder (SentenceTransformers)                   │
│ └── 连接 ChromaDB 向量数据库                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: 文件扫描                                                 │
│ ├── 遍历 ./data/postgres 目录                                    │
│ ├── 筛选 *.c 和 *.h 文件                                         │
│ └── 排除测试文件和第三方库                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         ┌──────────────────────────────────────┐
         │ 找到的文件示例:                       │
         │ - src/backend/executor/execMain.c    │
         │ - src/backend/executor/execProcnode.c│
         │ - src/include/executor/executor.h    │
         │ - ... (约 3000+ 文件)                │
         └──────────────────┬───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: 代码解析 (Tree-sitter)                                   │
│ 对每个文件:                                                      │
│ ├── 读取文件内容                                                 │
│ ├── 生成 AST (Abstract Syntax Tree)                              │
│ ├── 提取函数定义 (function_definition)                           │
│ ├── 提取结构体 (struct_specifier)                                │
│ ├── 提取宏定义 (#define)                                         │
│ └── 提取注释 (docstring)                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
         ┌──────────────────────────────────────┐
         │ 解析结果示例:                         │
         │                                      │
         │ Entity: ExecutorRun                  │
         │ Type: FUNCTION                       │
         │ File: executor/execMain.c            │
         │ Lines: 234-312                       │
         │ Signature: void ExecutorRun(...)     │
         │ Docstring: /** ... */                │
         └──────────────────┬───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: 批量嵌入生成 (SentenceTransformers)                      │
│ ├── 准备文本批次 (默认 64 个实体/批)                             │
│ ├── 调用嵌入模型 (BGE-large-zh-v1.5)                             │
│ ├── 生成 1024 维向量                                             │
│ └── 归一化处理                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: 向量存储 (ChromaDB)                                      │
│ ├── 构建元数据 (文件路径、行号、类型等)                          │
│ ├── 批量插入到 collection                                        │
│ └── 更新索引统计信息                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: 后处理与报告                                             │
│ ├── 生成索引统计报告                                             │
│ ├── 保存处理日志                                                 │
│ └── 显示完成摘要                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 详细执行步骤

### Step 1: CLI 参数解析

**依赖交互:**
- **Typer**: 命令行参数解析和验证
- **Pydantic**: 配置模型验证
- **Rich**: 终端输出美化

**代码示例:**
```python
@app.command()
def index_code(
    directory: Path = typer.Argument(..., exists=True, file_okay=False),
    clear: bool = typer.Option(False, "--clear", "-c"),
    workers: int = typer.Option(4, "--workers", "-w"),
    batch_size: int = typer.Option(64, "--batch-size", "-b"),
):
    """Index PostgreSQL source code directory."""
```

**处理过程:**
1. 解析 `directory` 参数，验证路径存在且为目录
2. 检查 `--clear` 标志，决定是否清空现有索引
3. 读取 `--workers` 设置并行度（默认为 4）
4. 读取 `--batch-size` 设置嵌入批处理大小（默认为 64）

**输出示例:**
```
PostgreSQL Source Code Indexer
==============================
Source directory: F:\data\postgres
Clear existing: False
Workers: 4
Batch size: 64
```

---

### Step 2: 初始化组件

**依赖交互:**

| 组件 | 依赖库 | 作用 |
|------|--------|------|
| 代码解析器 | `tree-sitter`, `tree-sitter-c` | 解析 C 语言 AST |
| 嵌入模型 | `sentence-transformers`, `FlagEmbedding` | 生成语义向量 |
| 向量数据库 | `chromadb` | 存储向量索引 |
| 配置管理 | `pydantic-settings` | 加载 API Key 等配置 |

**初始化流程:**

```python
# 1. 加载配置
settings = get_settings()  # 从 .kimi.toml 和环境变量加载

# 2. 初始化代码解析器
parser = PostgreSQLCodeParser()  # 加载 tree-sitter-c grammar

# 3. 初始化嵌入模型
embedder = CodeEmbedder(
    model_name="BAAI/bge-large-zh-v1.5",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# 4. 连接 ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="pg_code",
    metadata={"hnsw:space": "cosine"}
)
```

**嵌入模型加载输出:**
```
Loading embedding model: BAAI/bge-large-zh-v1.5
Device: cuda
Vector dimension: 1024
```

---

### Step 3: 文件扫描

**依赖交互:**
- **Python pathlib**: 目录遍历和文件筛选
- **fnmatch**: 模式匹配

**文件筛选规则:**

```python
INCLUDE_PATTERNS = ["*.c", "*.h"]
EXCLUDE_PATTERNS = [
    "**/test/**",
    "**/tests/**", 
    "**/*_test.c",
    "**/tmp_*",
    "**/.git/**",
]

KEY_DIRECTORIES = [
    "src/backend",      # 后端实现
    "src/include",      # 头文件
    "src/common",       # 公共代码
    "src/port",         # 平台适配
]
```

**扫描过程:**

```
Scanning directory: ./data/postgres

Found source files:
  src/backend/executor/
    ├── execMain.c          ✓
    ├── execProcnode.c      ✓
    ├── execScan.c          ✓
    └── ... (52 files)
  
  src/backend/optimizer/
    ├── plan/
    ├── prep/
    ├── util/
    └── ... (89 files)
  
  src/include/
    ├── executor/
    ├── optimizer/
    ├── storage/
    └── ... (400+ header files)

Total: 3,247 files to process
```

---

### Step 4: 代码解析 (Tree-sitter)

**依赖交互:**
- **tree-sitter**: 核心解析引擎
- **tree-sitter-c**: C 语言 grammar

**解析过程详解:**

#### 4.1 读取文件并生成 AST

```python
# 读取文件
source_bytes = file_path.read_bytes()

# 解析为 AST
tree = parser.parse_bytes(source_bytes)
root_node = tree.root_node
```

**AST 结构示例:**
```
translation_unit [0:0 - 312:0]
├── preproc_include [0:0 - 0:18]
├── function_definition [45:0 - 78:1]  ← ExecutorRun
│   ├── type: primitive_type [45:0 - 45:4] "void"
│   ├── declarator: function_declarator [45:5 - 45:40]
│   │   ├── declarator: identifier [45:5 - 45:15] "ExecutorRun"
│   │   └── parameters: parameter_list [45:15 - 45:40]
│   └── body: compound_statement [46:0 - 78:1]
├── function_definition [80:0 - 120:1]  ← ExecutorFinish
└── ...
```

#### 4.2 提取函数定义

```python
def extract_function(node, source, file_path):
    # 获取函数名
    func_name = extract_function_name(node.child_by_field_name("declarator"))
    # Result: "ExecutorRun"
    
    # 提取签名
    signature = extract_signature(node, source)
    # Result: "void ExecutorRun(QueryDesc *queryDesc, ..."
    
    # 提取文档注释
    docstring = extract_docstring(node, source)
    # Result: "/**\n * ExecutorRun - Main executor routine...\n */"
    
    return CodeEntity(
        id=f"func:executor/execMain.c:ExecutorRun",
        type=CodeEntityType.FUNCTION,
        name="ExecutorRun",
        file_path="src/backend/executor/execMain.c",
        start_line=234,
        end_line=312,
        content="void ExecutorRun(...) { ... }",
        signature=signature,
        docstring=docstring,
    )
```

#### 4.3 提取结构体

```python
# 提取 struct QueryDesc
def extract_struct(node, source, file_path):
    name = node.child_by_field_name("name").text  # "QueryDesc"
    
    return CodeEntity(
        id=f"struct:include/nodes/execnodes.h:QueryDesc",
        type=CodeEntityType.STRUCT,
        name="QueryDesc",
        file_path="src/include/nodes/execnodes.h",
        start_line=45,
        end_line=89,
        content="typedef struct QueryDesc { ... } QueryDesc;",
    )
```

#### 4.4 提取宏定义

```python
# 使用正则提取 #define
macro_pattern = r'^\s*#define\s+(\w+)\s*(.*)$'

# 示例: #define MAXATTR 100
# 提取: name="MAXATTR", value="100"
```

**解析进度输出:**
```
Parsing source files...
[████████████████████░░░░░░░░░░░░░░░░░░░░] 52% (1,687/3,247)

Current: src/backend/optimizer/plan/planner.c
  Found: 23 functions, 4 structs, 15 macros
```

---

### Step 5: 嵌入生成 (SentenceTransformers)

**依赖交互:**
- **sentence-transformers**: 嵌入模型推理
- **torch**: 张量计算（GPU 加速）
- **numpy**: 向量处理
- **tqdm**: 进度显示

**嵌入生成流程:**

```python
# 1. 准备文本批次
batch = [
    "void ExecutorRun(QueryDesc *queryDesc, ...",  # 函数签名
    "struct QueryDesc { CmdType operation; ...",    # 结构体定义
    "#define MAXATTR 100",                           # 宏定义
    ...
]

# 2. 调用嵌入模型
embeddings = embedder.model.encode(
    batch,
    batch_size=64,
    convert_to_numpy=True,
    normalize_embeddings=True,  # 归一化，便于余弦相似度计算
    show_progress_bar=True,
)

# 3. 输出: 1024 维向量矩阵
# Shape: (64, 1024)
```

**嵌入示例:**

```
Entity: ExecutorRun
Text: "void ExecutorRun(QueryDesc *queryDesc, ScanDirection direction, ..."
Embedding: [0.023, -0.156, 0.089, ..., 0.042]  (1024 dimensions)
Norm: 1.0 (L2 normalized)

Entity: QueryDesc
Text: "typedef struct QueryDesc { CmdType operation; PlannedStmt *plannedstmt; ..."
Embedding: [0.045, -0.078, 0.134, ..., -0.023]  (1024 dimensions)
Norm: 1.0
```

**GPU 加速输出:**
```
Generating embeddings...
Device: cuda:0
Model: BAAI/bge-large-zh-v1.5
Batch size: 64

Progress: 100%|████████████████████| 45/45 batches [02:34<00:00, 3.42s/batch]
Total entities: 2,847
Embedding shape: (2847, 1024)
```

---

### Step 6: 向量存储 (ChromaDB)

**依赖交互:**
- **chromadb**: 向量数据库存储和索引
- **numpy**: 向量序列化

**存储过程:**

```python
# 1. 构建元数据
metadatas = [
    {
        "entity_type": "function",
        "name": "ExecutorRun",
        "file_path": "src/backend/executor/execMain.c",
        "start_line": 234,
        "end_line": 312,
        "line_count": 79,
        "docstring_length": 256,
    },
    ...
]

# 2. 构建文档列表
documents = [
    "void ExecutorRun(QueryDesc *queryDesc, ScanDirection direction, uint64 count)",
    ...
]

# 3. 生成唯一 IDs
ids = [
    "func:executor/execMain.c:ExecutorRun",
    ...
]

# 4. 批量插入到 ChromaDB
collection.add(
    ids=ids,
    embeddings=embeddings.tolist(),
    metadatas=metadatas,
    documents=documents,
)
```

**ChromaDB 内部存储结构:**

```
Collection: pg_code
├── embedding_function: default
├── metadata: {"hnsw:space": "cosine"}
├── count: 12,547 entities
│
└── Documents:
    ├── id: "func:executor/execMain.c:ExecutorRun"
    │   ├── embedding: [1024 float values]
    │   ├── metadata: {type: "function", name: "ExecutorRun", ...}
    │   └── document: "void ExecutorRun(...)"
    │
    ├── id: "struct:nodes/execnodes.h:QueryDesc"
    │   ├── embedding: [1024 float values]
    │   └── ...
    │
    └── ...
```

**存储进度输出:**
```
Storing embeddings to ChromaDB...
Collection: pg_code
Database path: ./chroma_db

Batch: 100%|████████████████████| 45/45 [00:23<00:00, 1.95it/s]

Total entities stored: 12,547
  - Functions: 8,234
  - Structs: 1,567
  - Macros: 2,389
  - Variables: 357
```

---

### Step 7: 后处理与报告

**生成的输出:**

#### 7.1 终端输出

```
╔════════════════════════════════════════════════════════════════╗
║           Indexing Complete - Summary Report                   ║
╚════════════════════════════════════════════════════════════════╝

Source Directory: ./data/postgres
Processing Time: 3m 42s

Files Processed:
  ├─ Total files scanned: 3,247
  ├─ Successfully parsed: 3,198
  └─ Failed/Skipped: 49

Entities Extracted:
  ├─ Functions: 8,234
  ├─ Structs/Unions: 1,567
  ├─ Enums: 234
  ├─ Macros: 2,389
  ├─ Typedefs: 456
  └─ Variables: 667
  ─────────────────────────
  Total: 13,547 entities

Vector Store:
  ├─ Collection: pg_code
  ├─ Vector dimension: 1024
  ├─ Index type: HNSW (cosine)
  └─ Storage path: ./chroma_db

Top 10 Largest Functions:
  1. execMain.c:standard_ExecutorRun (245 lines)
  2. planner.c:subquery_planner (198 lines)
  3. nodeNestloop.c:ExecNestLoop (187 lines)
  ...

Most Referenced Functions:
  1. palloc (2,345 callers)
  2. ereport (1,987 callers)
  3. lappend (1,543 callers)
  ...

✓ Indexing complete! Ready for queries.
```

#### 7.2 生成的文件

```
./chroma_db/
├── chroma.sqlite3              # 元数据存储
└── <uuid>/
    ├── index/
    │   ├── header.bin          # HNSW 索引头
    │   └── data_level0.bin     # 向量数据
    └── id_to_uuid/

./logs/
└── index_2024-01-15_14-32-18.log  # 详细处理日志
    ├── 文件列表
    ├── 解析错误
    ├── 警告信息
    └── 性能统计

./cache/
└── embeddings_cache.pkl         # 嵌入向量缓存（可选）
```

#### 7.3 JSON 报告

```json
{
  "timestamp": "2024-01-15T14:32:18",
  "command": "index-code ./data/postgres",
  "duration_seconds": 222,
  "source_directory": "./data/postgres",
  "files": {
    "total": 3247,
    "parsed": 3198,
    "failed": 49
  },
  "entities": {
    "functions": 8234,
    "structs": 1567,
    "enums": 234,
    "macros": 2389,
    "typedefs": 456,
    "variables": 667,
    "total": 13547
  },
  "vector_store": {
    "collection": "pg_code",
    "dimension": 1024,
    "metric": "cosine",
    "path": "./chroma_db"
  },
  "largest_functions": [
    {"name": "standard_ExecutorRun", "file": "execMain.c", "lines": 245},
    {"name": "subquery_planner", "file": "planner.c", "lines": 198}
  ],
  "most_referenced": [
    {"name": "palloc", "callers": 2345},
    {"name": "ereport", "callers": 1987}
  ]
}
```

---

## 依赖交互详细说明

### 1. Tree-sitter (代码解析)

```python
# 依赖: tree-sitter, tree-sitter-c

# 加载语言库
import tree_sitter_c as tstc
from tree_sitter import Language, Parser

language = Language(tstc.language(), "c")
parser = Parser()
parser.set_language(language)

# 解析文件
tree = parser.parse(source_bytes)
```

**性能指标:**
- 解析速度: ~50,000 LOC/秒
- 内存使用: ~200MB 峰值
- 准确率: > 98% (C 代码)

### 2. SentenceTransformers (嵌入生成)

```python
# 依赖: sentence-transformers, torch, numpy

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
embeddings = model.encode(texts, device="cuda")
```

**性能指标:**
- 模型大小: ~1.3 GB
- 推理速度: ~100 texts/秒 (GPU)
- 向量维度: 1024
- 内存使用: ~2 GB GPU / ~3 GB RAM

### 3. ChromaDB (向量存储)

```python
# 依赖: chromadb

import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("pg_code")
```

**性能指标:**
- 写入速度: ~500 entities/秒
- 查询延迟: < 50ms (10K 实体)
- 存储大小: ~60 MB (10K entities × 1024 dims)

### 4. Typer + Rich (CLI)

```python
# 依赖: typer, rich

import typer
from rich.console import Console
from rich.progress import Progress

app = typer.Typer()
console = Console()
```

---

## 常见问题与解决方案

### Q1: 内存不足 (OOM)

**症状:**
```
RuntimeError: CUDA out of memory
```

**解决方案:**
```bash
# 减小批处理大小
pg-qa index-code ./data/postgres --batch-size 32

# 或使用 CPU
export CUDA_VISIBLE_DEVICES=""
pg-qa index-code ./data/postgres
```

### Q2: 解析错误过多

**症状:**
```
Failed to parse 500+ files
```

**原因:**
- PostgreSQL 使用 GNU C 扩展
- 部分文件使用了复杂的宏

**解决方案:**
```bash
# 查看详细日志
cat logs/index_*.log | grep ERROR

# 跳过特定目录
pg-qa index-code ./data/postgres --exclude "**/contrib/**"
```

### Q3: 索引速度太慢

**优化建议:**
```bash
# 1. 使用更多工作线程
pg-qa index-code ./data/postgres --workers 8

# 2. 使用 GPU 加速嵌入生成
# (需要安装 torch with CUDA)

# 3. 使用 SSD 存储向量数据库
# ChromaDB 在 SSD 上性能更好
```

---

## 完整命令参考

```bash
# 基本用法
pg-qa index-code ./data/postgres

# 清空现有索引并重建
pg-qa index-code ./data/postgres --clear

# 使用 8 个工作线程
pg-qa index-code ./data/postgres --workers 8

# 减小批处理大小以节省内存
pg-qa index-code ./data/postgres --batch-size 32

# 指定自定义向量数据库路径
pg-qa index-code ./data/postgres --db-path ./custom_chroma_db

# 显示详细进度
pg-qa index-code ./data/postgres --verbose

# 组合使用
pg-qa index-code ./data/postgres \
  --clear \
  --workers 8 \
  --batch-size 64 \
  --verbose
```

---

## 总结

`pg-qa index-code` 命令通过以下步骤完成 PostgreSQL 源码索引:

1. **文件扫描** → 找到所有 *.c 和 *.h 文件 (~3000+ 文件)
2. **AST 解析** → Tree-sitter 提取函数、结构体、宏 (~13K+ 实体)
3. **嵌入生成** → BGE 模型生成 1024 维向量
4. **向量存储** → ChromaDB 持久化存储
5. **报告生成** → 统计信息、日志、JSON 报告

**总耗时:** 约 3-5 分钟（取决于硬件配置）

**最终产出:**
- 可查询的向量索引
- 详细的索引统计
- 持久化的元数据

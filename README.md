# PostgreSQL Source Code QA System

一个专业的 PostgreSQL 源码与文档问答系统，能够深度理解 PostgreSQL C 语言源代码，结合官方 PDF 文档，回答关于 PostgreSQL 内部原理的各种问题。

## 功能特性

- 🔍 **源码深度解析**: 使用 Tree-sitter 解析 PostgreSQL C 源码，提取函数、结构体、宏定义
- 📚 **PDF 文档理解**: 解析官方 PDF 文档，保留章节结构和代码示例
- 🔗 **代码-文档关联**: 智能建立代码实体与文档描述的映射关系
- 🧠 **语义检索**: 基于向量 + BM25 的混合检索
- 💬 **智能问答**: 基于 Moonshot Kimi 的自然语言问答，引用具体源码位置
- 🌐 **中英双语**: 支持中文提问，获取详细解答

## 技术栈

| 组件 | 技术 | CPU/GPU |
|------|------|---------|
| **LLM** | Moonshot Kimi K2 | 云端 API，无需本地 GPU |
| **RAG** | LlamaIndex | CPU 运行 |
| **向量库** | ChromaDB | CPU 运行 |
| **代码解析** | Tree-sitter (C grammar) | CPU 运行 |
| **PDF 解析** | PyMuPDF + pdfplumber | CPU 运行 |
| **嵌入模型** | BGE-large / MiniLM | **支持 CPU** |
| **Web UI** | Streamlit / Gradio | CPU 运行 |
| **API** | FastAPI | CPU 运行 |

✅ **所有组件都支持纯 CPU 运行，无需 GPU 即可部署！**

### 🚀 纯 CPU 快速开始 (5 分钟)

```bash
# 1. 克隆并安装
git clone https://github.com/your-username/pg-source-qa.git
cd pg-source-qa
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. 配置 API Key
cp .kimi.toml.example .kimi.toml
# 编辑 .kimi.toml，填入你的 Moonshot API Key

# 3. 下载 PostgreSQL 源码并索引
python scripts/download_postgres.py
pg-qa index-code ./data/postgres

# 4. 开始问答！
pg-qa chat
```

详细步骤参见 [纯 CPU 快速启动指南](docs/QUICK_START_CPU.md)

---

## 快速开始

### 1. 环境要求

**软件:**
- Python 3.10+
- Git (用于下载 PostgreSQL 源码)
- Moonshot AI API Key

**硬件:**
- **CPU**: 支持 CPU 运行，无需 GPU！
- **最小配置**: 4核 CPU + 8GB 内存
- **推荐配置**: 8核 CPU + 16GB 内存

> 💡 **GPU 需求?** 不需要！系统默认在 CPU 上运行。GPU 只在索引阶段加速 4-10 倍，日常查询几乎无差异。详见 [CPU 部署指南](docs/CPU_DEPLOYMENT.md)

### 2. 安装

```bash
# 克隆仓库
git clone <your-repo-url>
cd pg-source-qa

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 3. 准备数据

```bash
# 下载 PostgreSQL 源码
pg-qa download-source --version 16 --output ./data/postgres

# 下载官方文档 (手动下载后放到 data/docs/)
# https://www.postgresql.org/files/documentation/pdf/16/postgresql-16-A4.pdf
```

### 4. 配置

复制配置模板并填写 API Key：

```bash
cp .kimi.toml.example .kimi.toml
```

编辑 `.kimi.toml`：

```toml
[moonshot]
api_key = "sk-your-api-key-here"
base_url = "https://api.moonshot.cn/v1"
model = "kimi-k2-0711-preview"
```

### 5. 构建索引

```bash
# 索引 PostgreSQL 源码
pg-qa index-code ./data/postgres

# 索引官方文档
pg-qa index-docs ./data/docs/postgresql-16-A4.pdf

# 构建代码-文档关联
pg-qa build-knowledge-graph
```

### 6. 使用

#### 命令行

```bash
# 单次查询
pg-qa query "ExecInitNode 函数的作用是什么？"

# 交互式聊天
pg-qa chat

# 查看索引状态
pg-qa status
```

#### Web 界面

```bash
streamlit run src/source_qa/web/app.py
```

#### Python API

```python
from source_qa import PGQASystem

# 初始化系统
qa = PGQASystem()

# 提问
answer = qa.query("解释 PostgreSQL 的 MVCC 机制")
print(answer)

# 查看引用的源码
for source in answer.sources:
    print(f"{source.file_path}:{source.line_start}-{source.line_end}")
    print(source.content)
```

## 示例问题

```
- "ExecutorRun 的执行流程是什么？"
- "heap_insert 函数是如何工作的？"
- "PostgreSQL 的锁机制有哪些类型？"
- "查询优化器如何选择执行计划？"
- "WAL (Write-Ahead Log) 的作用是什么？"
- "Buffer Manager 的工作原理？"
- "什么是 PostgreSQL 的 Memory Contexts？"
- "死锁检测是如何实现的？"
```

## 项目结构

```
pg-source-qa/
├── src/
│   └── source_qa/
│       ├── __init__.py
│       ├── cli.py              # 命令行接口
│       ├── config.py           # 配置管理
│       ├── models/             # 数据模型
│       │   ├── code_entity.py  # 代码实体
│       │   ├── doc_chunk.py    # 文档块
│       │   └── knowledge_edge.py
│       ├── parsers/            # 解析器
│       │   ├── code_parser.py  # 代码解析 (Tree-sitter)
│       │   └── pdf_parser.py   # PDF 解析
│       ├── indexers/           # 索引模块
│       │   ├── code_indexer.py
│       │   └── doc_indexer.py
│       ├── retrievers/         # 检索模块
│       │   ├── hybrid_retriever.py
│       │   └── reranker.py
│       ├── qa_engine.py        # 问答引擎
│       └── web/                # Web 界面
│           └── app.py
├── tests/                      # 测试代码
├── docs/                       # 项目文档
│   ├── CPU_DEPLOYMENT.md       # CPU 部署指南
│   ├── DEVELOPMENT_PLAN.md     # 开发计划
│   ├── DEPENDENCIES.md         # 依赖说明
│   └── INDEX_COMMAND_GUIDE.md  # 索引命令详解
├── scripts/                    # 工具脚本
│   ├── setup.ps1
│   └── setup.sh
├── data/                       # 数据目录 (gitignored)
│   ├── postgres/               # PostgreSQL 源码
│   └── docs/                   # PDF 文档
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [QUICK_START_CPU.md](docs/QUICK_START_CPU.md) | **纯 CPU 快速启动指南** - 5 分钟启动系统 |
| [CPU_DEPLOYMENT.md](docs/CPU_DEPLOYMENT.md) | CPU 部署详细指南 - 硬件要求、性能对比、优化建议 |
| [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | 完整开发计划 - 架构设计、里程碑、技术选型 |
| [DEPENDENCIES.md](docs/DEPENDENCIES.md) | 依赖库详细说明 |
| [INDEX_COMMAND_GUIDE.md](docs/INDEX_COMMAND_GUIDE.md) | `pg-qa index-code` 命令详解 |
| [CLI_COMMAND_GUIDE.md](docs/CLI_COMMAND_GUIDE.md) | `pg-qa` 命令生成原理详解 |
| [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md) | GitHub 上传指南 |

---

## 上传到 GitHub

### 自动上传脚本

```powershell
# 运行上传脚本
.\upload_to_github.ps1 -Username "your-github-username" -RepoName "pg-source-qa"
```

### 手动上传

```bash
# 1. 初始化 Git 仓库
git init

# 2. 添加文件
git add .

# 3. 提交
git commit -m "Initial commit: PostgreSQL Source Code QA System"

# 4. 添加远程仓库 (替换 your-username)
git remote add origin https://github.com/your-username/pg-source-qa.git

# 5. 推送
git branch -M main
git push -u origin main
```

详细指南参见 [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)

## 开发计划

参见 [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MOONSHOT_API_KEY` | Moonshot API Key | - |
| `MOONSHOT_MODEL` | 使用的模型 | `kimi-k2-0711-preview` |
| `EMBEDDING_MODEL` | 嵌入模型 | `BAAI/bge-large-zh-v1.5` |
| `VECTOR_STORE_PATH` | 向量存储路径 | `./chroma_db` |
| `CHUNK_SIZE` | 代码分块大小 | `1000` |
| `TOP_K` | 检索结果数量 | `5` |

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License

## 致谢

- [PostgreSQL](https://www.postgresql.org/) - 世界上最先进的开源关系数据库
- [Moonshot AI](https://www.moonshot.cn/) - Kimi 大模型
- [LlamaIndex](https://www.llamaindex.ai/) - RAG 框架

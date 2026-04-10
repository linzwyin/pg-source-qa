# PostgreSQL 源码问答系统 - 开发计划

## 项目概述

构建一个专业的 PostgreSQL 知识问答系统，能够：
- 深度理解 PostgreSQL 源代码结构（C 语言）
- 解析官方 PDF 文档
- 关联代码与文档，提供准确的回答
- 支持中文和英文问答

---

## Phase 1: 需求分析与技术选型

### 1.1 核心需求分析

| 需求项 | 描述 | 优先级 |
|--------|------|--------|
| 源码解析 | 解析 PostgreSQL C 源码，提取函数、结构体、宏定义 | P0 |
| PDF 解析 | 提取官方 PDF 文档内容，保留章节结构 | P0 |
| 代码-文档关联 | 建立代码实体与文档描述的映射关系 | P1 |
| 语义检索 | 基于语义的代码和文档检索 | P0 |
| 问答系统 | 支持自然语言问答，引用源码和文档 | P0 |
| 多语言支持 | 支持中文提问，返回答案 | P1 |

### 1.2 技术选型

#### 核心技术栈

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **LLM** | Moonshot Kimi K2 | 支持长上下文，代码理解能力强 |
| **RAG 框架** | LlamaIndex + 自定义 | 灵活的检索增强生成 |
| **向量数据库** | ChromaDB / Milvus | 支持大规模向量检索 |
| **代码解析** | Tree-sitter (C grammar) | 准确的 C 代码 AST 解析 |
| **PDF 解析** | PyMuPDF + pdfplumber | 保留布局，提取文本和表格 |
| **嵌入模型** | BGE-large / GTE-large | 中文 + 代码语义理解好 |
| **Web 界面** | Streamlit / Gradio | 快速搭建交互界面 |
| **API 服务** | FastAPI | 高性能异步 API |

#### 为什么选这些技术？

```
PostgreSQL 源码特点：
├── C 语言代码（90%+）
├── 复杂的宏定义和条件编译
├── 特定的内存管理机制
├── 复杂的执行器/优化器逻辑
└── 大量注释说明

PDF 文档特点：
├── 多列布局
├── 代码示例块
├── 表格和图示
├── 章节层次结构
└── 交叉引用
```

---

## Phase 2: 核心架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Web UI    │  │   CLI Tool  │  │      API Endpoint       │  │
│  │  (Streamlit)│  │  (Rich CLI) │  │      (FastAPI)          │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Processing Layer                       │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Query Parser  │  │ Intent Class. │  │ Context Assembler   │ │
│  │               │  │               │  │                     │ │
│  └───────┬───────┘  └───────┬───────┘  └──────────┬──────────┘ │
└──────────┼──────────────────┼─────────────────────┼────────────┘
           │                  │                     │
           └──────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Retrieval Layer (Hybrid)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Code Retriever │  │  Doc Retriever  │  │ Graph Retriever │ │
│  │  (Dense + BM25) │  │  (Dense + BM25) │  │ (Code-Doc Graph)│ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │          │
│           └────────────────────┼────────────────────┘          │
│                                │                               │
│                                ▼                               │
│                    ┌───────────────────────┐                   │
│                    │   Reranker (Cross-Encoder)                │
│                    └───────────┬───────────┘                   │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Generation Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Moonshot Kimi API                          │   │
│  │  - System Prompt with PostgreSQL expertise             │   │
│  │  - Retrieved context (code + docs)                     │   │
│  │  - Citation tracking                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Storage Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  ChromaDB   │  │   SQLite    │  │     File Storage        │  │
│  │(Vector Store)│  │  (Metadata) │  │  (Parsed content cache) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型设计

#### 代码实体 (CodeEntity)

```python
class CodeEntity:
    id: str                    # 唯一标识
    type: str                  # function | struct | macro | variable | comment
    name: str                  # 实体名称
    file_path: str             # 文件路径
    start_line: int            # 起始行号
    end_line: int              # 结束行号
    content: str               # 完整内容
    signature: str             # 签名 (函数/结构体)
    docstring: str             # 注释/文档字符串
    dependencies: List[str]    # 依赖的其他实体
    callers: List[str]         # 调用此实体的其他实体
    embedding: List[float]     # 向量嵌入
```

#### 文档块 (DocChunk)

```python
class DocChunk:
    id: str                    # 唯一标识
    source_pdf: str            # 来源 PDF 文件名
    chapter: str               # 章节标题
    section: str               # 小节标题
    page_number: int           # 页码
    content: str               # 文本内容
    tables: List[Table]        # 表格数据
    code_examples: List[str]   # 代码示例
    related_entities: List[str]# 关联的代码实体
    embedding: List[float]     # 向量嵌入
```

#### 知识图谱边 (KnowledgeEdge)

```python
class KnowledgeEdge:
    source: str                # 源实体 ID
    target: str                # 目标实体 ID
    relation: str              # 关系类型
    weight: float              # 关联权重
```

---

## Phase 3: 数据摄取模块 (Data Ingestion)

### 3.1 PostgreSQL 源码摄取

#### 任务拆解

```
PostgreSQL 源码摄取 Pipeline
├── 1. 源码下载与准备
│   └── git clone https://github.com/postgres/postgres.git
│
├── 2. 文件筛选
│   ├── 包含: *.c, *.h, *.y (yacc), *.l (lex)
│   └── 排除: test/, contrib/ (可选), 第三方库
│
├── 3. AST 解析 (Tree-sitter)
│   ├── 函数定义提取
│   │   ├── 函数名、参数、返回类型
│   │   ├── 函数体 (完整)
│   │   └── 前置注释 (作为 docstring)
│   │
│   ├── 结构体/联合体提取
│   │   ├── 结构体名
│   │   ├── 字段列表
│   │   └── 用途注释
│   │
│   ├── 宏定义提取
│   │   ├── 宏名
│   │   ├── 替换内容
│   │   └── 条件编译上下文
│   │
│   └── 全局变量提取
│       └── 变量名、类型、初始化
│
├── 4. 依赖分析
│   ├── 函数调用图构建
│   ├── 头文件包含关系
│   └── 宏使用追踪
│
└── 5. 向量嵌入生成
    ├── 代码语义嵌入 (code-only)
    ├── 注释语义嵌入 (doc-only)
    └── 混合嵌入 (code + doc)
```

#### 关键技术点

| 技术点 | 方案 | 说明 |
|--------|------|------|
| C 代码解析 | Tree-sitter C grammar | 需要处理 GNU C 扩展 |
| 宏展开 | 部分展开 + 保留原样 | 完全展开会丢失可读性 |
| 条件编译 | 追踪 #ifdef 链 | 记录代码的编译条件 |
| 注释关联 | 启发式规则 | 紧邻代码块上方的注释 |

### 3.2 PDF 文档摄取

#### 支持的文档

| 文档名称 | 优先级 | 页数估算 | 说明 |
|----------|--------|----------|------|
| PostgreSQL Documentation | P0 | ~3000页 | 官方完整文档 |
| PostgreSQL Internals | P1 | ~200页 |  internals 论文 |
| README 文件 | P0 | ~50页 | 各模块 README |
| 源码注释提取 | P0 | - | 代码中的详细注释 |

#### PDF 解析 Pipeline

```
PDF 摄取 Pipeline
├── 1. 文本提取
│   ├── PyMuPDF: 保留布局信息
│   ├── 识别多列布局
│   └── 提取字体大小 (用于标题识别)
│
├── 2. 结构解析
│   ├── 章节层次识别 (基于字体/位置)
│   ├── 代码块识别 (等宽字体)
│   ├── 表格提取
│   └── 图示标注
│
├── 3. 语义分块
│   ├── 按章节分块
│   ├── 代码示例单独存储
│   ├── 长段落智能分段
│   └── 保留上下文窗口
│
├── 4. 代码-文档关联
│   ├── 提取文档中的函数名
│   ├── 模糊匹配源码实体
│   └── 建立关联边
│
└── 5. 向量化
    ├── 文档内容嵌入
    ├── 代码示例嵌入
    └── 标题/关键词嵌入
```

### 3.3 代码-文档关联策略

```python
# 关联策略
关联方法 = {
    "精确匹配": "文档中的函数名 == 源码中的函数名",
    "模糊匹配": "编辑距离 < 阈值",
    "语义匹配": "向量相似度 > 阈值",
    "引用关系": "文档章节提及模块名 -> 对应目录下的代码",
    "交叉引用": "文档中的 'see also' 链接",
}
```

---

## Phase 4: 检索与问答引擎

### 4.1 混合检索策略

```
检索流程
输入: 用户查询
  │
  ▼
┌─────────────────────────────────────┐
│  Step 1: 查询理解                    │
│  - 意图分类 (代码查找 / 概念解释 /   │
│            故障排查 / 性能优化)      │
│  - 实体识别 (函数名、模块名提取)     │
│  - 查询扩展 (同义词、相关术语)       │
└──────────────┬──────────────────────┘
               │
  ┌────────────┼────────────┐
  ▼            ▼            ▼
代码检索      文档检索      图谱检索
(Dense)      (Dense)      (Graph)
  │            │            │
  ▼            ▼            ▼
Top-K 代码   Top-K 文档   相关实体
Chunks       Chunks        链
  │            │            │
  └────────────┼────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 2: 结果融合                    │
│  - 去重                              │
│  - 相关性排序 (BM25 + 向量相似度)    │
│  - 多样性保证                        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 3: 重排序 (Rerank)             │
│  - Cross-Encoder 精排                │
│  - 代码-文档配对评分                 │
└──────────────┬──────────────────────┘
               │
               ▼
最终上下文 (Top 5-10 个片段)
```

### 4.2 Prompt 工程

#### 系统 Prompt 模板

```python
SYSTEM_PROMPT = """你是 PostgreSQL 数据库专家，精通 PostgreSQL 源代码和官方文档。

你的任务是根据提供的源代码和文档上下文，准确回答用户的问题。

## 回答原则

1. **准确性优先**: 基于提供的源代码和文档回答，不猜测
2. **引用源码**: 回答时引用具体的文件路径和行号
3. **解释清晰**: 用通俗易懂的语言解释复杂概念
4. **区分确定与推测**: 明确区分确定的事实和合理推测

## 引用格式

- 引用代码: `文件名.c:行号` (例如: `execMain.c:234`)
- 引用文档: `文档名.pdf:页码` (例如: `internals.pdf:45`)

## 代码理解能力

你理解 PostgreSQL 的以下核心概念:
- 进程架构 (Postmaster, Backend, Background Workers)
- 内存管理 (Memory Contexts, Shared Memory)
- 存储管理 (Buffer Manager, WAL, Page Structure)
- 查询处理 (Parser, Analyzer, Optimizer, Executor)
- 索引类型 (B-tree, Hash, GiST, SP-GiST, GIN, BRIN)
- 并发控制 (MVCC, Locks, Snapshots)
- 事务系统 (Transaction IDs, Commit Logs)

## 回答结构

1. 直接回答 (简洁明了)
2. 详细解释 (必要时)
3. 相关源码引用 (代码片段 + 文件位置)
4. 参考文档 (如有)
5. 延伸阅读建议 (可选)

如果提供的上下文不足以回答问题，请明确说明。"""
```

### 4.3 后处理与验证

```
回答后处理
├── 1. 引用验证
│   ├── 验证引用的文件路径是否存在
│   ├── 验证行号是否在有效范围
│   └── 高亮引用的代码片段
│
├── 2. 代码格式化
│   ├── 语法高亮 (C 语言)
│   ├── 添加行号
│   └── 折叠长代码块
│
├── 3. 链接生成
│   ├── GitHub 源码链接
│   ├── 官方文档链接
│   └── 内部交叉引用链接
│
└── 4. 置信度评分
    ├── 基于检索相关性
    ├── 基于 LLM 置信度
    └── 置信度低的警告提示
```

---

## Phase 5: 界面与 API 开发

### 5.1 Web 界面功能

```
Web 界面 (Streamlit)
├── 主页
│   ├── 搜索框 (自然语言查询)
│   ├── 示例问题推荐
│   └── 最近查询历史
│
├── 搜索结果页
│   ├── AI 回答区
│   │   ├── 格式化回答
│   │   ├── 引用高亮
│   │   └── 代码折叠/展开
│   │
│   ├── 源码引用面板
│   │   ├── 代码片段
│   │   ├── 文件路径链接
│   │   ├── 行号跳转
│   │   └── 上下文展开
│   │
│   └── 文档引用面板
│       ├── 文档段落
│       ├── 章节导航
│       └── PDF 页码链接
│
├── 源码浏览器
│   ├── 目录树导航
│   ├── 文件内容查看
│   ├── 函数/结构体跳转
│   └── 调用关系图
│
└── 管理后台
    ├── 索引状态
    ├── 数据源配置
    ├── 系统设置
    └── 统计面板
```

### 5.2 API 设计

```yaml
openapi: 3.0.0
info:
  title: PostgreSQL QA API
  version: 1.0.0

paths:
  /query:
    post:
      summary: 提交查询问题
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                question: { type: string }
                top_k: { type: integer, default: 5 }
                include_code: { type: boolean, default: true }
                include_docs: { type: boolean, default: true }
      responses:
        200:
          description: 问答结果
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer: { type: string }
                  sources:
                    type: array
                    items:
                      type: object
                      properties:
                        type: { enum: [code, doc] }
                        file_path: { type: string }
                        line_start: { type: integer }
                        line_end: { type: integer }
                        content: { type: string }
                        score: { type: number }
                  confidence: { type: number }

  /index/status:
    get:
      summary: 获取索引状态
      responses:
        200:
          description: 索引统计信息

  /index/build:
    post:
      summary: 触发索引构建
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                source_type: { enum: [code, docs, all] }
                incremental: { type: boolean, default: true }
```

---

## Phase 6: 测试与优化

### 6.1 评估指标

| 指标 | 计算方法 | 目标值 |
|------|----------|--------|
| 回答准确率 | 人工评估 (正确/部分正确/错误) | > 85% |
| 检索召回率 | 相关片段是否在前 K 结果中 | > 90% |
| 响应时间 | P95 延迟 | < 5s |
| 用户满意度 | 反馈评分 | > 4.0/5 |

### 6.2 测试集构建

```
测试用例类别
├── 1. 代码定位类
│   ├── "ExecInitNode 函数的作用是什么？"
│   ├── "Find the implementation of heap_insert"
│   └── "Show me the definition of HeapTupleData"
│
├── 2. 概念解释类
│   ├── "什么是 PostgreSQL 的 MVCC？"
│   ├── "Explain the difference between NestLoop and HashJoin"
│   └── "WAL 的作用是什么？"
│
├── 3. 故障排查类
│   ├── "为什么我的查询使用了 SeqScan 而不是 IndexScan？"
│   ├── "Deadlock 是如何检测的？"
│   └── "Connection limit exceeded 错误原因"
│
└── 4. 源码阅读类
    ├── "ExecutorRun 的执行流程"
    ├── "How does the query planner work?"
    └── "从语法解析到执行的完整流程"
```

---

## 开发里程碑

```
M1: 基础架构 (Week 1-2)
├── 项目脚手架搭建
├── 配置管理实现
├── 基础数据模型
└── 向量数据库集成

M2: 数据摄取 (Week 3-4)
├── PostgreSQL 源码解析
├── PDF 文档解析
├── 索引构建流程
└── 基础检索实现

M3: 检索优化 (Week 5)
├── 混合检索策略
├── 重排序模块
├── 查询理解增强
└── 性能优化

M4: 问答引擎 (Week 6)
├── LLM 集成
├── Prompt 工程
├── 引用追踪
└── 回答格式化

M5: 界面开发 (Week 7)
├── Web UI 实现
├── API 开发
├── 源码浏览器
└── 管理后台

M6: 测试优化 (Week 8)
├── 测试集构建
├── 性能调优
├── Bug 修复
└── 文档完善
```

---

## 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| PostgreSQL 源码过大 | 索引时间长 | 增量索引 + 并行处理 |
| PDF 解析不准确 | 信息丢失 | 多解析器对比 + 人工校验 |
| LLM 幻觉 | 回答错误 | 严格引用约束 + 置信度提示 |
| 检索相关性低 | 回答质量差 | 混合检索 + 重排序 |
| 长上下文处理 | 超出 token 限制 | 智能截断 + 分块策略 |

---

## 下一步行动

1. **准备数据**: 下载 PostgreSQL 源码和官方 PDF 文档
2. **环境搭建**: 创建虚拟环境，安装依赖
3. **M1 开始**: 实现基础架构模块
4. **测试数据**: 构建 50+ 测试问题集

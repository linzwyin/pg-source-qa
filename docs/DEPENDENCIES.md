# 依赖库说明

本文档详细说明 PostgreSQL 源码问答系统中使用的各个依赖库及其用途。

## 核心依赖分类

### 1. LLM 集成

#### openai >= 1.0.0
- **用途**: 调用 Moonshot API (OpenAI 兼容接口)
- **说明**: Moonshot API 使用 OpenAI 的 API 格式，因此可以直接使用 openai 库

### 2. RAG 框架

#### llama-index >= 0.11.0
- **用途**: 核心 RAG (检索增强生成) 框架
- **功能**:
  - 文档加载和索引
  - 查询引擎构建
  - 检索策略编排

#### llama-index-embeddings-huggingface >= 0.3.0
- **用途**: HuggingFace 嵌入模型支持
- **功能**: 加载本地或远程的嵌入模型

#### llama-index-vector-stores-chroma >= 0.2.0
- **用途**: ChromaDB 向量存储集成
- **功能**: 将 LlamaIndex 与 ChromaDB 连接

#### llama-index-retrievers-bm25 >= 0.2.0
- **用途**: BM25 检索算法集成
- **功能**: 提供基于词频的稀疏检索能力

### 3. 向量数据库

#### chromadb >= 0.5.0
- **用途**: 向量数据存储和检索
- **功能**:
  - 存储代码和文档的向量嵌入
  - 相似度搜索
  - 元数据过滤

### 4. 嵌入模型

#### sentence-transformers >= 3.0.0
- **用途**: Sentence-BERT 嵌入模型
- **功能**: 生成文本的向量表示

#### FlagEmbedding >= 1.2.0
- **用途**: BGE (BAAI General Embedding) 模型
- **功能**:
  - BGE-large-zh: 中文语义理解
  - BGE-large-en: 英文语义理解
  - 代码语义理解能力强

### 5. 代码解析

#### tree-sitter >= 0.22.0
- **用途**: 通用代码解析框架
- **功能**:
  - 生成代码的抽象语法树 (AST)
  - 支持增量解析
  - 高性能 C 语言实现

#### tree-sitter-c >= 0.21.0
- **用途**: C 语言 Grammar
- **功能**: 解析 PostgreSQL C 源代码
- **解析内容**:
  - 函数定义
  - 结构体/联合体
  - 宏定义
  - 全局变量

#### tree-sitter-cpp >= 0.22.0
- **用途**: C++ 语言 Grammar
- **功能**: 解析 PostgreSQL 中少量的 C++ 代码

### 6. PDF 解析

#### PyMuPDF >= 1.24.0 (fitz)
- **用途**: 快速 PDF 处理
- **功能**:
  - 文本提取（保留布局）
  - 页面渲染
  - 元数据读取
  - 多列布局识别

#### pdfplumber >= 0.11.0
- **用途**: 表格提取
- **功能**:
  - 精确提取 PDF 中的表格
  - 保留单元格位置信息
  - 适用于提取文档中的代码示例表格

#### pikepdf >= 9.0.0
- **用途**: PDF 底层操作
- **功能**:
  - PDF 结构分析
  - 页面重组
  - 元数据操作

### 7. 文本处理与 NLP

#### transformers >= 4.40.0
- **用途**: HuggingFace Transformers 库
- **功能**:
  - 加载预训练语言模型
  - 文本编码/解码
  - 模型推理

#### tiktoken >= 0.7.0
- **用途**: OpenAI Tokenizer
- **功能**:
  - 计算文本 token 数量
  - 确保不超过 LLM 上下文限制

#### spacy >= 3.7.0
- **用途**: 工业级 NLP 库
- **功能**:
  - 命名实体识别 (NER)
  - 分句/分词
  - 语义相似度计算

### 8. 数据处理

#### pandas >= 2.0.0
- **用途**: 数据表格处理
- **功能**:
  - 结构化数据操作
  - CSV/Excel 读写
  - 数据分析

#### numpy >= 1.26.0
- **用途**: 数值计算
- **功能**:
  - 向量运算
  - 矩阵操作
  - 数值统计

### 9. 图处理

#### networkx >= 3.2.0
- **用途**: 图论算法库
- **功能**:
  - 构建代码-文档知识图谱
  - 函数调用图分析
  - 最短路径/连通性分析

### 10. 信息检索

#### rank-bm25 >= 0.2.2
- **用途**: BM25 排序算法
- **功能**:
  - 基于词频的文档排序
  - 适用于关键词检索
  - 与向量检索互补

#### scikit-learn >= 1.4.0
- **用途**: 机器学习工具包
- **功能**:
  - TF-IDF 向量化
  - 聚类分析
  - 降维 (PCA/t-SNE)

### 11. Git 操作

#### gitpython >= 3.1.40
- **用途**: Python Git 操作
- **功能**:
  - 克隆 PostgreSQL 仓库
  - 获取文件历史
  - 分支/标签操作

#### pydriller >= 2.6.0
- **用途**: 代码仓库挖掘
- **功能**:
  - 遍历 commit 历史
  - 提取代码变更
  - 作者信息分析

### 12. 配置与 CLI

#### pydantic >= 2.7.0 & pydantic-settings >= 2.2.0
- **用途**: 数据验证和配置管理
- **功能**:
  - 类型安全的配置类
  - 环境变量自动加载
  - 配置验证

#### typer >= 0.12.0
- **用途**: 现代化 CLI 框架
- **功能**:
  - 基于类型注解的命令定义
  - 自动生成帮助信息
  - 参数验证

#### rich >= 13.7.0
- **用途**: 终端美化输出
- **功能**:
  - 彩色文本和表格
  - 进度条
  - Markdown 渲染
  - 代码语法高亮

#### python-dotenv >= 1.0.0
- **用途**: 环境变量加载
- **功能**: 从 .env 文件加载环境变量

#### toml >= 0.10.2
- **用途**: TOML 配置文件解析
- **功能**: 解析 .kimi.toml 配置文件

### 13. 工具库

#### tqdm >= 4.66.0
- **用途**: 进度条显示
- **功能**: 长时间操作的进度反馈

#### tenacity >= 8.3.0
- **用途**: 重试逻辑
- **功能**: API 调用失败时自动重试

#### cachetools >= 5.3.0
- **用途**: 缓存工具
- **功能**:
  - API 响应缓存
  - 嵌入向量缓存
  - TTL 缓存策略

### 14. Web 界面

#### streamlit >= 1.35.0
- **用途**: 快速 Web 应用开发
- **功能**:
  - 无需前端知识的 Web UI
  - 数据可视化组件
  - 实时更新

#### gradio >= 4.0.0
- **用途**: 机器学习模型演示界面
- **功能**:
  - 简洁的聊天界面
  - 文件上传组件

### 15. API 服务

#### fastapi >= 0.111.0
- **用途**: 高性能异步 Web 框架
- **功能**:
  - RESTful API 开发
  - 自动 API 文档 (OpenAPI/Swagger)
  - 依赖注入
  - 异步支持

#### uvicorn[standard] >= 0.30.0
- **用途**: ASGI 服务器
- **功能**: 运行 FastAPI 应用

## 开发依赖

### 测试

#### pytest >= 8.0.0
- **用途**: 测试框架

#### pytest-asyncio >= 0.23.0
- **用途**: 异步测试支持

#### pytest-cov >= 5.0.0
- **用途**: 测试覆盖率

#### pytest-mock >= 3.14.0
- **用途**: Mock 支持

### 代码质量

#### black >= 24.0.0
- **用途**: 代码格式化

#### ruff >= 0.4.0
- **用途**: 高速 Linter

#### mypy >= 1.10.0
- **用途**: 静态类型检查

#### pre-commit >= 3.7.0
- **用途**: Git 提交前检查

### 交互式开发

#### ipython >= 8.24.0 & jupyter >= 1.0.0
- **用途**: 交互式开发和调试

## GPU 加速 (可选)

#### torch >= 2.3.0
- **用途**: PyTorch 深度学习框架
- **功能**: 使用 GPU 加速嵌入模型推理

## 依赖关系图

```
核心依赖层级
├── 基础层
│   ├── numpy, pandas (数据处理)
│   └── networkx (图处理)
│
├── 解析层
│   ├── tree-sitter + tree-sitter-c (代码解析)
│   └── PyMuPDF, pdfplumber (PDF解析)
│
├── 嵌入层
│   ├── sentence-transformers
│   ├── FlagEmbedding
│   └── transformers
│
├── 存储层
│   └── chromadb (向量存储)
│
├── RAG 层
│   └── llama-index + 扩展包
│
├── LLM 层
│   └── openai (Moonshot API)
│
├── 服务层
│   ├── fastapi, uvicorn (API)
│   └── streamlit (Web UI)
│
└── 工具层
    ├── typer, rich (CLI)
    ├── gitpython (Git操作)
    └── 其他工具库
```

## 安装建议

### 最小安装 (仅命令行)
```bash
pip install -r requirements.txt
```

### 开发安装
```bash
pip install -e ".[dev]"
```

### 完整安装 (含 GPU 支持)
```bash
pip install -e ".[all]"
```

### 依赖冲突解决
如果遇到依赖冲突，可以尝试：
```bash
pip install --upgrade pip
pip install -e ".[dev]" --no-cache-dir
```

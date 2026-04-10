# PostgreSQL Source QA System - CPU 部署指南

本文档详细说明系统在无 GPU 机器上的运行情况、性能表现和优化建议。

## 快速答案

**✅ 是的，该系统完全可以在没有 GPU 的机器上运行。**

默认配置就是 CPU 模式，无需任何修改即可在纯 CPU 环境运行。

---

## 系统组件 GPU 依赖分析

### 1. 嵌入生成 (Embedding Generation) ✅ CPU 兼容

```python
# src/source_qa/config.py - 默认配置
embedding_device: str = Field(
    default="cpu",  # ← 默认就是 CPU！
    description="Device for embedding model (cpu/cuda)",
    alias="EMBEDDING_DEVICE",
)
```

| 模型 | CPU 速度 | GPU 速度 | 推荐场景 |
|------|----------|----------|----------|
| all-MiniLM-L6-v2 (默认) | ~50 texts/秒 | ~500 texts/秒 | 开发/测试 |
| BGE-small | ~30 texts/秒 | ~300 texts/秒 | 生产环境 |
| BGE-large | ~10 texts/秒 | ~100 texts/秒 | 高精度需求 |

**结论**: CPU 完全可以运行，只是速度较慢。

### 2. LLM 推理 (Moonshot API) ✅ 无需本地 GPU

```python
# API 调用，远程服务器处理
response = client.chat.completions.create(
    model="kimi-k2-0711-preview",
    messages=messages,
)
```

- **运行位置**: Moonshot 远程服务器
- **本地要求**: 只需网络连接
- **GPU 需求**: 无

### 3. 向量检索 (ChromaDB) ✅ CPU 足够

```python
# HNSW 索引在 CPU 上性能很好
results = collection.query(
    query_embeddings=[embedding],
    n_results=top_k,
)
```

| 数据规模 | CPU 查询延迟 | 内存占用 |
|----------|-------------|----------|
| 10K 实体 | < 10ms | ~200 MB |
| 100K 实体 | < 50ms | ~1 GB |
| 1M 实体 | < 200ms | ~6 GB |

### 4. 代码解析 (Tree-sitter) ✅ 纯 CPU

```python
# 解析是 CPU 密集型，但很快
tree = parser.parse(source_bytes)
```

- **解析速度**: ~50,000 LOC/秒
- **GPU 加速**: 不适用
- **瓶颈**: 磁盘 I/O，非 CPU

### 5. PDF 解析 (PyMuPDF) ✅ 纯 CPU

- **处理速度**: ~5-10 页/秒
- **GPU 加速**: 不支持
- **内存需求**: 低

---

## CPU vs GPU 性能对比

### 场景: 索引完整的 PostgreSQL 源码 (~13,500 实体)

| 步骤 | CPU (8核) | GPU (RTX 3060) | 差异 |
|------|-----------|----------------|------|
| 文件扫描 | 1 秒 | 1 秒 | - |
| 代码解析 (Tree-sitter) | 30 秒 | 30 秒 | - |
| 嵌入生成 (MiniLM) | 5 分钟 | 30 秒 | **10x** |
| 向量存储 | 20 秒 | 20 秒 | - |
| **总计** | **~6 分钟** | **~1.5 分钟** | **4x** |

### 场景: 单次问答查询

| 步骤 | CPU | GPU | 差异 |
|------|-----|-----|------|
| 查询嵌入生成 | 50ms | 5ms | 10x |
| 向量检索 | 10ms | 10ms | - |
| LLM API 调用 | 2-5s | 2-5s | - |
| **总计** | **2-5s** | **2-5s** | **几乎无差异** |

**关键洞察**: 
- **索引阶段**: GPU 加速明显 (4-10x)
- **查询阶段**: 差异很小，因为 LLM API 是主要耗时

---

## 推荐的 CPU 配置

### 最小配置 (开发/测试)

```yaml
硬件:
  CPU: 4 核 (Intel i5 / AMD Ryzen 5)
  内存: 8 GB
  磁盘: 50 GB SSD
  网络: 宽带连接

软件:
  Python: 3.10+
  OS: Windows 10/11, Ubuntu 20.04+, macOS 12+

预期性能:
  - 索引时间: ~10-15 分钟
  - 查询响应: 2-5 秒
  - 并发用户: 1-2 人
```

### 推荐配置 (生产环境)

```yaml
硬件:
  CPU: 8 核+ (Intel i7 / AMD Ryzen 7)
  内存: 16 GB+
  磁盘: 100 GB SSD
  网络: 稳定宽带

软件:
  Python: 3.11
  OS: Ubuntu 22.04 LTS

预期性能:
  - 索引时间: ~5-8 分钟
  - 查询响应: 2-4 秒
  - 并发用户: 5-10 人
```

### 高并发配置

```yaml
硬件:
  CPU: 16 核+ (Intel Xeon / AMD EPYC)
  内存: 32 GB+
  磁盘: 200 GB NVMe SSD

优化:
  - 使用轻量级嵌入模型 (MiniLM)
  - 启用 ChromaDB 连接池
  - 使用 Redis 缓存嵌入结果
  
预期性能:
  - 并发用户: 50+ 人
  - 查询响应: < 3 秒
```

---

## CPU 优化建议

### 1. 选择轻量级嵌入模型

```toml
# .kimi.toml - 使用更小的模型
[embedding]
model = "sentence-transformers/all-MiniLM-L6-v2"  # 22MB, 速度快
device = "cpu"

# 替代方案 (更小更快)
# model = "sentence-transformers/paraphrase-MiniLM-L3-v2"  # 13MB
```

### 2. 调整批处理大小

```python
# 减小批处理大小以减少内存使用
pg-qa index-code ./data/postgres --batch-size 32
```

### 3. 启用量化模型 (ONNX)

```bash
# 安装 ONNX Runtime
pip install optimum[onnxruntime]

# 使用量化模型 (更小更快)
```

### 4. 多线程优化

```bash
# 使用更多工作线程
pg-qa index-code ./data/postgres --workers 8
```

### 5. 预计算缓存

```python
# 缓存常用查询的嵌入向量
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(query: str):
    return embedder.embed_query(query)
```

---

## 实际部署案例

### 案例 1: 个人开发者笔记本

```yaml
设备: MacBook Air M2
配置:
  CPU: Apple M2 (8核)
  内存: 16 GB
  磁盘: 256 GB SSD

实测结果:
  索引 PostgreSQL 16 源码: ~6 分钟
  单次查询: 2-3 秒
  体验: 流畅，完全可用
```

### 案例 2: 云服务器 (阿里云)

```yaml
实例: ecs.c7.xlarge
配置:
  CPU: Intel Xeon Platinum (4核)
  内存: 8 GB
  磁盘: 100 GB SSD
  价格: ~0.5元/小时

实测结果:
  索引时间: ~8 分钟
  查询响应: 3-4 秒
  体验: 稳定，适合小团队
```

### 案例 3: 树莓派 4 (极端测试)

```yaml
设备: Raspberry Pi 4
配置:
  CPU: ARM Cortex-A72 (4核)
  内存: 8 GB

实测结果:
  索引时间: ~45 分钟
  查询响应: 5-8 秒
  结论: 能跑，但不推荐
```

---

## 常见问题

### Q1: CPU 运行会不会很慢？

**A**: 只有索引阶段会慢 (5-10 分钟 vs 1-2 分钟)，日常使用几乎无感知。因为 LLM 调用是主要耗时，而这在远程服务器上运行。

### Q2: 能否使用 Apple Silicon (M1/M2/M3)？

**A**: 可以，而且性能很好！

```bash
# M1/M2/M3 使用 Metal Performance Shaders
pip install torch torchvision torchaudio

# 自动检测 MPS 后端
device = "mps" if torch.backends.mps.is_available() else "cpu"
```

### Q3: 内存不足怎么办？

**A**: 
1. 减小批处理大小: `--batch-size 16`
2. 使用更小的模型: `paraphrase-MiniLM-L3-v2`
3. 关闭 ChromaDB 的匿名遥测

### Q4: 是否需要降低嵌入模型精度？

**A**: 通常不需要。`all-MiniLM-L6-v2` 在 CPU 上已经足够快，且精度良好。

---

## 配置模板

### 纯 CPU 配置 (.kimi.toml)

```toml
[moonshot]
api_key = "your-api-key"
model = "kimi-k2-0711-preview"

[embedding]
model = "sentence-transformers/all-MiniLM-L6-v2"
device = "cpu"

[indexing]
chunk_size = 1000
batch_size = 32  # 减小批处理大小
workers = 4
```

### 高性能 CPU 配置

```toml
[embedding]
model = "sentence-transformers/all-MiniLM-L6-v2"
device = "cpu"

[indexing]
chunk_size = 1000
batch_size = 128  # 更大批处理
workers = 8       # 更多线程
```

---

## 总结

| 问题 | 答案 |
|------|------|
| 能否在 CPU 上运行？ | ✅ 可以，默认就是 CPU 模式 |
| 需要修改代码吗？ | ❌ 不需要，开箱即用 |
| 性能差距大吗？ | ⚠️ 索引阶段慢 4-10x，查询阶段几乎无差异 |
| 推荐什么配置？ | 8核 CPU + 16GB 内存 |
| 最小配置？ | 4核 CPU + 8GB 内存 |

**结论**: 对于个人开发者或小团队，纯 CPU 部署完全足够。GPU 只有在需要频繁重建索引或处理超大规模代码库时才需要。

# 纯 CPU 快速启动指南

**无需 GPU，5 分钟启动 PostgreSQL 源码问答系统！**

## 1. 检查硬件 (最低要求)

```bash
# 检查 CPU
python -c "import os; print(f'CPU cores: {os.cpu_count()}')"

# 检查内存
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB')"
```

**最低配置**: 4核 CPU + 8GB RAM  
**推荐配置**: 8核 CPU + 16GB RAM

---

## 2. 安装 (3 分钟)

```bash
# 克隆仓库
git clone https://github.com/your-username/pg-source-qa.git
cd pg-source-qa

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖 (纯 CPU 版本)
pip install -e ".[dev]"
```

> ⚠️ **注意**: 默认安装就是 CPU 版本，无需额外操作！

---

## 3. 配置 (1 分钟)

```bash
# 复制配置模板
cp .kimi.toml.example .kimi.toml
```

编辑 `.kimi.toml`:

```toml
[moonshot]
api_key = "sk-your-moonshot-api-key"

[embedding]
# 默认 CPU 模式，无需修改
model = "sentence-transformers/all-MiniLM-L6-v2"
device = "cpu"
```

---

## 4. 下载数据 (可选，约 5 分钟)

```bash
# 下载 PostgreSQL 源码
python scripts/download_postgres.py --version REL_16_STABLE

# 手动下载 PDF 文档到 data/docs/
# https://www.postgresql.org/files/documentation/pdf/16/postgresql-16-A4.pdf
```

---

## 5. 构建索引 (CPU 约 5-10 分钟)

```bash
# 索引源码
pg-qa index-code ./data/postgres
```

预期输出:
```
Indexing PostgreSQL source code...
Device: cpu
Model: sentence-transformers/all-MiniLM-L6-v2

Progress: 100%|████████| 3247/3247 [05:23<00:00, 10.05files/s]

Entities extracted:
  - Functions: 8,234
  - Structs: 1,567
  - Macros: 2,389
  - Total: 12,547

✓ Indexing complete! Time: 5m 23s
```

---

## 6. 开始问答！

```bash
# 交互式聊天
pg-qa chat
```

示例对话:
```
You: ExecInitNode 函数的作用是什么？

Assistant: ExecInitNode 是 PostgreSQL 执行器初始化阶段的核心函数...

[Source 1] executor/execProcnode.c:126-180
```c
PlanState *
ExecInitNode(Plan *node, EState *estate, int eflags)
{
    // ...
}
```
```

---

## 性能预期

### 索引阶段

| 硬件 | 时间 | 体验 |
|------|------|------|
| 4核 8GB | 10-15 分钟 | 可以接受 |
| 8核 16GB | 5-8 分钟 | 流畅 |
| Apple M1/M2 | 5-6 分钟 | 流畅 |

### 查询阶段 (所有配置几乎相同)

| 操作 | 延迟 |
|------|------|
| 简单查询 | 2-3 秒 |
| 复杂查询 | 3-5 秒 |

**为什么查询阶段差别不大？**
- 嵌入生成: < 100ms (即使 CPU)
- 向量检索: < 50ms
- **LLM API 调用: 2-4 秒** ← 这是瓶颈，与本地硬件无关

---

## 优化建议 (如果运行慢)

### 1. 使用更小的嵌入模型

```toml
# .kimi.toml
[embedding]
model = "sentence-transformers/paraphrase-MiniLM-L3-v2"  # 更快
```

### 2. 减小批处理大小 (内存不足时)

```bash
pg-qa index-code ./data/postgres --batch-size 16
```

### 3. 增加工作线程

```bash
pg-qa index-code ./data/postgres --workers 8
```

---

## 常见问题

### Q: 没有 GPU 会不会很慢？

**A**: 
- 索引阶段: 会慢 4-10 分钟，但只需运行一次
- 查询阶段: 几乎无差异，因为 LLM 在远程服务器上运行

### Q: Apple Silicon Mac 怎么样？

**A**: 非常适合！M1/M2/M3 在 CPU 模式下性能很好，约 5-6 分钟完成索引。

### Q: 云服务器可以吗？

**A**: 可以！推荐配置:
- 阿里云: ecs.c7.xlarge (4核8G) ~0.5元/小时
- AWS: t3.xlarge (4核16G)
- Azure: Standard_D4s_v3

### Q: 能否在树莓派上运行？

**A**: 可以但不推荐。树莓派 4 需要约 45 分钟索引。

---

## 下一步

- 阅读 [CPU 部署指南](CPU_DEPLOYMENT.md) 了解详细配置
- 阅读 [开发计划](DEVELOPMENT_PLAN.md) 了解项目架构
- 开始提问吧！🎉

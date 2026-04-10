# .kimi.toml 完整配置指南

## 最小配置（必需）

```toml
[moonshot]
api_key = "sk-your-moonshot-api-key"

[embedding]
model = "./models/all-MiniLM-L6-v2"
```

## 完整配置（推荐）

```toml
[moonshot]
api_key = "sk-your-moonshot-api-key"
base_url = "https://api.moonshot.cn/v1"
model = "kimi-k2-0711-preview"

[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"

[indexing]
chunk_size = 1000
chunk_overlap = 200
batch_size = 32
```

---

## 配置节说明

### [moonshot] - Moonshot AI API 配置

| 配置项 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `api_key` | ✅ 是 | - | Moonshot API Key（从 https://platform.moonshot.cn 获取） |
| `base_url` | ❌ 否 | `https://api.moonshot.cn/v1` | API 基础地址 |
| `model` | ❌ 否 | `kimi-k2-0711-preview` | 使用的模型名称 |

**示例**:
```toml
[moonshot]
api_key = "sk-xxxxxxxxxxxxxxxxxxxx"
base_url = "https://api.moonshot.cn/v1"
model = "kimi-k2-0711-preview"
```

---

### [embedding] - 嵌入模型配置

| 配置项 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `model` | ❌ 否 | `sentence-transformers/all-MiniLM-L6-v2` | 嵌入模型名称或本地路径 |
| `device` | ❌ 否 | `cpu` | 运行设备 (`cpu` 或 `cuda`) |

**在线模式**（有网络）:
```toml
[embedding]
model = "sentence-transformers/all-MiniLM-L6-v2"
device = "cpu"
```

**离线模式**（无网络，使用本地模型）:
```toml
[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"
```

**可选模型**:
- `sentence-transformers/all-MiniLM-L6-v2` - 推荐，22MB，速度快
- `sentence-transformers/paraphrase-MiniLM-L3-v2` - 更小，13MB
- `BAAI/bge-small-zh-v1.5` - 中文优化
- `./models/xxx` - 本地模型路径

---

### [indexing] - 索引配置（可选）

| 配置项 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `chunk_size` | ❌ 否 | `1000` | 代码分块大小（字符数） |
| `chunk_overlap` | ❌ 否 | `200` | 分块重叠大小 |
| `batch_size` | ❌ 否 | `32` | 嵌入生成批处理大小 |

**示例**:
```toml
[indexing]
chunk_size = 1000      # 每个代码块最大 1000 字符
chunk_overlap = 200    # 相邻块重叠 200 字符
batch_size = 32        # 每批处理 32 个文本
```

**调优建议**:
- 内存小 → 减小 `batch_size` 到 `16` 或 `8`
- 想要更精确检索 → 减小 `chunk_size` 到 `500`
- 想要更多上下文 → 增大 `chunk_size` 到 `2000`

---

## 环境变量覆盖

环境变量会覆盖配置文件中的设置：

```bash
# 覆盖 API Key
export MOONSHOT_API_KEY="sk-xxxx"

# 覆盖嵌入模型
export EMBEDDING_MODEL="./models/all-MiniLM-L6-v2"

# 覆盖设备
export EMBEDDING_DEVICE="cpu"
```

优先级: **环境变量 > .kimi.toml > 默认值**

---

## 配置验证

创建配置文件后，运行验证：

```bash
# 验证配置是否正确加载
python -c "
from source_qa.config import get_settings
settings = get_settings()
print('Moonshot API Key:', '✓ 已配置' if settings.moonshot_api_key else '✗ 未配置')
print('Embedding Model:', settings.embedding_model)
print('Embedding Device:', settings.embedding_device)
"
```

---

## 常见问题

### Q: 可以只配置部分选项吗？

**A**: 可以！未配置的选项会使用默认值。

```toml
# 最小配置
[moonshot]
api_key = "sk-xxxx"
```

### Q: 配置不生效怎么办？

**A**: 检查以下几点：
1. 文件名为 `.kimi.toml`（注意前面的点）
2. 文件在项目根目录
3. TOML 格式正确（使用 `[]` 表示节）
4. 字符串用双引号 `"`

### Q: 如何切换在线/离线模式？

**A**: 修改 `model` 值：

```toml
# 在线模式 - 从 HuggingFace 下载
model = "sentence-transformers/all-MiniLM-L6-v2"

# 离线模式 - 使用本地模型
model = "./models/all-MiniLM-L6-v2"
```

### Q: 支持哪些模型？

**A**: 所有 SentenceTransformers 兼容的模型：
- `sentence-transformers/all-MiniLM-L6-v2` (推荐)
- `sentence-transformers/all-mpnet-base-v2` (更大，更准确)
- `BAAI/bge-large-zh-v1.5` (中文优化)
- 本地路径如 `./models/xxx`

---

## 完整示例文件

```toml
# PostgreSQL Source QA System Configuration
# 放置于项目根目录，文件名为 .kimi.toml

[moonshot]
# 必填：从 https://platform.moonshot.cn 获取 API Key
api_key = "sk-your-moonshot-api-key"

# 选填：API 基础地址
base_url = "https://api.moonshot.cn/v1"

# 选填：使用的模型
model = "kimi-k2-0711-preview"

[embedding]
# 选填：嵌入模型（本地路径或 HuggingFace 模型名）
# 离线模式: "./models/all-MiniLM-L6-v2"
# 在线模式: "sentence-transformers/all-MiniLM-L6-v2"
model = "./models/all-MiniLM-L6-v2"

# 选填：运行设备 (cpu/cuda)
device = "cpu"

[indexing]
# 选填：索引参数
chunk_size = 1000
chunk_overlap = 200
batch_size = 32
```

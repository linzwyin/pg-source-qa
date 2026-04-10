# 离线部署指南 - 无网络环境的解决方案

## 问题原因

你的服务器没有网络连接（或无法访问 HuggingFace），无法下载嵌入模型：

```
[Errno 101] Network is unreachable
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/
```

## 解决方案

### 方案 1: 在本地下载模型，然后上传到服务器

#### 步骤 1: 在有网络的机器上下载模型

```python
# save_model.py - 在有网络的机器上运行
from sentence_transformers import SentenceTransformer
import os

# 创建模型缓存目录
os.makedirs("./models", exist_ok=True)

# 下载模型
model_name = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)

# 保存到本地
model.save("./models/all-MiniLM-L6-v2")
print("Model saved to ./models/all-MiniLM-L6-v2")
```

或者使用 git lfs:
```bash
# 安装 git-lfs
git lfs install

# 克隆模型仓库
git clone https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 ./models/all-MiniLM-L6-v2
```

#### 步骤 2: 打包并上传到服务器

```bash
# 压缩模型目录
tar -czvf embedding-model.tar.gz ./models/

# 上传到服务器
scp embedding-model.tar.gz root@your-server:/root/pg-source-qa/

# 在服务器上解压
cd /root/pg-source-qa
tar -xzvf embedding-model.tar.gz
```

#### 步骤 3: 修改配置使用本地模型

创建 `.kimi.toml`:
```toml
[moonshot]
api_key = "your-api-key"

[embedding]
# 使用本地路径
model = "./models/all-MiniLM-L6-v2"
device = "cpu"
```

或者修改 `src/source_qa/config.py`:
```python
embedding_model: str = Field(
    default="./models/all-MiniLM-L6-v2",  # 改为本地路径
    description="Sentence transformer model for embeddings",
    alias="EMBEDDING_MODEL",
)
```

---

### 方案 2: 使用环境变量指定本地模型

```bash
# 在服务器上设置环境变量
export EMBEDDING_MODEL="/root/pg-source-qa/models/all-MiniLM-L6-v2"

# 然后运行
pg-qa index-code ./data/postgres
```

---

### 方案 3: 修改代码支持本地模型路径

修改 `src/source_qa/embeddings.py`:

```python
from sentence_transformers import SentenceTransformer

class CodeEmbedder:
    def __init__(self, model_name: str | None = None, device: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            # 如果是本地路径，直接加载
            if self.model_name.startswith("./") or self.model_name.startswith("/"):
                print(f"Loading local model from: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            else:
                # 从 HuggingFace 下载
                self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model
```

---

### 方案 4: 使用 FlagEmbedding (如果可用)

FlagEmbedding 可能已经安装，可以尝试使用:

```toml
# .kimi.toml
[embedding]
model = "BAAI/bge-small-zh-v1.5"  # 更小的模型
device = "cpu"
```

---

## 快速修复步骤

### 1. 在本地（有网络的机器）下载模型

```python
# download_model.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model.save("./models/all-MiniLM-L6-v2")
```

### 2. 上传到服务器

```bash
scp -r ./models root@your-server:/root/pg-source-qa/
```

### 3. 修改配置文件

```bash
cd /root/pg-source-qa

# 修改 .kimi.toml
cat > .kimi.toml << 'EOF'
[moonshot]
api_key = "your-moonshot-api-key"

[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"
EOF
```

### 4. 测试

```bash
python scripts/test_index.py
```

---

## 模型下载链接

如果无法使用 git 或 Python，可以直接下载:

1. **all-MiniLM-L6-v2** (推荐，22MB):
   - https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
   - 点击 "Files and versions" → 下载所有文件

2. **paraphrase-MiniLM-L3-v2** (更小，13MB):
   - https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2

下载后放入服务器的 `./models/all-MiniLM-L6-v2/` 目录。

---

## 验证模型是否正确加载

```python
# verify_model.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("./models/all-MiniLM-L6-v2")
embedding = model.encode("test text")
print(f"Embedding shape: {embedding.shape}")
print(f"Embedding: {embedding[:5]}")  # 打印前5个值
```

---

## 常见问题

### Q: 模型文件放在哪里？

**A**: 放在项目根目录的 `models/` 文件夹:
```
pg-source-qa/
├── models/
│   └── all-MiniLM-L6-v2/
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── tokenizer.json
│       └── ...
├── src/
└── ...
```

### Q: 可以使用其他模型吗？

**A**: 可以，只要是 SentenceTransformer 兼容的模型:
- `sentence-transformers/all-MiniLM-L6-v2` (推荐)
- `sentence-transformers/paraphrase-MiniLM-L3-v2` (更小)
- `sentence-transformers/all-MiniLM-L12-v2` (更大，更慢)

### Q: 模型需要多大磁盘空间？

**A**: 
- MiniLM-L6-v2: ~22 MB
- MiniLM-L3-v2: ~13 MB
- BGE-large: ~1.3 GB

---

## 完整离线部署脚本

在服务器上创建 `setup_offline.sh`:

```bash
#!/bin/bash
# setup_offline.sh - 在服务器上运行

set -e

echo "Setting up offline deployment..."

# 1. 检查模型是否存在
if [ ! -d "./models/all-MiniLM-L6-v2" ]; then
    echo "ERROR: Model not found at ./models/all-MiniLM-L6-v2"
    echo "Please download the model on a machine with internet and upload it."
    exit 1
fi

# 2. 创建配置文件
cat > .kimi.toml << 'EOF'
[moonshot]
api_key = "your-api-key-here"

[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"
EOF

echo "Configuration created. Please edit .kimi.toml and add your API key."

# 3. 验证模型
echo "Verifying model..."
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('./models/all-MiniLM-L6-v2', local_files_only=True)
embedding = model.encode('test')
print(f'Model loaded successfully! Dimension: {len(embedding)}')
"

echo "Setup complete!"
```

# 修复 .kimi.toml 格式问题

## 问题

你的 `.kimi.toml` 文件格式不正确：

```toml
# 错误的格式
[
embedding
]
model = "./models/all-MiniLM-L6-v2"
```

## 正确格式

TOML 格式应该是：

```toml
# 正确的格式
[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"
```

## 快速修复

在服务器上运行：

```bash
cd /root/pg-source-qa

# 删除错误的配置文件
rm .kimi.toml

# 创建正确的配置文件
cat > .kimi.toml << 'EOF'
[moonshot]
api_key = "your-moonshot-api-key-here"
base_url = "https://api.moonshot.cn/v1"
model = "kimi-k2-0711-preview"

[embedding]
model = "./models/all-MiniLM-L6-v2"
device = "cpu"

[indexing]
chunk_size = 1000
batch_size = 32
EOF

# 验证
python scripts/verify_offline_setup.py
```

## 完整的 .kimi.toml 示例

```toml
[moonshot]
api_key = "sk-your-api-key"
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

## TOML 格式规则

1. **Section 格式**: `[section_name]` - 方括号在同一行
2. **Key-Value**: `key = "value"` - 等号两边有空格
3. **字符串**: 用双引号 `"` 包裹
4. **缩进**: 不需要缩进

## 验证 TOML 语法

```bash
# 安装 toml 验证工具
pip install toml

# 验证
python -c "import toml; toml.load('.kimi.toml'); print('Valid TOML!')"
```

## 修复后再次运行

```bash
python scripts/verify_offline_setup.py
```

预期输出：
```
✓ Models directory exists
✓ Model loaded successfully!
✓ Config file exists
✓ All checks passed! Ready for offline use.
```

# VibeCopilot 知识管理系统使用指南

本指南将帮助您快速上手 VibeCopilot 知识管理系统，包括环境配置、文档处理和知识查询等核心功能。

## 环境配置

### 前置条件

- Python 3.9+ 环境
- OpenAI API 密钥
- Obsidian（可选，用于可视化知识图谱）

### 安装依赖

```bash
cd /Users/<username>/Public/VibeCopilot
pip install -r requirements.txt
```

### 配置 API 密钥

将 OpenAI API 密钥设置为环境变量：

```bash
export OPENAI_API_KEY="你的OpenAI API密钥"
```

或者在脚本运行时临时设置：

```bash
OPENAI_API_KEY="你的密钥" python scripts/basic_memory/langchain_parser.py your_docs_folder
```

## 文档处理流程

### 1. 使用 LangChain 解析文档

```bash
cd /Users/<username>/Public/VibeCopilot
python scripts/basic_memory/langchain_parser.py 文档目录
```

示例：
```bash
python scripts/basic_memory/langchain_parser.py docs/dev/architecture
```

### 2. 使用 OpenAI 解析文档（替代方案）

```bash
cd /Users/<username>/Public/VibeCopilot
python scripts/basic_memory/openai_parser.py 文档目录
```

### 3. 导出到 Obsidian

```bash
cd /Users/<username>/Public/VibeCopilot
python scripts/basic_memory/export_to_obsidian.py
```

此操作会将解析结果导出到 `/Users/<username>/basic-memory/obsidian_vault` 目录。

## 知识查询

通过自然语言查询知识库：

```bash
cd /Users/<username>/Public/VibeCopilot
python scripts/basic_memory/query_knowledge.py --query "你的问题"
```

示例：
```bash
python scripts/basic_memory/query_knowledge.py --query "组件通信机制是如何工作的？"
```

## 常见问题

### 问题：无法连接 OpenAI API

- 检查 API 密钥是否正确
- 确认网络连接是否正常
- 可能需要设置代理：`export HTTPS_PROXY="your_proxy_url"`

### 问题：解析大型文档超时

- 尝试减小文档大小或分拆文档
- 增加超时设置：在脚本中修改 `timeout` 参数

### 问题：查询结果不准确

- 确保文档已成功解析
- 增加检索数量：修改 `search_kwargs={"k": 5}` 中的 k 值
- 尝试优化查询措辞，更明确地表达意图

## 数据管理

系统默认路径：

- 数据库：`/Users/<username>/basic-memory/main.db`
- 向量索引：`/Users/<username>/basic-memory/vector_index`
- Obsidian输出：`/Users/<username>/basic-memory/obsidian_vault`

### 备份数据

建议定期备份数据库和向量索引：

```bash
cp -r /Users/<username>/basic-memory /path/to/backup/$(date +%Y%m%d)
```

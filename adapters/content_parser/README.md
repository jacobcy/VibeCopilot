# 内容解析模块

统一的内容解析模块，用于处理Markdown文档和规则文件，支持多种LLM后端（OpenAI、Ollama等）。

## 功能

- 解析Markdown文档和规则文件
- 自动检测内容类型
- 支持OpenAI和Ollama作为解析引擎
- 支持不同的内容类型（rule、document、generic）
- 自动保存解析结果到数据库

## 使用方法

### 解析文件

```python
from adapters.content_parser import parse_file

# 解析规则文件
result = parse_file("path/to/rule.mdc", content_type="rule")

# 解析文档文件
result = parse_file("path/to/document.md", content_type="document")

# 自动检测内容类型
result = parse_file("path/to/file.md")

# 指定解析器
result = parse_file("path/to/file.md", parser_type="openai", model="gpt-4o-mini")
```

### 解析内容

```python
from adapters.content_parser import parse_content

# 解析规则内容
result = parse_content(content, context="file_path.mdc", content_type="rule")

# 解析文档内容
result = parse_content(content, context="file_path.md", content_type="document")
```

### 自定义解析器

```python
from adapters.content_parser import create_parser

# 创建自定义解析器
parser = create_parser(parser_type="openai", model="gpt-4o-mini", content_type="rule")
result = parser.parse_file("path/to/rule.mdc")
```

## 配置

通过环境变量配置默认行为：

- `VIBE_CONTENT_PARSER` - 默认解析器类型（openai或ollama，默认为openai）
- `VIBE_OPENAI_MODEL` - 默认OpenAI模型（默认为gpt-4o-mini）
- `VIBE_OLLAMA_MODEL` - 默认Ollama模型（默认为mistral）
- `OPENAI_API_KEY` - OpenAI API密钥

## 架构

```
content_parser/
├── __init__.py             # 模块入口
├── base_parser.py          # 解析器基类
├── openai_parser.py        # OpenAI解析器
├── ollama_parser.py        # Ollama解析器
├── parser_factory.py       # 解析器工厂
├── utils.py                # 工具函数
└── lib/                    # 通用库
    ├── content_template.py # 内容模板
    └── openai_api.py       # OpenAI API客户端
```

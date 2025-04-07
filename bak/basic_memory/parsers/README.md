# Basic Memory 解析器

Basic Memory解析器是VibeCopilot知识处理系统的核心组件，提供各种文档解析和知识提取功能。

## 解析器类型

目前支持的解析器包括:

1. **RegexParser** - 使用正则表达式进行基础的文档解析
2. **LangChainKnowledgeProcessor** - 使用LangChain进行高级语义解析和知识提取

## LangChain知识处理器

LangChain知识处理器(`LangChainKnowledgeProcessor`)是一个强大的解析引擎，能够从文档中提取结构化知识，构建知识图谱。

### 工作原理

处理流程包括以下步骤:

1. **文档加载**: 从指定目录加载各种格式的文档
2. **文档分割**: 将大型文档分割成适合处理的较小块
3. **向量化**: 将文本块转换为向量嵌入
4. **知识提取**: 使用大语言模型从文本中提取实体和关系
5. **知识存储**: 将提取的知识结构化并存储到数据库中

### 使用方法

**1. 命令行使用**

```bash
# 基本使用
python -m adapters.basic_memory.cli import langchain ./文档目录

# 高级选项
python -m adapters.basic_memory.cli import langchain ./文档目录 \
  --model gpt-4o-mini \
  --db ./knowledge.db
```

**2. 代码中使用**

```python
from adapters.basic_memory.parsers import LangChainKnowledgeProcessor

# 初始化处理器
processor = LangChainKnowledgeProcessor(
    source_dir="./文档目录",
    model="gpt-4o-mini",
    db_path="./knowledge.db"
)

# 处理文档
processor.process_documents()
```

## 正则表达式解析器

正则表达式解析器(`RegexParser`)使用预定义的正则表达式模式来从文本中提取信息，适合处理具有固定格式的文档。

### 使用方法

**1. 命令行使用**

```bash
python -m adapters.basic_memory.cli parse regex ./文档目录或文件
```

**2. 代码中使用**

```python
from adapters.basic_memory.parsers import parse_with_regex

# 解析文本
result = parse_with_regex(text_content, document_title)
```

## 扩展解析器

要添加新的解析器，请遵循以下步骤:

1. 在`parsers`目录下创建新的解析器模块(如`my_parser.py`)
2. 在`__init__.py`中导出新的解析器
3. 为CLI添加对应的命令支持

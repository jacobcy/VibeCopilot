# 统一解析框架

本模块为VibeCopilot项目中的内容解析提供了统一的方法，包括规则、文档和实体。

## 概述

解析框架包括：

1. **基础解析器接口**：所有解析器的通用接口
2. **特定解析器实现**：特定后端的实现（OpenAI、Ollama、Regex）
3. **内容处理器**：针对不同内容类型的专用处理器
4. **工厂**：用于创建适当解析器实例的工厂

## 结构

- `base_parser.py`：定义解析器接口的抽象基类
- `parser_factory.py`：用于创建解析器实例的工厂
- `parsers/`：特定后端的解析器实现
  - `openai_parser.py`：基于OpenAI的解析器
  - `ollama_parser.py`：基于Ollama的解析器
  - `regex_parser.py`：用于简单模式匹配的基于正则表达式的解析器
- `processors/`：针对特定内容类型的处理器
  - `rule_processor.py`：用于规则内容的处理器
  - `document_processor.py`：用于文档内容的处理器
  - `entity_processor.py`：用于实体提取的处理器

## 使用

### 基本用法

```python
from src.core.parsing.parser_factory import create_parser

# 使用OpenAI后端创建规则解析器
parser = create_parser("rule", "openai")

# 解析规则文件
result = parser.parse_file(".cursor/rules/core-rules/concept.mdc")

# 解析规则文本
rule_text = "# My Rule\n\nThis is a rule example."
result = parser.parse_text(rule_text, "rule")
```

### 使用处理器

```python
from src.core.parsing.processors.rule_processor import RuleProcessor
from src.core.parsing.processors.document_processor import DocumentProcessor

# 创建处理器
rule_processor = RuleProcessor()
document_processor = DocumentProcessor()

# 处理规则文件
rule_data = rule_processor.process_rule_file(".cursor/rules/core-rules/concept.mdc")

# 处理文档文件
doc_data = document_processor.process_document_file("docs/user/guide.md")
```

### 实体提取

```python
from src.core.parsing.processors.entity_processor import EntityProcessor

# 创建实体处理器
entity_processor = EntityProcessor()

# 从内容中提取实体
content = "VibeCopilot uses Python and TypeScript."
result = entity_processor.process_content(content)

# 访问提取的实体和关系
entities = result["entities"]
relationships = result["relationships"]
```

## 扩展

### 添加新的解析器后端

1. 在`parsers/`目录中创建一个新的解析器类
2. 实现`BaseParser`接口
3. 在`parser_factory.py`中注册解析器

### 添加新的内容类型

1. 更新解析器实现以处理新的内容类型
2. 在`processors/`目录中创建一个新的处理器类

## 配置

在创建解析器或处理器时可以提供配置：

```python
config = {
    "model": "gpt-4",
    "temperature": 0.2,
    "max_tokens": 4000
}

parser = create_parser("rule", "openai", config)
```

默认配置从应用程序配置中加载。

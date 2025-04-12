# 统一解析框架

本模块为VibeCopilot项目中的内容解析提供了统一的方法，包括规则、文档和实体。

## 概述

解析框架包括：

1. **基础解析器接口**：所有解析器的通用接口
2. **统一LLM解析器**：支持多种LLM提供者的统一实现
3. **特定解析器实现**：非LLM的特定解析器如正则表达式解析器
4. **内容处理器**：针对不同内容类型的专用处理器
5. **LLM服务层**：与不同LLM提供者API交互
6. **工厂**：用于创建适当解析器实例和LLM服务的工厂

## 结构

- `base_parser.py`：定义解析器接口的抽象基类
- `parser_factory.py`：用于创建解析器实例的工厂
- `prompt_templates.py`：提供给LLM的各种内容类型提示模板
- `parsers/`：解析器实现
  - `llm_parser.py`：统一的LLM解析器，支持多种LLM提供者
  - `openai_parser.py`：兼容层（使用统一LLM解析器）
  - `ollama_parser.py`：兼容层（使用统一LLM解析器）
  - `regex_parser.py`：用于简单模式匹配的基于正则表达式的解析器
- `processors/`：针对特定内容类型的处理器
  - `rule_processor.py`：用于规则内容的处理器
  - `document_processor.py`：用于文档内容的处理器
  - `entity_processor.py`：用于实体提取的处理器
  - `workflow_processor.py`：用于工作流内容的处理器

## LLM服务层

- `src/llm/service_factory.py`：用于创建LLM服务实例的工厂
- `src/llm/openai_service.py`：与OpenAI API交互的服务
- `src/llm/providers/`：不同LLM提供者的服务实现
  - `ollama_service.py`：与Ollama API交互的服务

## 使用

### 基本用法

```python
from src.parsing.parser_factory import create_parser

# 创建LLM解析器，支持"openai"和"ollama"提供者
parser = create_parser("rule", "openai")

# 解析规则文件
result = parser.parse_file(".cursor/rules/core-rules/concept.mdc")

# 解析规则文本
rule_text = "# My Rule\n\nThis is a rule example."
result = parser.parse_text(rule_text, "rule")
```

### 使用处理器

```python
from src.parsing.processors import RuleProcessor, DocumentProcessor, WorkflowProcessor

# 创建处理器
rule_processor = RuleProcessor()
document_processor = DocumentProcessor()
workflow_processor = WorkflowProcessor()

# 处理规则文件
rule_data = rule_processor.process_rule_file(".cursor/rules/core-rules/concept.mdc")

# 处理文档文件
doc_data = document_processor.process_document_file("docs/user/guide.md")

# 解析工作流内容
workflow_data = await workflow_processor.parse_workflow(workflow_content)
```

### 实体提取

```python
from src.parsing.processors import EntityProcessor

# 创建实体处理器，可以选择"openai"或"ollama"后端
entity_processor = EntityProcessor(backend="openai")

# 从内容中提取实体
content = "VibeCopilot uses Python and TypeScript."
result = entity_processor.process_content(content)

# 访问提取的实体和关系
entities = result["entities"]
relationships = result["relationships"]
```

## 扩展

### 添加新的LLM提供者

1. 在`src/llm/providers/`目录中创建一个新的服务类，如`some_provider_service.py`
2. 实现与其他服务相同的接口
3. 在`src/llm/service_factory.py`中注册新的服务
4. LLMParser会自动使用新添加的提供者

### 添加新的内容类型

1. 在`src/parsing/prompt_templates.py`中添加新的提示模板
2. 在`processors/`目录中创建一个新的处理器类

## 验证

内容验证功能位于`src/validation/`模块：

- `workflow_validation.py`：提供工作流验证函数
- `core/workflow_validator.py`：提供工作流验证器类

```python
# 使用函数式API
from src.validation import workflow_validation

# 验证工作流
workflow_validation.validate_workflow(workflow_data)
```

## 配置

在创建解析器或处理器时可以提供配置：

```python
config = {
    "provider": "openai",  # 或 "ollama"
    "model": "gpt-4",      # 对于OpenAI
    "temperature": 0.2,
    "max_tokens": 4000
}

parser = create_parser("rule", "openai", config)
```

默认配置从应用程序配置中加载。

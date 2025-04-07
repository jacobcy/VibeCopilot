# VibeCopilot 适配器模块

## 重要提示：模块重构

**注意**：适配器模块已经重构！内容解析和数据存储功能已被统一到新框架中：

- `adapters/content_parser` → `src/core/parsing`
- `adapters/rule_parser` → `src/core/parsing`（特别是 RuleProcessor）
- `adapters/basic_memory` → `src/memory` 和 `src/db/vector`

适配器模块仍然保留，但只是作为转发到新模块的兼容层。请在新代码中直接使用新模块。

## 当前适配器

VibeCopilot 支持多种适配器，用于与不同的服务和工具集成：

### 内容解析 (已迁移)

内容解析功能已迁移到 `src/core/parsing`。

```python
# 旧用法
from adapters.content_parser import parse_file, parse_content

# 新用法
from src.core.parsing import create_parser
parser = create_parser("document", "openai")
result = parser.parse_file("path/to/file.md")
```

### 规则解析 (已迁移)

规则解析功能已迁移到 `src/core/parsing` 和 RuleProcessor。

```python
# 旧用法
from adapters.rule_parser import parse_rule_file

# 新用法
from src.core.parsing.processors.rule_processor import RuleProcessor
processor = RuleProcessor()
result = processor.process_rule_file("path/to/rule.mdc")
```

### 基本记忆 (已迁移)

基本记忆功能已迁移到 `src/memory` 和 `src/db/vector`。

```python
# 旧用法
from adapters.basic_memory import MemoryManager

# 新用法
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
```

### 其他适配器

其他适配器仍然保持原状：

- `obsidian`: Obsidian服务适配器
- `docusaurus`: Docusaurus文档适配器
- `n8n`: n8n工作流适配器
- `gitdiagram`: Git图表适配器
- `github_project`: GitHub项目适配器
- `notion_to_md`: Notion导出适配器

## 未来计划

未来将继续重构其他适配器模块，使其更加模块化和易于维护。建议开发新功能时直接使用新的统一框架。

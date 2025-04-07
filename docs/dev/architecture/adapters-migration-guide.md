# 适配器模块迁移指南

本文档提供了从旧的适配器模块迁移到新的统一框架的指南。

## 背景

VibeCopilot 项目已经实现了内容解析和数据存储的统一框架，替代了原来的多个独立模块：

- `adapters/content_parser`：已迁移到 `src/core/parsing`
- `adapters/rule_parser`：已迁移到 `src/core/parsing`（特别是 RuleProcessor）
- `adapters/basic_memory`：已迁移到 `src/memory` 和 `src/db/vector`

旧的适配器模块仍然保留，但现在它们只是作为简单的兼容层，将调用转发到新的统一框架。

## 迁移步骤

### 1. 从 content_parser 迁移

#### 旧用法

```python
from adapters.content_parser import ContentParser, parse_file, parse_content

# 使用解析器实例
parser = ContentParser()
result = parser.parse("# My Document\n\nThis is content.")

# 或使用便捷函数
result = parse_file("path/to/document.md")
```

#### 新用法

```python
from src.core.parsing import create_parser

# 使用工厂创建解析器
parser = create_parser("document", "openai")  # 或 "ollama", "regex"
result = parser.parse_text("# My Document\n\nThis is content.")

# 解析文件
result = parser.parse_file("path/to/document.md")
```

### 2. 从 rule_parser 迁移

#### 旧用法

```python
from adapters.rule_parser import parse_rule_file, RuleParser

# 解析规则文件
rule = parse_rule_file(".cursor/rules/core-rules/concept.mdc")

# 或使用解析器实例
parser = RuleParser()
rule = parser.parse_rule_file(".cursor/rules/core-rules/concept.mdc")
```

#### 新用法

```python
from src.core.parsing.processors.rule_processor import RuleProcessor

# 创建规则处理器
processor = RuleProcessor(backend="openai")  # 或 "ollama", "regex"

# 处理规则文件
rule = processor.process_rule_file(".cursor/rules/core-rules/concept.mdc")

# 处理规则目录
rules = processor.process_rule_directory(".cursor/rules/core-rules")
```

### 3. 从 basic_memory 迁移

#### 旧用法

```python
from adapters.basic_memory import MemoryManager

# 创建内存管理器
memory = MemoryManager()

# 同步内容
await memory.sync_all()

# 存储和检索内容
# ...
```

#### 新用法

```python
# 根据需要导入相应的管理器
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.sync_service import SyncService
from src.db.vector.memory_adapter import BasicMemoryAdapter

# 创建同步服务
sync_service = SyncService()
await sync_service.sync_all()

# 管理实体
entity_manager = EntityManager()
entity = await entity_manager.create_entity(
    "technology",
    {"name": "Python", "version": "3.9"}
)

# 记录观察
observation_manager = ObservationManager()
observation = await observation_manager.record_observation(
    "VibeCopilot 项目已更新。",
    {"type": "development", "title": "项目更新"}
)

# 管理关系
relation_manager = RelationManager()
relation = await relation_manager.create_relation(
    "entity_vibecopilot", "entity_python", "uses"
)

# 向量存储
vector_store = BasicMemoryAdapter()
results = await vector_store.search("VibeCopilot 项目")
```

## 完整示例

### 使用新的解析框架

```python
from src.core.parsing import create_parser
from src.core.parsing.processors.document_processor import DocumentProcessor
from src.core.parsing.processors.rule_processor import RuleProcessor
from src.core.parsing.processors.entity_processor import EntityProcessor

# 创建基本解析器
parser = create_parser("generic", "openai")
result = parser.parse_file("path/to/file.md")

# 使用专门的处理器
doc_processor = DocumentProcessor()
rule_processor = RuleProcessor()
entity_processor = EntityProcessor()

# 处理文档
doc = doc_processor.process_document_file("docs/user/guide.md")

# 处理规则
rule = rule_processor.process_rule_file(".cursor/rules/core-rules/concept.mdc")

# 提取实体
content = "VibeCopilot 使用 Python 和 TypeScript。"
entities = entity_processor.process_content(content)
```

### 使用新的内存系统

```python
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.sync_service import SyncService

# 同步内容
sync_service = SyncService()
await sync_service.sync_rules([".cursor/rules/core-rules/concept.mdc"])
await sync_service.sync_documents(["docs/user/guide.md"])

# 管理实体
entity_manager = EntityManager()
python_entity = await entity_manager.create_entity(
    "technology",
    {
        "name": "Python",
        "version": "3.9",
        "description": "Python 是一种编程语言"
    }
)

typescript_entity = await entity_manager.create_entity(
    "technology",
    {
        "name": "TypeScript",
        "version": "4.5",
        "description": "TypeScript 是 JavaScript 的类型化超集"
    }
)

# 管理关系
relation_manager = RelationManager()
await relation_manager.create_relation(
    python_entity["id"],
    typescript_entity["id"],
    "relates_to",
    {"similarity": "high"}
)

# 记录观察
observation_manager = ObservationManager()
await observation_manager.record_observation(
    "Python 和 TypeScript 都是 VibeCopilot 项目使用的编程语言。",
    {
        "type": "development",
        "title": "技术栈观察",
        "tags": ["programming", "technology"]
    },
    related_entities=[python_entity["id"], typescript_entity["id"]]
)
```

## 注意事项

1. 新框架提供了更一致的 API 和更丰富的功能
2. 旧模块将在未来版本中移除，建议尽快迁移
3. 如果遇到迁移问题，可以参考各模块的 README 文件或查看单元测试示例

## 更多资源

- [统一内容解析框架文档](../../src/core/parsing/README.md)
- [内存管理系统文档](../../src/memory/README.md)
- [向量存储文档](../../src/db/vector/README.md)
- [统一内容解析与数据存储集成开发记录](../../blog/统一内容解析与数据存储集成开发记录.md)

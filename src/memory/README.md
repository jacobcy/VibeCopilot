# 记忆管理系统概述

## 概述

记忆系统由以下部分组成：

1. **同步服务（Sync Service）**：将本地内容与Basic Memory同步
2. **实体管理器（Entity Manager）**：管理知识实体及其属性
3. **观察管理器（Observation Manager）**：记录和检索观察内容（事实、事件、状态）
4. **关系管理器（Relation Manager）**：处理实体之间的关系

## 结构

- `sync_service.py`：本地内容和Basic Memory的同步服务
- `entity_manager.py`：知识实体的管理
- `observation_manager.py`：用于记录事实和事件的观察管理
- `relation_manager.py`：实体关系管理

## 使用方法

### 同步服务

同步服务用于将本地内容（规则、文档）与Basic Memory同步。

```python
from src.memory.sync_service import SyncService

# 创建同步服务
sync_service = SyncService()

# 同步所有规则
result = await sync_service.sync_rules()

# 同步特定文档文件
files = ["docs/user/guide.md", "docs/dev/architecture.md"]
result = await sync_service.sync_documents(files)

# 同步所有内容
result = await sync_service.sync_all()
```

### 实体管理器

实体管理器用于创建、更新和管理知识实体。

```python
from src.memory.entity_manager import EntityManager

# 创建实体管理器
entity_manager = EntityManager()

# 创建新实体
entity = await entity_manager.create_entity(
    entity_type="technology",
    properties={
        "name": "Python",
        "version": "3.9",
        "category": "programming_language"
    }
)

# 通过ID获取实体
python_entity = await entity_manager.get_entity(entity["id"])

# 更新实体
updated_entity = await entity_manager.update_entity(
    entity["id"],
    properties={"version": "3.10"}
)

# 搜索实体
results = await entity_manager.search_entities("Python programming")
```

### 观察管理器

观察管理器用于记录和检索观察内容。

```python
from src.memory.observation_manager import ObservationManager

# 创建观察管理器
observation_manager = ObservationManager()

# 记录观察内容
observation = await observation_manager.record_observation(
    content="VibeCopilot仓库已更新，添加了新功能。",
    metadata={
        "type": "development",
        "title": "仓库更新",
        "tags": ["github", "development"]
    },
    related_entities=["entity_vibecopilot", "entity_github"]
)

# 获取观察内容
result = await observation_manager.get_observation(observation["id"])

# 搜索观察内容
results = await observation_manager.search_observations(
    query="仓库更新",
    observation_type="development"
)

# 获取最近的观察内容
recent = await observation_manager.get_recent_observations(limit=5)
```

### 关系管理器

关系管理器用于创建和查询实体之间的关系。

```python
from src.memory.relation_manager import RelationManager

# 创建关系管理器
relation_manager = RelationManager()

# 创建关系
relation = await relation_manager.create_relation(
    source_id="entity_vibecopilot",
    target_id="entity_python",
    relation_type="uses",
    properties={"since": "2023-01-01"}
)

# 获取实体的关系
relations = await relation_manager.get_relations(
    entity_id="entity_vibecopilot",
    relation_type="uses"
)

# 查找实体间的路径
path = await relation_manager.find_path(
    source_id="entity_vibecopilot",
    target_id="entity_claude",
    max_depth=3
)

# 查找共同连接
common = await relation_manager.find_common_connections(
    entity_id1="entity_vibecopilot",
    entity_id2="entity_cursor"
)
```

## 配置

所有组件都接受可选的配置参数，用于自定义行为。

```python
config = {
    "default_folder": "custom_folder",
    "default_tags": "custom_tag"
}

entity_manager = EntityManager(config)
```

默认配置从应用程序配置中加载。

## Basic Memory集成

VibeCopilot使用Basic Memory作为底层知识库系统。Basic Memory提供了强大的本地知识存储能力，所有内容以Markdown文件形式存储，并具有语义搜索能力。

### 配置Basic Memory

VibeCopilot在`.ai/memory`目录下设置了专用的Basic Memory项目：

```bash
# 添加VibeCopilot项目
basic-memory project add vibecopilot ~/Public/VibeCopilot/.ai/memory

# 设置为默认项目
basic-memory project default vibecopilot
```

### 命令实现方式

VibeCopilot通过以下方式实现memory命令：

1. **命令行接口**：`memory_click.py`定义了命令及其参数
2. **子命令处理**：`memory_subcommands.py`提供子命令处理逻辑
3. **具体处理程序**：
   - `mcp_handlers.py`：通过调用basic-memory工具实现核心功能
   - `script_handlers.py`：提供额外的脚本处理功能

### 命令使用示例

```bash
# 列出知识库内容
vc memory list

# 显示特定内容
vc memory show --path "docs/architecture.md"

# 创建新笔记
vc memory create --title "开发笔记" --folder "notes" --content "这是一篇开发笔记"

# 搜索内容
vc memory search --query "架构设计"

# 同步知识库
vc memory sync

# 导入外部文档
vc memory import-docs --source-dir "external/docs"
```

### 与Basic Memory的集成方式

VibeCopilot的memory命令通过以下方式与Basic Memory集成：

1. **命令转发**：将VibeCopilot命令转换为Basic Memory命令
2. **结果格式化**：将Basic Memory输出格式化为VibeCopilot标准格式
3. **异常处理**：提供友好的错误信息和故障恢复机制
4. **权限管理**：确保安全的文件操作和访问控制

整个系统设计为模块化结构，使得记忆管理功能可以方便地扩展和定制。

# 数据库模块 (src/db)

本模块提供 VibeCopilot 的数据持久化层，负责数据的存储、检索和管理，采用 SQLAlchemy ORM 框架与 SQLite 数据库。

## 模块结构

```
src/db/
├── README.md                # 本文档
├── __init__.py              # 模块入口，导出核心功能
├── connection_manager.py    # 数据库连接管理器
├── repository.py            # 数据访问对象基类
├── service.py               # 统一数据库服务接口
├── core/                    # 核心组件
│   ├── entity_manager.py    # 实体管理器
│   └── mock_storage.py      # 模拟存储
├── models/                  # 数据库模型定义
├── repositories/            # 数据访问对象实现
└── specific_managers/       # 特定实体管理器
```

## 核心组件说明

### 1. DatabaseService

统一的数据库服务入口，整合了各种仓库对象和实体管理器，提供面向业务层的 API：

```python
from src.db.service import DatabaseService

# 创建数据库服务实例
db_service = DatabaseService()

# 使用通用方法
entities = db_service.get_entities("epic")
entity = db_service.get_entity("task", "task_123")
db_service.create_entity("story", {"title": "新故事"})

# 使用特定实体方法
epics = db_service.list_epics()
db_service.create_task({"title": "实现新功能", "priority": "high"})
```

### 2. Repository 基类

所有具体仓库类的基类，提供通用的 CRUD 操作：

```python
from src.db.repository import Repository
from src.models.db import Task

class TaskRepository(Repository[Task]):
    def __init__(self, session):
        super().__init__(session, Task)

    # 可添加特定于任务的数据访问方法
    def get_completed_tasks(self):
        return self.filter(completed=True)
```

### 3. EntityManager

整合不同类型的仓库，提供统一的实体管理接口：

```python
# EntityManager通常不直接使用，而是通过DatabaseService访问
entity_manager = EntityManager(repositories, mock_storage)
entities = entity_manager.get_entities("epic")
```

### 4. MockStorage

提供模拟存储功能，用于处理尚未完全迁移到数据库的实体类型：

```python
mock_storage = MockStorage()
mock_storage.get_entities("template")  # 从JSON文件读取
```

## 使用方法

### 基本使用

```python
from src.db.service import DatabaseService

# 初始化服务
db_service = DatabaseService()

# 获取所有epic
epics = db_service.get_entities("epic")
print(f"找到 {len(epics)} 个Epic")

# 创建新任务
task_data = {
    "title": "实现数据库模块",
    "description": "设计并实现数据库访问层",
    "status": "in_progress",
    "priority": "high"
}
task = db_service.create_task(task_data)
print(f"创建任务 '{task['title']}', ID: {task['id']}")
```

### 在命令行界面使用

数据库模块通过 CLI 命令提供交互式界面：

```bash
# 初始化数据库
vibecopilot db init

# 列出所有Epic
vibecopilot db list --type epic

# 查看特定任务
vibecopilot db show --type task --id task_123

# 创建实体
vibecopilot db create --type story --data '{"title": "实现X功能", "priority": "high"}'
```

## 数据模型和架构

### 模型层次关系

VibeCopilot 使用分层数据模型：

1. **Roadmap**: 顶层实体，代表一个完整的路线图计划
2. **Epic**: 属于特定的 Roadmap，表示大型功能模块
3. **Story**: 属于特定的 Epic，表示用户故事
4. **Task**: 属于特定的 Story，表示具体任务
5. **Milestone**: 属于特定的 Roadmap，表示里程碑

### 模型和仓库对应关系

| 模型类 | 仓库类 | 描述 |
|-------|-------|------|
| `Roadmap` | `RoadmapRepository` | 路线图 |
| `Epic` | `EpicRepository` | 史诗级功能 |
| `Story` | `StoryRepository` | 用户故事 |
| `Task` | `TaskRepository` | 具体任务 |
| `Milestone` | `MilestoneRepository` | 里程碑 |

## 错误处理

本模块采用异常处理机制：

1. 仓库层捕获数据库异常并记录日志
2. 服务层处理业务逻辑异常，提供友好错误信息
3. 每个操作都有详细的日志记录，便于调试

## 扩展和维护

### 添加新模型

1. 在 `src/models/db/` 目录下创建模型类
2. 确保模型继承自 `Base` 并实现 `to_dict()` 方法
3. 创建对应的仓库类，继承自 `Repository`
4. 在 `DatabaseService` 中注册仓库并提供访问方法

### 调试技巧

1. 启用详细日志记录：`LOG_LEVEL=DEBUG vibecopilot ...`
2. 使用 `--verbose` 选项获取详细输出：`vibecopilot db list --type epic --verbose`
3. 在开发过程中，可以使用 `db_service.get_stats()` 获取数据库状态

## 注意事项

1. 不要直接修改数据库文件，总是通过 API 进行操作
2. 使用前确保已调用 `init_db()` 初始化数据库
3. 在处理大量数据时，注意使用分页查询以提高性能
4. 避免递归嵌套问题，使用 `_safe_to_dict()` 方法而非模型自带的 `to_dict()`

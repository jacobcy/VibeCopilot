# 路线图 (Roadmap) 模块

路线图模块提供了VibeCopilot中路线图管理的核心功能，包括数据存储、检索、操作以及与外部系统的同步。

## 模块结构

该模块采用分层架构，包含以下主要组件：

```
src/roadmap/
├── __init__.py      # 导出核心服务和模型
├── core/            # 核心功能实现
│   ├── __init__.py
│   ├── manager.py           # 路线图管理核心逻辑
│   ├── status.py            # 路线图状态处理
│   └── updater.py           # 路线图更新逻辑
├── service/         # 服务层 - 模块的主要入口和业务逻辑
│   ├── __init__.py
│   ├── roadmap_service.py   # 主服务类，整合其他组件
│   ├── roadmap_data.py      # 数据访问和查询逻辑
│   ├── roadmap_operations.py # 路线图增删改操作逻辑
│   └── roadmap_status.py    # 路线图状态服务
├── sync/            # 同步服务 - 处理与外部系统的数据同步
│   ├── __init__.py
│   ├── github_sync.py        # GitHub 同步实现
│   ├── github_api_facade.py  # GitHub API 封装
│   ├── github_mapper.py      # GitHub数据映射
│   ├── yaml_sync.py          # 新版YAML同步服务
│   ├── yaml.py               # YAML文件导入/导出实现
│   ├── yaml_validator_schema.py   # YAML验证架构
│   ├── yaml_validator_section.py  # YAML部分验证
│   └── yaml_validator_cli.py      # YAML验证CLI工具
├── dao/             # 数据访问层
├── models.py        # 数据模型定义
├── status.py        # 状态提供者
├── docs/            # 文档
│   └── entity_relationships.md  # 实体关系模型说明
└── examples/        # 示例代码和指南
```

## 组件说明

- **核心层 (`core`)**: 提供路线图功能的基础实现。
  - `RoadmapManager`: 路线图数据的基础管理功能。
  - `RoadmapStatus`: 路线图状态的核心处理逻辑。
  - `RoadmapUpdater`: 处理路线图信息的更新逻辑。

- **服务层 (`service`)**: 作为路线图模块的主要接口，提供统一的路线图管理功能。
  - `RoadmapService`: 整合所有路线图功能的主服务类。
  - `roadmap_data.py`: 负责路线图数据的访问、查询和聚合。
  - `roadmap_operations.py`: 负责路线图及其关联元素（Epics, Stories, Tasks, Milestones）的创建、更新和删除操作。
  - `roadmap_status.py`: 提供路线图状态的服务接口。

- **同步层 (`sync`)**: 负责路线图与外部系统的数据同步。
  - `GitHubSyncService`: 实现与GitHub仓库的项目板和议题的双向同步。详细指南参见 [`roadmap_github_sync.md`](./docs/roadmap_github_sync.md)。
  - `YamlSyncService`: 处理路线图数据的YAML文件导入和导出，并内置了验证逻辑。详细指南参见 [`roadmap_yaml_sync.md`](./docs/roadmap_yaml_sync.md)。
  - 验证组件: 包括`yaml_validator_schema.py`, `yaml_validator_section.py`和`yaml_validator_cli.py`。
  - 验证工具：python src/roadmap/sync/yaml_validator_cli.py validate path/to/roadmap.yaml

## 架构关系

路线图服务采用分层设计：

- `service`层为对外接口，调用`core`层的核心实现
- `core`层封装基础逻辑，使用`dao`层访问数据
- `sync`层提供与外部系统的集成能力

模块间的导出遵循完全限定路径的导入方式，如：
```python
from src.roadmap.service.roadmap_service import RoadmapService
```

## 主要功能

- **路线图管理**: 创建、查询、更新、删除和切换活动路线图。
- **元素管理**: 管理路线图下的 Epics, Stories, Tasks, Milestones。
- **状态管理**: 查询和更新路线图元素的状态。
- **数据同步**:
  - **GitHub同步**: 与GitHub Projects和Issues双向同步（需要配置环境变量）。
  - **YAML导入/导出**: 支持路线图数据的导入和导出，内置格式验证。
- **工作流集成**: 通过Task与Session的关联，实现路线图与工作流执行的无缝连接。

## 路线图与工作流集成

VibeCopilot实现了路线图(Roadmap)与工作流(Workflow)的无缝集成，核心在于Task与FlowSession之间的关联关系：

### 实体关系模型

- **Story → Task → Session**: 采用单向关联机制，遵循从规划到执行的自然工作流向：
  - **Story**: 代表开发中的用户故事或功能点，是路线图的组成部分
  - **Task**: 代表具体的工作项，可以关联到Story成为路线图的一部分
  - **Session**: 工作流会话，专注于完成一个具体Task的执行实例

### 关联机制

- Task通过`story_id`关联到Story
- Session通过`task_id`关联到Task
- 每个Session专注于一个Task，而一个Task可以有多个Session

### 集成优势

1. **专注原则**: 工作流会话(Session)专注于完成单个任务，使工作目标更清晰
2. **工作流跟踪**: 任务可能需要多次不同类型的工作流才能完成，通过多个Session记录完整过程
3. **进度可视化**: 通过查看任务关联的会话，了解具体工作进度和执行方法
4. **双向导航**: 可从路线图任务查看相关工作流，也可从工作流会话了解其所服务的任务

### CLI使用示例

```bash
# 创建关联到故事的任务
vc task create --title "实现登录功能" --link-story story_123

# 查看特定故事下的所有任务
vc task list --story story_123

# 创建专注于特定任务的工作流会话
vc flow session create --flow auth_flow --task task_456

# 查看任务相关的工作流会话
vc task show task_456
```

详细的实体关系和数据结构请参考 [`entity_relationships.md`](./docs/entity_relationships.md)。

## 路线图状态机制

路线图模块实现了可靠的状态持久化机制，确保用户会话间保持状态一致性：

### 1. 活动路线图状态持久化

- **存储机制**:
  - 活动路线图ID存储在`system_configs`表中
  - 使用键值对形式：`key = "active_roadmap_id"`, `value = "<roadmap_id>"`
  - 通过`SystemConfigRepository`管理配置访问

- **持久化流程**:
  - `RoadmapService`启动时自动从数据库加载活动路线图
  - 路线图切换时，通过`set_active_roadmap()`方法更新数据库
  - 所有事务操作确保数据一致性，失败时自动回滚

- **验证机制**:
  - 加载活动路线图ID时验证路线图是否存在
  - 无效ID自动从配置表中移除，防止状态错误

### 2. 状态服务集成

- **RoadmapStatusProvider**:
  - 实现`IStatusProvider`接口，向状态系统提供路线图状态
  - 自动获取活动路线图的进度和状态信息
  - 支持查询、更新路线图元素状态

- **状态数据模型**:
  - 路线图状态包含整体进度、里程碑状态和任务完成情况
  - 状态更新通过事件通知机制触发订阅者

### 3. 状态查询API

- `get_active_roadmap_id()`: 获取当前活动路线图ID
- `check_roadmap_status()`: 检查路线图、里程碑或任务的状态
- `get_roadmap_status_summary()`: 获取路线图状态概览（进度百分比、完成任务数等）

### 4. 状态更新流程

- **任务状态更新**:
  - 通过`update_roadmap_status(element_id, element_type, status)`更新元素状态
  - 状态变更触发`RoadmapStatus`中的计算逻辑，更新相关联元素状态

- **状态传播**:
  - 任务状态变更自动更新所属故事状态
  - 故事状态变更影响所属Epic状态
  - Epic状态反映在整体路线图进度上

## API 概览 (RoadmapService)

*注意：以下为部分核心方法示例，具体参数和返回值请参考源代码。*

### 路线图管理

- `create_roadmap(...)`: 创建新路线图。
- `delete_roadmap(roadmap_id)`: 删除路线图。
- `get_roadmap(roadmap_id)`: 获取路线图基本信息。
- `list_roadmaps()`: 获取所有路线图列表。
- `set_active_roadmap(roadmap_id)`: 设置当前用户的活动路线图。
- `get_active_roadmap_id()`: 获取当前活动路线图ID。
- `get_roadmap_details(roadmap_id)`: 获取路线图详细信息（包含所有元素）。
- `get_roadmap_status_summary(roadmap_id)`: 获取路线图状态概览。

### 数据访问与操作

- `get_epics(roadmap_id)`: 获取路线图下的 Epics。
- `get_stories(roadmap_id, epic_id=None)`: 获取路线图或特定 Epic 下的 Stories。
- `get_tasks(roadmap_id, story_id=None, milestone_id=None)`: 获取路线图、特定 Story 或 Milestone 下的 Tasks。
- `get_milestones(roadmap_id)`: 获取路线图下的 Milestones。
- `create_epic(roadmap_id, ...)`: 创建 Epic。
- `create_story(roadmap_id, epic_id, ...)`: 创建 Story。
- `create_task(roadmap_id, story_id, ...)`: 创建 Task。
- `update_task_status(task_id, status, ...)`: 更新任务状态。
- `add_comment_to_task(task_id, ...)`: 为任务添加评论。
- `get_task_sessions(task_id)`: 获取任务关联的所有工作流会话。
- *(其他创建/更新/删除方法)*

### 同步操作

- `sync_to_github(roadmap_id)`: 将指定路线图同步到关联的 GitHub 项目。
- `sync_from_github(roadmap_id)`: 从关联的 GitHub 项目同步状态更新到本地路线图。
- `export_to_yaml(roadmap_id, output_path)`: 将路线图导出为 YAML 文件。
- `import_from_yaml(file_path, roadmap_id=None)`: 从 YAML 文件导入或更新路线图。

## 使用示例

### 基本操作

```python
from src.roadmap import RoadmapService

# 创建服务实例 (通常通过依赖注入获取)
service = RoadmapService()

# 创建新路线图 (假设返回包含 roadmap_id 的字典)
roadmap_info = service.create_roadmap(title="新项目路线图", description="...")
roadmap_id = roadmap_info['id']

# 设置为活动路线图
service.set_active_roadmap(roadmap_id)

# 添加 Epic
epic_info = service.create_epic(roadmap_id, title="核心功能")
epic_id = epic_info['id']

# 添加 Story
story_info = service.create_story(roadmap_id, epic_id, title="用户认证")
story_id = story_info['id']

# 添加 Task
task_info = service.create_task(roadmap_id, story_id, title="实现登录接口")
task_id = task_info['id']

# 获取路线图详情
details = service.get_roadmap_details(roadmap_id)
print(f"路线图 '{details['title']}' 包含 {len(details.get('tasks', []))} 个任务")

# 获取状态概览
summary = service.get_roadmap_status_summary(roadmap_id)
print(f"路线图进度: {summary['progress']}%")
```

### 状态管理示例

```python
from src.roadmap import RoadmapService

service = RoadmapService()

# 获取当前活动路线图
active_id = service.get_active_roadmap_id()
if not active_id:
    # 如果没有活动路线图，选择第一个可用的
    roadmaps = service.list_roadmaps()
    if roadmaps["roadmaps"]:
        active_id = roadmaps["roadmaps"][0]["id"]
        service.set_active_roadmap(active_id)

# 检查路线图状态
status = service.check_roadmap_status(check_type="roadmap", element_id=None, roadmap_id=active_id)
print(f"路线图状态: {status}")

# 更新任务状态
result = service.update_roadmap_status(
    element_id="task-123",
    element_type="task",
    status="completed"
)
if result["success"]:
    print("任务状态已更新")
else:
    print(f"更新失败: {result.get('error')}")
```

### 路线图与工作流集成示例

```python
from src.roadmap import RoadmapService
from src.flow_session import FlowSessionService

roadmap_service = RoadmapService()
flow_service = FlowSessionService()

# 获取任务
task_id = "task-123"
task = roadmap_service.get_task(task_id)

# 创建专注于该任务的工作流会话
workflow_id = "auth-workflow"
session = flow_service.create_session(
    workflow_id=workflow_id,
    name=f"任务执行: {task['title']}",
    task_id=task_id
)

# 获取任务关联的会话
sessions = roadmap_service.get_task_sessions(task_id)
print(f"任务 '{task['title']}' 有 {len(sessions)} 个关联会话")

# 当会话完成时更新任务状态
if session["status"] == "COMPLETED":
    roadmap_service.update_task_status(task_id, "completed")
```

## 状态集成

路线图模块通过 `RoadmapStatus` 与核心的 `Status` 模块集成，提供路线图相关的状态信息。`RoadmapStatusProvider` 实现了 `IStatusProvider` 接口，实现了统一的状态查询和管理。

## 依赖关系

- 数据库服务 (`src.db.service.DatabaseService`)
- 状态服务 (`src.status.service.StatusService`)
- 数据模型 (`src.models.db`)
- GitHub 适配器 (`adapters.github_project`) - 用于GitHub同步
- 工作流会话服务 (`src.flow_session.FlowSessionService`) - 用于任务与工作流集成

## 测试

路线图模块的测试位于 `tests/unit/roadmap/` 目录下。运行测试：

```bash
# (示例命令，具体请参考项目测试配置)
pytest tests/unit/roadmap
```

# 路线图模块

路线图模块提供了完整的路线图管理功能，包括路线图数据的存储、检索、同步和操作。

## 模块结构

该模块采用分层架构，包含以下组件：

```
src/roadmap/
├── core/            # 核心功能
├── service/         # 服务层
│   ├── __init__.py  # 导出RoadmapService
│   ├── roadmap_service.py  # 主服务类
│   ├── roadmap_data.py     # 数据访问和查询功能
│   └── roadmap_operations.py  # 路线图操作功能
├── sync/            # 同步服务
└── examples/        # 示例代码
```

## 组件说明

### 服务层 (service)

服务层是路线图模块的主要接口，提供了统一的路线图管理功能。

- **RoadmapService**: 整合所有路线图功能的主服务类
- **roadmap_data.py**: 提供路线图数据访问和查询相关功能
- **roadmap_operations.py**: 提供路线图的各种操作函数

### 核心层 (core)

核心层提供了路线图的基本功能实现：

- **RoadmapManager**: 路线图管理器
- **RoadmapStatus**: 路线图状态管理
- **RoadmapUpdater**: 路线图更新器

### 同步层 (sync)

同步层提供了路线图与外部系统的同步功能：

- **GitHubSyncService**: GitHub同步服务
- **YamlSyncService**: YAML文件同步服务

## 重构说明

路线图服务已经进行了模块化重构，主要变更如下：

1. 将原本集中在`roadmap_service.py`的功能拆分为三个文件：
   - `roadmap_service.py`: 主服务类，整合其他组件
   - `roadmap_data.py`: 数据访问和查询相关功能
   - `roadmap_operations.py`: 路线图操作相关功能

2. 采用委托模式，将具体功能实现委托给相应的模块，使代码结构更清晰

3. 保持了对外接口的一致性，不影响现有调用代码

这种重构提高了代码的可维护性和可扩展性，同时遵循了单一职责原则。

## 主要功能

- **路线图管理**: 创建、查询、更新和删除路线图
- **Epic管理**: 创建、查询和更新Epic（大型功能）
- **Story管理**: 创建、查询和更新Story（用户故事）
- **Task管理**: 创建、查询和更新Task（具体任务）
- **状态管理**: 更新和同步路线图元素的状态
- **里程碑管理**: 创建和跟踪项目里程碑
- **GitHub同步**: 与GitHub仓库的项目板和议题同步
- **YAML导入/导出**: 支持路线图数据的导入和导出

## API列表

### 路线图管理

- `create_roadmap(name, description, version)`: 创建新的路线图
- `delete_roadmap(roadmap_id)`: 删除路线图
- `get_roadmap(roadmap_id)`: 获取路线图详情
- `get_roadmaps()`: 获取所有路线图
- `set_active_roadmap(roadmap_id)`: 设置活跃路线图
- `switch_roadmap(roadmap_id)`: 切换活跃路线图
- `get_roadmap_info(roadmap_id)`: 获取路线图信息和统计数据

### 数据访问

- `get_epics(roadmap_id)`: 获取路线图下的所有Epic
- `get_stories(roadmap_id)`: 获取路线图下的所有Story
- `get_milestones(roadmap_id)`: 获取路线图下的所有里程碑
- `get_milestone_tasks(milestone_id, roadmap_id)`: 获取里程碑下的所有任务
- `list_tasks(roadmap_id)`: 获取路线图下的所有任务

### 操作和同步

- `update_roadmap_status(element_id, element_type, status, roadmap_id)`: 更新路线图元素状态
- `update_roadmap(roadmap_id)`: 更新路线图数据
- `sync_to_github(roadmap_id)`: 同步路线图到GitHub
- `sync_from_github(roadmap_id)`: 从GitHub同步状态到路线图
- `export_to_yaml(roadmap_id, output_path)`: 导出路线图到YAML文件
- `import_from_yaml(file_path, roadmap_id)`: 从YAML文件导入路线图数据

## 使用示例

### 创建和使用路线图

```python
from src.roadmap import RoadmapService

# 创建路线图服务实例
service = RoadmapService()

# 创建新的路线图
result = service.create_roadmap("项目路线图", "项目开发计划路线图")
roadmap_id = result["roadmap_id"]

# 设置为活跃路线图
service.set_active_roadmap(roadmap_id)

# 获取路线图信息
info = service.get_roadmap_info()
print(f"路线图进度: {info['stats']['progress']}%")
```

### 导出和导入

```python
from src.roadmap import RoadmapService

service = RoadmapService()

# 导出路线图到YAML
service.export_to_yaml(output_path="roadmap_export.yml")

# 导入路线图
service.import_from_yaml("roadmap_export.yml")
```

### GitHub同步

```python
from src.roadmap import RoadmapService

service = RoadmapService()

# 同步路线图到GitHub
service.sync_to_github()

# 从GitHub同步更新
service.sync_from_github()
```

## 依赖关系

路线图模块依赖以下组件：

- 数据库服务 (`src.db.service.DatabaseService`)
- 数据同步器 (`src.db.sync.DataSynchronizer`)
- 数据模型 (`src.models.db`)

## 测试

路线图模块的测试位于 `tests/roadmap/` 目录下，包括：

- 单元测试：测试各个组件的独立功能
- 集成测试：测试组件之间的交互
- 基本导入测试：测试基本导入和环境设置

运行测试：

```bash
# 运行所有路线图测试
python -m tests.roadmap.run_tests

# 运行特定测试文件
python -m tests.roadmap.test_manager

# 运行特定测试类
python -m unittest tests.roadmap.test_manager.TestRoadmapManager

# 运行特定测试方法
python -m unittest tests.roadmap.test_manager.TestRoadmapManager.test_check_roadmap
```

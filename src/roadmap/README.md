# 路线图模块 (Roadmap Module)

路线图模块提供了完整的路线图管理功能，支持路线图的创建、查询、更新和同步。

## 目录结构

```
src/roadmap/
├── core/                 # 核心业务逻辑
│   ├── manager.py        # 路线图管理器
│   ├── status.py         # 状态管理
│   ├── updater.py        # 数据更新
│   └── __init__.py       # 模块初始化
├── service/              # 服务层
│   ├── roadmap_service.py # 路线图服务
│   └── __init__.py       # 模块初始化
├── sync/                 # 同步功能
│   ├── github_sync.py    # GitHub同步
│   ├── yaml_sync.py      # YAML文件同步
│   └── __init__.py       # 模块初始化
└── __init__.py           # 主模块初始化
```

## 主要功能

路线图模块提供以下主要功能：

1. **路线图基础管理**
   - 创建、查询、更新和删除路线图
   - 管理多个路线图，支持切换活跃路线图

2. **状态管理**
   - 检查里程碑和任务状态
   - 更新里程碑和任务状态
   - 计算路线图整体进度

3. **同步功能**
   - 导出路线图到YAML文件
   - 从YAML文件导入路线图
   - 与GitHub项目的同步

## 使用示例

### 创建并使用RoadmapService

```python
from src.roadmap import RoadmapService

# 创建路线图服务实例
service = RoadmapService()

# 创建新路线图
result = service.create_roadmap("产品开发路线图", "产品功能开发计划", "1.0")
roadmap_id = result["roadmap_id"]

# 获取路线图信息
info = service.get_roadmap_info(roadmap_id)

# 检查路线图状态
status = service.check_roadmap_status("roadmap", roadmap_id=roadmap_id)

# 导出到YAML文件
service.export_to_yaml(roadmap_id)
```

### 更新路线图状态

```python
# 更新任务状态
service.update_roadmap_status("task-123", "task", "completed")

# 更新里程碑状态
service.update_roadmap_status("milestone-456", "milestone", "in_progress")
```

### 多路线图管理

```python
# 列出所有路线图
roadmaps = service.list_roadmaps()

# 切换到其他路线图
service.switch_roadmap("roadmap-789")

# 删除路线图
service.delete_roadmap("roadmap-123")
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

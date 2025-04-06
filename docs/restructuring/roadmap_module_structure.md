# 路线图模块重构结构

## 模块概述

路线图模块进行了全面重构，按照职责分离原则拆分为更小、更集中的子模块。这种结构提高了代码的可读性、可维护性和可测试性。

## 目录结构

```
src/roadmap/
├── __init__.py                 # 公共接口
├── core/                       # 核心业务逻辑
│   ├── __init__.py             # 核心模块接口
│   ├── manager.py              # 路线图管理器
│   ├── status.py               # 状态管理
│   └── updater.py              # 数据更新
├── service/                    # 服务层
│   ├── __init__.py             # 服务模块接口
│   └── roadmap_service.py      # 综合服务
└── sync/                       # 同步功能
    ├── __init__.py             # 同步模块接口
    ├── github_sync.py          # GitHub同步
    └── yaml_sync.py            # YAML文件同步
```

## 模块职责

### 核心模块 (`src/roadmap/core/`)

核心模块包含路线图管理的核心业务逻辑：

1. **RoadmapManager** (`manager.py`): 负责路线图整体管理，提供检查路线图状态的功能
2. **RoadmapStatus** (`status.py`): 处理路线图元素状态的更新和管理
3. **RoadmapUpdater** (`updater.py`): 负责路线图数据的更新与维护

### 服务模块 (`src/roadmap/service/`)

服务模块提供高级服务接口，整合核心功能：

1. **RoadmapService** (`roadmap_service.py`): 综合服务，提供完整的路线图管理功能，包括创建、删除、切换、更新路线图，以及与外部系统同步

### 同步模块 (`src/roadmap/sync/`)

同步模块处理与外部系统的数据交换：

1. **GitHubSyncService** (`github_sync.py`): 处理路线图数据与GitHub项目的同步
2. **YamlSyncService** (`yaml_sync.py`): 处理路线图数据与YAML文件的导入导出

## 优点

1. **职责分离**: 每个模块负责特定功能，边界清晰
2. **代码复用**: 核心功能可被多个服务重用
3. **可扩展性**: 可以轻松添加新的同步目标或服务
4. **可测试性**: 更小的组件更容易进行单元测试
5. **文件大小**: 每个文件控制在合理范围内，方便维护

## 使用示例

```python
# 创建路线图服务
from src.roadmap import RoadmapService
service = RoadmapService()

# 创建新路线图
result = service.create_roadmap("项目2023规划", "2023年项目开发路线图")

# 查看路线图状态
status = service.check_roadmap_status()

# 同步到GitHub
github_result = service.sync_to_github()

# 导出到YAML
yaml_result = service.export_to_yaml()
```

## 增强功能

新的结构支持以下增强功能：

1. **多路线图支持**: 可以创建和管理多个路线图，并在它们之间切换
2. **灵活的同步选项**: 支持与GitHub和YAML文件的双向同步
3. **细粒度状态管理**: 可以单独更新和检查任务、里程碑、Epic和故事的状态
4. **完整的CRUD操作**: 为所有路线图元素提供完整的创建、读取、更新和删除功能

## 数据流

整体数据流如下：

1. 用户通过`RoadmapService`接口操作路线图
2. 服务层调用相应的核心组件处理业务逻辑
3. 核心组件与数据库交互，存储或检索数据
4. 同步操作由专门的同步服务处理，确保数据在不同系统间保持一致

# GitHub Roadmap模块重构计划

## 当前问题分析

1. **功能重复**:
   - 路线图处理功能在多个模块中重复实现
   - GitHub同步功能分散在不同模块
   - 多个CLI接口

2. **模块职责不明确**:
   - `adapters/projects`似乎是一个冗余的兼容层
   - `src/roadmap`和`adapters/roadmap_sync`功能重叠

3. **文档不一致**:
   - README描述的功能与实际实现不符

## 重构目标

建立清晰的模块边界和职责分工：

### 1. `adapters/roadmap_sync`

- **主要目的**: YAML <-> Markdown转换和文件同步
- **核心功能**:
  - Markdown解析和生成
  - YAML模式定义和验证
  - 格式之间的双向转换
  - 文件系统操作

### 2. `adapters/github_project`

- **主要目的**: GitHub Projects API集成
- **核心功能**:
  - GitHub API客户端
  - Projects/Issues管理
  - 与GitHub的路线图同步
  - 分析和报告工具

### 3. `src/roadmap`

- **主要目的**: 数据库操作和CLI工具
- **核心功能**:
  - 数据库模型和仓库
  - 路线图管理CLI
  - 模块之间的集成点

## 实施计划

### 阶段1: 具体实施步骤

1. **合并和重构`roadmap_sync`模块**
   - 保留核心Markdown和YAML转换功能
   - 删除重复的GitHub同步代码
   - 更新README准确描述模块功能

2. **增强`github_project`模块**
   - 集中GitHub API集成
   - 将散落在其他模块的GitHub同步功能合并到此
   - 更新文档明确职责

3. **简化`src/roadmap`模块**
   - 删除重复功能
   - 更新CLI以适配新的模块结构
   - 确保向后兼容性

4. **删除`adapters/projects`模块**
   - 将独特功能移至适当模块
   - 创建导入重定向确保现有代码继续工作
   - 更新依赖此模块的代码

### 阶段2: 文件迁移和删除计划

#### 文件迁移

| 源文件 | 目标位置 | 说明 |
|--------|----------|------|
| `adapters/projects/roadmap_generator.py` | `adapters/github_project/roadmap_generator.py` | 移至GitHub集成模块 |
| `adapters/projects/roadmap_processor.py` | `adapters/github_project/roadmap_processor.py` | 移至GitHub集成模块 |
| `adapters/projects/import_roadmap.py` | `adapters/github_project/import_roadmap.py` | 移至GitHub集成模块 |

#### 文件删除

| 文件 | 说明 |
|------|------|
| `adapters/projects/roadmap.py` | 不再需要的兼容层 |
| `adapters/projects/main.py` | 不再需要的入口点 |
| `adapters/roadmap_sync/db_processor.py` | 与`src/roadmap`重复的功能 |

### 阶段3: 测试和文档更新

1. **撰写测试**:
   - 为关键功能编写测试
   - 确保重构后的代码能正确工作

2. **更新文档**:
   - 更新每个模块的README
   - 创建模块间集成指南
   - 记录API变更

3. **创建迁移指南**:
   - 记录API变更
   - 提供从旧结构迁移到新结构的步骤

## 具体文件重构内容

### `adapters/roadmap_sync/README.md`

更新为:

```markdown
# 轻量级Markdown路线图工具

这是一个轻量级的Markdown路线图工具，专注于YAML和Markdown格式的双向转换。

## 核心功能

- **Markdown为中心**：使用Markdown文件作为数据源
- **双向转换**: 支持roadmap.yaml和Markdown故事文件之间的转换
- **命令行接口**：简单的CLI命令用于管理路线图文件
- **最小实现**：专注于文件格式转换

## 主要组件

- **markdown_parser.py**: 从Markdown读取故事数据
- **models.py**: 简单的数据模型
- **cli.py**: 命令行接口
- **converter/**: 提供YAML和Markdown之间的转换功能
  - **yaml_to_markdown.py**: 将roadmap.yaml转换为标准化的stories目录结构
  - **markdown_to_yaml.py**: 将stories目录转换为roadmap.yaml
  - **cli.py**: 转换器命令行工具

## 实现说明

本模块专注于文件格式转换，若需GitHub集成功能，请使用`adapters/github_project`模块。
```

### `adapters/github_project/README.md`

更新为:

```markdown
# GitHub Project 系统

## 简介

这是一个完整的GitHub Projects V2集成系统，提供高级项目管理、分析和路线图同步功能。支持与GitHub Projects的深度集成，包括自定义字段、看板视图和自动化流程。

## 核心功能

- **项目分析**: 自动分析项目进度、质量和风险
- **时间线调整**: 根据实际进度自动调整项目时间线
- **报告生成**: 生成项目状态报告和调整建议
- **路线图同步**: 与GitHub项目的双向同步
- **交互式管理**: 提供命令行和交互式界面管理项目

## 组件说明

- `api/`: GitHub API客户端实现
  - `github_client.py`: 基础API客户端
  - `projects_client.py`: Projects V2专用API客户端
  - `issues_client.py`: Issues API客户端

- `roadmap/`: 路线图管理功能
  - `roadmap_generator.py`: 生成和更新项目路线图
  - `roadmap_processor.py`: 处理路线图数据
  - `import_roadmap.py`: 导入外部路线图数据

- `analysis/`: 项目分析功能

- `manage_project.py`: 交互式项目管理工具
- `cli.py`: 项目分析命令行工具
- `weekly_update.sh`: 项目周报自动分析脚本

## 使用场景

- 适合复杂项目管理
- 需要高级数据分析和可视化
- 使用GitHub Projects V2作为主要项目管理工具
- 需要自动调整和项目预测
```

## 重构后的模块职责

### 1. `adapters/roadmap_sync`

负责纯文件操作和格式转换，不涉及GitHub或数据库操作。

### 2. `adapters/github_project`

负责所有GitHub相关的集成和同步功能，包括路线图同步。

### 3. `src/roadmap`

负责数据库操作和整体CLI，作为连接其他模块的中心点。

## 兼容性维护

为保持向后兼容，将在适当位置添加导入重定向，确保现有代码继续工作。
例如，在删除`adapters/projects`模块后，将创建一个新的`adapters/projects/__init__.py`文件，内容如下:

```python
"""
兼容性导入，重定向到新的模块位置
"""
import warnings

warnings.warn(
    "adapters.projects 模块已被弃用，请使用 adapters.github_project 或 adapters.roadmap_sync",
    DeprecationWarning,
    stacklevel=2
)

# 导入重定向
from adapters.github_project.roadmap_generator import RoadmapGenerator
from adapters.github_project.roadmap_processor import RoadmapProcessor
from adapters.github_project.import_roadmap import ImportRoadmap

__all__ = [
    "RoadmapGenerator",
    "RoadmapProcessor",
    "ImportRoadmap"
]
```

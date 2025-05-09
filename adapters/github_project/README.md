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

### API客户端 (`api/`)

模块化的GitHub API客户端实现，采用了分层设计：

- **基础API客户端**:
  - `github_client.py`: 兼容层，提供基础HTTP请求能力
  - `clients/github_client.py`: 核心实现，处理REST和GraphQL请求

- **项目管理客户端**:
  - `projects_client.py`: 兼容层
  - `clients/projects_client.py`: 项目核心功能
  - `clients/projects_fields.py`: 项目字段操作
  - `clients/projects_items.py`: 项目条目操作

- **Issues管理客户端**:
  - `issues_client.py`: 兼容层
  - `clients/issues_client.py`: 整合型客户端
  - `clients/issues/`: 专业功能子模块
    - `core.py`: 核心Issue操作
    - `comments.py`: 评论管理
    - `labels.py`: 标签管理
    - `milestones.py`: 里程碑管理

### 路线图管理 (`roadmap/`)

- `roadmap_generator.py`: 生成和更新项目路线图
- `roadmap_processor.py`: 处理路线图数据
- `import_roadmap.py`: 导入外部路线图数据

### 项目分析 (`analysis/`)

提供项目数据分析和可视化功能，包括进度分析、质量分析和风险评估。

### 交互工具

- `manage_project.py`: 交互式项目管理工具
- `cli.py`: 项目分析命令行工具
- `weekly_update.sh`: 项目周报自动分析脚本

## 设计原则

- **单一职责**: 每个模块和类只负责一项特定功能
- **模块化**: 功能组件化，可单独使用或组合使用
- **向后兼容**: 保持API稳定性，旧代码可继续使用
- **文件大小**: 遵循每个文件不超过200行的规范
- **错误处理**: 统一的日志记录和异常处理机制

## 使用场景

- 适合复杂项目管理
- 需要高级数据分析和可视化
- 使用GitHub Projects V2作为主要项目管理工具
- 需要自动调整和项目预测

## 快速开始

```python
# 使用整合型Issues客户端
from src.sync import GitHubIssuesClient

client = GitHubIssuesClient()
issues = client.get_issues("owner", "repo", state="open")

# 也可以使用专门的客户端
from src.sync.clients.issues import GitHubIssueLabelsClient

labels_client = GitHubIssueLabelsClient()
labels = labels_client.get_labels("owner", "repo")
```

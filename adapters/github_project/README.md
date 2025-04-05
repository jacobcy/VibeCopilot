# GitHub Project 系统

## 简介

这是一个完整的GitHub Projects V2集成系统，提供高级项目管理、分析和自动调整功能。支持与GitHub Projects的深度集成，包括自定义字段、看板视图和自动化流程。

## 核心功能

- **项目分析**: 自动分析项目进度、质量和风险
- **时间线调整**: 根据实际进度自动调整项目时间线
- **报告生成**: 生成项目状态报告和调整建议
- **交互式管理**: 提供命令行和交互式界面管理项目

## 组件说明

- `api/`: GitHub API客户端实现
  - `github_client.py`: 基础API客户端
  - `projects_client.py`: Projects V2专用API客户端
  - `issues_client.py`: Issues API客户端

- `projects/`: 项目管理核心功能
  - `roadmap_generator.py`: 生成和更新项目路线图
  - `roadmap_processor.py`: 处理路线图数据
  - `import_roadmap.py`: 导入外部路线图数据
  - `analysis/`: 项目分析功能

- `manage_project.py`: 交互式项目管理工具
- `project_cli.py`: 项目分析命令行工具
- `weekly_update.sh`: 项目周报自动分析脚本

## 使用场景

- 适合复杂项目管理
- 需要高级数据分析和可视化
- 使用GitHub Projects V2作为主要项目管理工具
- 需要自动调整和项目预测

## 使用方法

```bash
# 交互式项目管理
python scripts/github_projecct/manage_project.py --interactive

# 项目分析
python scripts/github_projecct/project_cli.py analysis

# 自动周报和调整
bash scripts/github_projecct/weekly_update.sh
```

## 环境配置

需要以下环境变量：

- `GITHUB_TOKEN`: GitHub API授权令牌
- `GITHUB_OWNER`: 仓库所有者
- `GITHUB_REPO`: 仓库名称
- `GITHUB_PROJECT_NUMBER`: GitHub Projects编号

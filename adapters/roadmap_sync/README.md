# 轻量级Markdown路线图工具

这是一个轻量级的Markdown路线图工具，作为特定于VibeCopilot项目的demo实现。它以Markdown文件为主要数据源，并提供与GitHub同步的基本功能。

## 核心功能

- **Markdown为中心**：使用Markdown文件作为数据源
- **GitHub同步**：支持将本地故事同步到GitHub里程碑和Issues
- **命令行接口**：简单的CLI命令用于管理路线图
- **最小实现**：专注于演示概念而非完整功能
- **双向转换**: 支持roadmap.yaml和Markdown故事文件之间的转换

## 主要组件

- **markdown_parser.py**: 从Markdown读取故事数据
- **github_sync.py**: 处理GitHub同步
- **models.py**: 简单的数据模型
- **cli.py**: 命令行接口
- **roadmap_processor.py**: 简化的处理器实现，连接Markdown和GitHub
- **converter/**: 提供YAML和Markdown之间的转换功能
  - **yaml_to_markdown.py**: 将roadmap.yaml转换为标准化的stories目录结构
  - **markdown_to_yaml.py**: 将stories目录转换为roadmap.yaml
  - **cli.py**: 转换器命令行工具

## 实现说明

本模块是一个演示用的简化实现，对于更完整的项目管理功能，建议使用：

1. **直接使用GitHub Projects**：对于复杂项目，推荐使用完整的GitHub Projects功能
2. **使用scripts/github_project模块**：对于需要自动化的复杂集成，可以使用此模块

## 使用示例

### 查看路线图状态

```bash
python -m scripts.roadmap.cli check
```

### 同步到GitHub

```bash
python -m scripts.roadmap.cli sync --push
```

### 将roadmap.yaml转换为Markdown文件

```bash
python -m scripts.roadmap.converter.cli yaml2md --roadmap=.ai/roadmap/current.yaml --output=.ai
```

### 将Markdown文件转换为roadmap.yaml

```bash
python -m scripts.roadmap.converter.cli md2yaml --stories=.ai/stories --output=.ai/roadmap/current.yaml
```

## 文件格式

### 里程碑Markdown示例

```markdown
---
id: M1
type: milestone
title: MVP发布
description: 发布第一个最小可行产品
start_date: 2023-10-01
end_date: 2023-12-31
status: in_progress
progress: 60
---

# MVP发布

这个里程碑的目标是发布第一个最小可行产品...
```

### 故事Markdown示例

```markdown
---
id: S1.1
title: 实现用户认证系统
status: in_progress
progress: 70
epic: Epic-M1
created_at: 2023-12-20
updated_at: 2023-12-25
---

# 实现用户认证系统

## 概述

实现基本的用户认证和登录功能...
```

### 任务Markdown示例

```markdown
---
id: TS1.1.1
title: 实现用户登录
story_id: S1.1
status: in_progress
priority: P1
estimate: 8
assignee: developer
tags: ["M1", "S1.1"]
created_at: 2023-12-20
---

# 实现用户登录

## 任务描述

实现基本的用户认证和登录功能...
```

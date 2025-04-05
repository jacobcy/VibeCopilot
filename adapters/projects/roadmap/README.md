# 路线图模块

为VibeCopilot提供先进的GitHub项目路线图生成、处理和导出功能。此模块通过解析GitHub Projects数据，生成结构化的路线图表示，支持多种输出格式。

## 主要功能

- **路线图生成**：从GitHub Projects数据生成结构化路线图
- **多格式输出**：支持JSON、YAML、Markdown和HTML格式
- **高度定制**：提供多种模板和格式化选项
- **数据验证**：确保路线图数据的完整性和有效性
- **导入/导出**：支持从多种数据源导入，以及导出到不同格式

## 模块组织

模块采用单一职责设计原则，将功能拆分为多个专注的小模块：

- `generator.py`：核心生成器组件，控制路线图生成流程
- `templates.py`：提供预设路线图模板
- `formatters.py`：处理输出格式化逻辑
- `validators.py`：验证路线图数据的有效性
- `converters.py`：不同格式之间的转换
- `markdown_helper.py`：处理Markdown格式的导入和导出
- `data_merger.py`：合并多个路线图数据源

## 使用方法

### 基本使用

```python
from ..api import GitHubProjectsClient
from .roadmap import RoadmapGenerator, get_roadmap_template, format_roadmap_data

# 初始化路线图生成器
client = GitHubProjectsClient()
generator = RoadmapGenerator(client)

# 获取项目数据并生成路线图
project_data = client.get_project_v2("owner", "repo", project_number)
roadmap = generator.generate_roadmap(project_data)

# 应用模板
template = get_roadmap_template("agile")
roadmap = generator.apply_template(roadmap, template)

# 输出为Markdown
markdown = format_roadmap_data(roadmap, "markdown")
```

### 命令行使用

```bash
python -m scripts.github_project.projects.roadmap_cli --owner user --repo repo --project 1 --format markdown,html --output ./docs/roadmap
```

## 数据模型

路线图使用结构化数据模型，主要包含以下组件：

### 路线图（Roadmap）

```json
{
  "title": "项目路线图",
  "description": "项目描述",
  "version": "1.0.0",
  "milestones": [...],
  "tasks": [...]
}
```

### 里程碑（Milestone）

```json
{
  "id": "m1",
  "name": "里程碑名称",
  "description": "里程碑描述",
  "start_date": "2023-01-01",
  "end_date": "2023-03-31",
  "progress": 75,
  "tasks": [...]
}
```

### 任务（Task）

```json
{
  "id": "t1",
  "title": "任务标题",
  "description": "任务描述",
  "status": "in_progress",
  "milestone": "m1",
  "priority": "high",
  "assignees": ["user1", "user2"]
}
```

## 扩展

### 添加新模板

1. 修改`templates.py`文件
2. 在`_ROADMAP_TEMPLATES`字典中添加新模板
3. 确保模板包含必要的里程碑和状态定义

### 添加新输出格式

1. 修改`formatters.py`文件
2. 添加新的格式化函数（如`_generate_xxx`）
3. 在`format_roadmap_data`中注册新格式

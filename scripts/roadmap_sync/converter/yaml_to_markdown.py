"""
YAML转Markdown转换器

提供从roadmap.yaml转换为标准化stories目录结构的功能。
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml


def standardize_id(old_id, type_prefix, milestone=None, story=None):
    """
    标准化ID格式

    Args:
        old_id: 原始ID (例如 T1.1)
        type_prefix: 新ID的类型前缀 (如 'E', 'S', 'TS')
        milestone: 可选的里程碑ID
        story: 可选的故事ID

    Returns:
        str: 标准化后的ID
    """
    if type_prefix == "S":
        # 对于milestone转story的情况，直接保留milestone ID
        if old_id.startswith("M"):
            return old_id

        # 故事ID格式: S1.1, S2.3, ...
        if milestone:
            milestone_num = re.search(r"M(\d+)", milestone).group(1)
            # 如果原始ID已有编号，提取它
            match = re.search(r"(\d+)(?:\.(\d+))?", old_id)
            if match and match.group(2):
                return f"S{milestone_num}.{match.group(2)}"
            # 否则创建新编号
            return f"S{milestone_num}.{old_id.split('.')[-1] if '.' in old_id else '1'}"
        return old_id

    elif type_prefix == "TS":
        # 任务ID格式: TS1.1.1, TS2.3.2, ...
        if milestone and story:
            # 从里程碑提取编号
            if story.startswith("M"):  # 如果story实际上是milestone ID
                milestone_num = re.search(r"M(\d+)", story).group(1)
                # 提取任务编号
                match = re.search(r"T\d+\.(\d+)", old_id)
                task_num = match.group(1) if match else "1"
                return f"TS{milestone_num}.1.{task_num}"
            else:  # 正常情况
                milestone_num = re.search(r"M(\d+)", milestone).group(1)
                story_num = (
                    re.search(r"S\d+\.(\d+)", story).group(1)
                    if re.search(r"S\d+\.(\d+)", story)
                    else "1"
                )

                # 提取任务编号
                match = re.search(r"T\d+\.(\d+)(?:\.(\d+))?", old_id)
                task_num = "1"
                if match:
                    task_num = match.group(2) if match.group(2) else match.group(1)

                return f"TS{milestone_num}.{story_num}.{task_num}"
        return old_id

    # 默认保持原样
    return old_id


def create_story_markdown(story_data, output_dir):
    """
    创建故事的Markdown文件

    Args:
        story_data: 故事数据
        output_dir: 输出目录

    Returns:
        str: 生成的文件路径
    """
    story_id = story_data.get("id", "")
    title = story_data.get("title", "未命名故事")
    description = story_data.get("description", "")
    status = story_data.get("status", "planned")
    progress = story_data.get("progress", 0)
    epic = story_data.get("epic", "")

    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
id: "{story_id}"
title: "{title}"
status: "{status}"
progress: {progress}
"""

    # 只有当epic存在时才添加
    if epic:
        content += f'epic: "{epic}"\n'

    content += f"""created_at: "{today}"
updated_at: "{today}"
---

# {title}

## 概述

{description}

## 详情

该故事包含以下主要内容：

1. **待定部分1** - 状态: 待定
   - 待定子任务1
   - 待定子任务2

2. **待定部分2** - 状态: 待定
   - 待定子任务1
   - 待定子任务2

## 相关任务

- 🚧 任务ID: 待定
  - 🚧 状态: 待定
  - 🚧 进度: 0%

## 关联信息

- 里程碑: {story_id if story_id.startswith('M') else '无'}
- 优先级: {story_data.get('priority', 'P2')}
- 开发者: {', '.join(story_data.get('assignees', ['待定']))}

> 该故事是从roadmap.yaml自动生成的
"""

    # 确保目录存在
    stories_dir = os.path.join(output_dir, "stories")
    os.makedirs(stories_dir, exist_ok=True)

    # 创建文件
    file_path = os.path.join(stories_dir, f"{story_id}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path, story_id


def create_task_markdown(task_data, milestone_id, output_dir):
    """
    创建任务的Markdown文件

    Args:
        task_data: 任务数据
        milestone_id: 里程碑ID，作为故事ID使用
        output_dir: 输出目录

    Returns:
        str: 生成的文件路径
    """
    old_id = task_data.get("id", "")
    # 将milestone_id同时作为story_id传递
    task_id = standardize_id(old_id, "TS", milestone=milestone_id, story=milestone_id)
    title = task_data.get("title", "未命名任务")
    description = task_data.get("description", "")
    status = task_data.get("status", "todo")
    priority = task_data.get("priority", "P2")
    assignees = task_data.get("assignees", [])
    assignee = assignees[0] if assignees else "developer"

    # 收集标签，包括里程碑ID和可能的Epic ID
    tags = [f'"{milestone_id}"']
    if "epic" in task_data:
        tags.append(f'"{task_data["epic"]}"')

    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
id: {task_id}
title: {title}
story_id: {milestone_id}
status: {status}
priority: {priority}
estimate: 8
assignee: {assignee}
tags: [{", ".join(tags)}]
created_at: {today}
---

# {title}

## 任务描述

{description}

## 详细需求

1. 待定需求1
2. 待定需求2
3. 待定需求3

## 技术要点

1. 待定技术点1
2. 待定技术点2
3. 待定技术点3

## 验收标准

1. 待定验收标准1
2. 待定验收标准2
3. 待定验收标准3

## 相关文档

- [相关文档1](#)
- [相关文档2](#)

## 依赖任务

无

## 子任务

1. 待定子任务1
2. 待定子任务2
"""

    # 确保目录存在
    tasks_dir = os.path.join(output_dir, "tasks", task_id)
    os.makedirs(tasks_dir, exist_ok=True)

    # 创建子目录
    os.makedirs(os.path.join(tasks_dir, "test"), exist_ok=True)
    os.makedirs(os.path.join(tasks_dir, "review"), exist_ok=True)
    os.makedirs(os.path.join(tasks_dir, "commit"), exist_ok=True)

    # 创建文件
    file_path = os.path.join(tasks_dir, "task.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def convert_roadmap_to_stories(roadmap_path, output_dir, clear_existing=False):
    """
    将roadmap.yaml转换为标准化的stories和tasks文件结构

    Args:
        roadmap_path: roadmap.yaml文件路径
        output_dir: 输出目录(.ai目录)
        clear_existing: 是否清除现有文件

    Returns:
        dict: 转换统计信息
    """
    # 读取roadmap.yaml
    with open(roadmap_path, "r", encoding="utf-8") as f:
        roadmap_data = yaml.safe_load(f)

    # 如果需要清除现有文件
    if clear_existing:
        for subdir in ["stories", "tasks"]:
            dir_path = os.path.join(output_dir, subdir)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 创建基本目录结构
    for subdir in ["stories", "tasks", "prd", "architecture", "cache", "logs"]:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)

    # 存储统计信息
    stats = {"epics": 0, "stories": 0, "tasks": 0, "milestones": 0}

    # 处理里程碑 - 直接作为Story
    milestones = roadmap_data.get("milestones", [])
    stats["milestones"] = len(milestones)

    # 里程碑ID到Epic映射 (用于后续任务分配)
    milestone_epics = {}

    # 处理每个里程碑
    for milestone in milestones:
        milestone_id = milestone.get("id", "")
        epic_id = milestone.get("epic", "")

        # 将里程碑作为Story处理
        story_data = {
            "id": milestone_id,
            "title": milestone.get("name", "未命名里程碑"),
            "description": milestone.get("description", ""),
            "status": milestone.get("status", "planned"),
            "progress": milestone.get("progress", 0),
            "priority": "P0",  # 里程碑通常具有最高优先级
            "assignees": [],
        }

        # 如果里程碑有epic，则记录
        if epic_id:
            story_data["epic"] = epic_id
            stats["epics"] += 1

        # 创建故事文件
        story_file, story_id = create_story_markdown(story_data, output_dir)
        stats["stories"] += 1

        # 记录里程碑ID
        milestone_epics[milestone_id] = milestone_id

    # 处理任务
    tasks = roadmap_data.get("tasks", [])

    # 为每个任务创建文件
    for task in tasks:
        milestone_id = task.get("milestone", "")
        if milestone_id in milestone_epics:
            # 确保任务有正确的Epic关联
            task_copy = task.copy()  # 创建任务数据的副本，以免修改原始数据

            # 如果任务没有自己的epic标签，但里程碑有关联的epic，则继承里程碑的epic
            if "epic" not in task_copy:
                # 检查该里程碑是否有关联的epic
                for milestone in milestones:
                    if milestone.get("id") == milestone_id and "epic" in milestone:
                        task_copy["epic"] = milestone.get("epic")
                        break

            # 直接在milestone下创建任务
            create_task_markdown(task_copy, milestone_id, output_dir)
            stats["tasks"] += 1

    return stats


def convert_directory_structure(oldpath_pattern, newpath_pattern, directory):
    """
    将旧的目录结构文件转换为新的标准化结构

    Args:
        oldpath_pattern: 旧文件路径模式
        newpath_pattern: 新文件路径模式
        directory: 起始目录
    """
    pass  # 待实现

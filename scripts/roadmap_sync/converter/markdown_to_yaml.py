"""
Markdown转YAML转换器

提供将.ai/stories目录中的Markdown文件转换回roadmap.yaml的功能。
该功能是从现有的markdown_parser.py扩展而来。
"""

import glob
import os
import re
from datetime import datetime
from pathlib import Path

import yaml

from ..markdown_parser import parse_frontmatter, read_all_stories


def read_story_files(stories_dir):
    """
    读取故事目录中的所有文件，并分别识别里程碑、故事和任务

    Args:
        stories_dir: 故事目录路径

    Returns:
        dict: 包含里程碑、故事和任务的字典
    """
    result = {"milestones": [], "tasks": [], "epics": []}

    # 读取stories目录
    story_files = glob.glob(os.path.join(stories_dir, "*.md"))
    for file_path in story_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, _ = parse_frontmatter(content)
            frontmatter["file_path"] = file_path

            # 判断文件类型
            file_id = frontmatter.get("id", "")
            if file_id.startswith("S"):
                result["milestones"].append(frontmatter)
        except Exception as e:
            print(f"读取故事文件 {file_path} 时出错: {e}")

    # 读取tasks目录下的所有task.md文件
    tasks_root = os.path.join(os.path.dirname(stories_dir), "tasks")
    if os.path.exists(tasks_root):
        task_dirs = [
            d for d in os.listdir(tasks_root) if os.path.isdir(os.path.join(tasks_root, d))
        ]
        for task_dir in task_dirs:
            task_file = os.path.join(tasks_root, task_dir, "task.md")
            if os.path.exists(task_file):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    frontmatter, _ = parse_frontmatter(content)
                    frontmatter["file_path"] = task_file
                    result["tasks"].append(frontmatter)
                except Exception as e:
                    print(f"读取任务文件 {task_file} 时出错: {e}")

    # 读取epics目录
    epics_dir = os.path.join(os.path.dirname(stories_dir), "epics")
    if os.path.exists(epics_dir):
        epic_files = glob.glob(os.path.join(epics_dir, "*.md"))
        for file_path in epic_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                frontmatter, _ = parse_frontmatter(content)
                frontmatter["file_path"] = file_path
                result["epics"].append(frontmatter)
            except Exception as e:
                print(f"读取Epic文件 {file_path} 时出错: {e}")

    print(
        f"直接读取: {len(result['milestones'])}个故事, {len(result['tasks'])}个任务, {len(result['epics'])}个Epic"
    )
    return result


def convert_stories_to_roadmap(stories_dir, output_yaml, pretty=True):
    """
    将stories目录中的Markdown文件转换为roadmap.yaml

    Args:
        stories_dir: stories目录路径
        output_yaml: 输出的YAML文件路径
        pretty: 是否美化YAML输出

    Returns:
        dict: 转换后的roadmap数据
    """
    # 直接读取文件，而不使用read_all_stories函数
    data = read_story_files(stories_dir)

    # 构建roadmap结构
    roadmap = {
        "title": "VibeCopilot开发路线图",
        "description": "从Markdown故事生成的VibeCopilot项目路线图",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "milestones": [],
        "tasks": [],
    }

    # 提取里程碑ID映射
    milestone_map = {}
    epic_milestone_map = {}

    # 从故事标题中提取里程碑信息
    for story in data.get("milestones", []):
        story_id = story.get("id", "")
        if story_id.startswith("S"):
            # 从S1.1提取M1
            match = re.match(r"S(\d+)", story_id)
            if match:
                milestone_id = f"M{match.group(1)}"
                milestone_map[story_id] = milestone_id

                # 检查是否有epic信息
                epic_id = story.get("epic", "")
                if epic_id.startswith("Epic-M"):
                    epic_milestone_map[epic_id] = milestone_id

    # 从Epic中提取里程碑信息
    for epic in data.get("epics", []):
        epic_id = epic.get("id", "")
        if epic_id.startswith("Epic-M"):
            milestone_id = epic_id.replace("Epic-", "")
            epic_milestone_map[epic_id] = milestone_id

    # 处理里程碑数据（从Epic生成）
    for epic in data.get("epics", []):
        epic_id = epic.get("id", "")
        if epic_id.startswith("Epic-M"):
            milestone_id = epic_id.replace("Epic-", "")

            roadmap_milestone = {
                "id": milestone_id,
                "name": epic.get("title", "Unknown Milestone"),
                "description": epic.get("description", ""),
                "start_date": epic.get("start_date", ""),
                "end_date": epic.get("end_date", ""),
                "status": epic.get("status", "planned"),
                "progress": epic.get("progress", 0),
            }
            roadmap["milestones"].append(roadmap_milestone)

    # 处理任务数据
    for task in data.get("tasks", []):
        task_id = task.get("id", "")
        story_id = task.get("story_id", "")
        milestone_id = ""

        # 从任务标签中获取里程碑ID
        tags = task.get("tags", [])
        for tag in tags:
            if tag.startswith("M"):
                milestone_id = tag
                break

        # 如果标签中没有，则从故事ID映射获取
        if not milestone_id and story_id in milestone_map:
            milestone_id = milestone_map[story_id]

        # 转换任务ID格式
        if task_id.startswith("TS"):
            # 从TS1.1.1提取为T1.1
            match = re.match(r"TS(\d+)\.(\d+)\.(\d+)", task_id)
            if match:
                milestone_num, story_num, task_num = match.groups()
                task_id = f"T{milestone_num}.{task_num}"

        roadmap_task = {
            "id": task_id,
            "title": task.get("title", ""),
            "description": task.get("description", ""),
            "milestone": milestone_id,
            "status": task.get("status", "todo"),
            "priority": task.get("priority", "P2"),
            "assignees": [task.get("assignee")] if task.get("assignee") else [],
        }
        roadmap["tasks"].append(roadmap_task)

    # 写入YAML文件
    os.makedirs(os.path.dirname(output_yaml), exist_ok=True)
    with open(output_yaml, "w", encoding="utf-8") as f:
        if pretty:
            yaml.dump(roadmap, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            yaml.dump(roadmap, f, allow_unicode=True)

    return roadmap

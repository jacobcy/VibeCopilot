"""
Markdown解析器模块

提供从Markdown文件读取故事数据的功能。
"""

import glob
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析Markdown文件的frontmatter部分

    Args:
        content: Markdown文件内容

    Returns:
        Tuple[Dict[str, Any], str]: (frontmatter字典, 剩余内容)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    try:
        frontmatter_str = match.group(1)
        remaining_content = match.group(2)

        # 解析YAML
        frontmatter = yaml.safe_load(frontmatter_str)
        return frontmatter or {}, remaining_content
    except Exception as e:
        print(f"解析frontmatter时出错: {e}")
        return {}, content


def read_markdown_file(file_path: str) -> Dict[str, Any]:
    """
    读取并解析Markdown文件

    Args:
        file_path: Markdown文件路径

    Returns:
        Dict[str, Any]: 解析后的数据
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析frontmatter
        frontmatter, markdown_content = parse_frontmatter(content)

        # 提取第一个标题作为备用标题
        title_match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        title = title_match.group(1) if title_match else None

        # 如果frontmatter中没有标题，使用提取的标题
        if "title" not in frontmatter and title:
            frontmatter["title"] = title

        # 添加文件路径
        frontmatter["file_path"] = file_path

        return frontmatter

    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return {"file_path": file_path, "error": str(e)}


def read_all_stories(stories_dir: str = None) -> Dict[str, Any]:
    """
    读取所有故事文件

    Args:
        stories_dir: 故事目录路径，默认为.ai/stories

    Returns:
        Dict[str, Any]: 包含里程碑和任务的数据结构
    """
    if stories_dir is None:
        stories_dir = os.path.join(os.getcwd(), ".ai", "stories")

    # 读取所有markdown文件
    md_files = glob.glob(os.path.join(stories_dir, "*.md"))
    stories_data = []

    for file_path in md_files:
        story_data = read_markdown_file(file_path)
        stories_data.append(story_data)

    # 区分里程碑和任务
    milestones = []
    tasks = []
    epics = {}  # 用于存储Epic信息

    # 首先，识别所有Epic
    for story in stories_data:
        if story.get("type") == "epic":
            epic_id = story.get("id")
            if epic_id:
                epics[epic_id] = {
                    "id": epic_id,
                    "name": story.get("title", "未命名Epic"),
                    "description": story.get("description", ""),
                }

    for story in stories_data:
        story_type = story.get("type", "").lower()

        if story_type == "task" or "epic_id" in story:
            # 这是一个任务
            epic_id = story.get("epic_id", "")
            task = {
                "id": story.get("id", ""),
                "title": story.get("title", "未命名任务"),
                "description": story.get("description", ""),
                "milestone": story.get("milestone", story.get("epic_id", "")),  # 支持两种方式指定milestone
                "status": story.get("status", "todo"),
                "priority": story.get("priority", "P2"),
                "assignees": story.get("assignees", []),
                "epic": epic_id,  # 新增epic字段
            }
            tasks.append(task)
        elif story_type == "milestone" or (
            story.get("id") and "epic_id" not in story and story_type != "epic"
        ):
            # 这是一个里程碑
            milestone = {
                "id": story.get("id", ""),
                "name": story.get("title", "未命名里程碑"),
                "description": story.get("description", ""),
                "start_date": story.get("start_date"),
                "end_date": story.get("end_date"),
                "status": story.get("status", "planned"),
                "progress": story.get("progress", 0),
            }
            milestones.append(milestone)

    print(f"从Markdown解析: {len(milestones)}个里程碑, {len(tasks)}个任务, {len(epics)}个Epic")

    return {
        "milestones": milestones,
        "tasks": tasks,
        "epics": list(epics.values()),  # 将Epic信息也作为结果返回
    }


def save_sync_status(sync_results: Dict[str, Any], status_file: str = None) -> None:
    """
    保存同步状态

    Args:
        sync_results: 同步结果
        status_file: 状态文件路径，默认为.ai/github_sync_status.json
    """
    if status_file is None:
        status_file = os.path.join(os.getcwd(), ".ai", "github_sync_status.json")

    # 确保目录存在
    os.makedirs(os.path.dirname(status_file), exist_ok=True)

    # 保存状态
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(sync_results, f, indent=2, ensure_ascii=False)


def load_sync_status(status_file: str = None) -> Dict[str, Any]:
    """
    加载同步状态

    Args:
        status_file: 状态文件路径，默认为.ai/github_sync_status.json

    Returns:
        Dict[str, Any]: 同步状态
    """
    if status_file is None:
        status_file = os.path.join(os.getcwd(), ".ai", "github_sync_status.json")

    if not os.path.exists(status_file):
        return {}

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载同步状态时出错: {e}")
        return {}


if __name__ == "__main__":
    # 简单测试
    data = read_all_stories()
    print(f"找到 {len(data['milestones'])} 个里程碑")
    print(f"找到 {len(data['tasks'])} 个任务")
    print(data)

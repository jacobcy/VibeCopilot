"""
数据库同步模块

提供数据库与文件系统、GitHub之间的同步功能，
确保不同数据源之间的一致性。
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .service import DatabaseService

# 配置日志
logger = logging.getLogger(__name__)


class DataSynchronizer:
    """数据同步器，负责数据库、文件系统和GitHub之间的同步"""

    def __init__(self, db_service: DatabaseService, project_root: Optional[str] = None):
        """
        初始化同步器

        Args:
            db_service: 数据库服务
            project_root: 项目根目录
        """
        self.db = db_service
        self.project_root = project_root or os.environ.get("PROJECT_ROOT", os.getcwd())
        self.ai_dir = os.path.join(self.project_root, ".ai")

    def _ensure_directory(self, directory: str) -> None:
        """确保目录存在"""
        os.makedirs(directory, exist_ok=True)

    # ===== 数据库到文件系统同步 =====

    def sync_task_to_filesystem(self, task_id: str) -> Optional[str]:
        """
        将任务同步到文件系统

        Args:
            task_id: 任务ID

        Returns:
            任务目录路径，如果失败则返回None
        """
        # 获取任务数据
        task_data = self.db.get_task(task_id)
        if not task_data:
            logger.error(f"任务不存在: {task_id}")
            return None

        # 构建任务目录路径
        task_dir = os.path.join(self.ai_dir, "tasks", task_id)
        self._ensure_directory(task_dir)

        # 创建子目录
        for subdir in ["test", "review", "commit"]:
            self._ensure_directory(os.path.join(task_dir, subdir))

        # 创建任务文件
        task_file = os.path.join(task_dir, "task.md")

        # 准备Markdown内容
        content = f"""---
id: {task_data['id']}
title: {task_data['title']}
story_id: {task_data.get('story_id', '')}
status: {task_data['status']}
priority: {task_data['priority']}
estimate: {task_data.get('estimate', 8)}
assignee: {task_data.get('assignee', '')}
tags: {json.dumps(task_data.get('labels', []))}
created_at: {task_data.get('created_at', datetime.now().isoformat())}
---

# {task_data['title']}

## 任务描述

{task_data.get('description', '待补充')}

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

        # 写入文件
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"任务已同步到文件系统: {task_id}")
        return task_dir

    def sync_story_to_filesystem(self, story_id: str) -> Optional[str]:
        """
        将故事同步到文件系统

        Args:
            story_id: 故事ID

        Returns:
            故事文件路径，如果失败则返回None
        """
        # 获取故事数据
        story_data = self.db.get_story(story_id)
        if not story_data:
            logger.error(f"故事不存在: {story_id}")
            return None

        # 构建故事目录路径
        stories_dir = os.path.join(self.ai_dir, "stories")
        self._ensure_directory(stories_dir)

        # 创建故事文件
        story_file = os.path.join(stories_dir, f"{story_id}.md")

        # 准备Markdown内容
        content = f"""---
id: "{story_data['id']}"
title: "{story_data['title']}"
status: "{story_data['status']}"
progress: {story_data['progress']}
"""

        # 如果有epic关联则添加
        if story_data.get("epic_id"):
            content += f'epic: "{story_data["epic_id"]}"\n'

        content += f"""created_at: "{story_data.get('created_at', datetime.now().isoformat())}"
updated_at: "{story_data.get('updated_at', datetime.now().isoformat())}"
---

# {story_data['title']}

## 概述

{story_data.get('description', '待补充')}

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
- 开发者:

> 该故事是从数据库自动生成的
"""

        # 写入文件
        with open(story_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"故事已同步到文件系统: {story_id}")
        return story_file

    def sync_all_to_filesystem(self) -> Tuple[int, int]:
        """
        将所有数据同步到文件系统

        Returns:
            同步的故事和任务数量
        """
        # 获取所有故事和任务
        stories = self.db.list_stories()
        tasks = self.db.list_tasks()

        # 同步故事
        story_count = 0
        for story in stories:
            story_id = story["id"]
            if self.sync_story_to_filesystem(story_id):
                story_count += 1

        # 同步任务
        task_count = 0
        for task in tasks:
            task_id = task["id"]
            if self.sync_task_to_filesystem(task_id):
                task_count += 1

        logger.info(f"所有数据已同步到文件系统: {story_count}个故事, {task_count}个任务")
        return story_count, task_count

    def sync_to_roadmap_yaml(self, output_path: Optional[str] = None) -> str:
        """
        将数据库数据同步到roadmap.yaml

        Args:
            output_path: 输出路径，默认为.ai/roadmap/current.yaml

        Returns:
            生成的YAML文件路径
        """
        # 导出数据
        roadmap_data = self.db.export_to_yaml()

        # 默认输出路径
        if not output_path:
            output_path = os.path.join(self.ai_dir, "roadmap", "current.yaml")

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 写入YAML文件
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(roadmap_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"数据已同步到YAML: {output_path}")
        return output_path

    # ===== 文件系统到数据库同步 =====

    def sync_from_roadmap_yaml(self, yaml_path: Optional[str] = None) -> Tuple[int, int, int]:
        """
        从roadmap.yaml同步数据到数据库

        Args:
            yaml_path: YAML文件路径，默认为.ai/roadmap/current.yaml

        Returns:
            导入的Epic、Story和Task数量
        """
        # 默认YAML路径
        if not yaml_path:
            yaml_path = os.path.join(self.ai_dir, "roadmap", "current.yaml")

        # 检查文件是否存在
        if not os.path.exists(yaml_path):
            logger.error(f"YAML文件不存在: {yaml_path}")
            return 0, 0, 0

        # 读取YAML文件
        with open(yaml_path, "r", encoding="utf-8") as f:
            roadmap_data = yaml.safe_load(f)

        # 导入数据
        result = self.db.import_from_yaml(roadmap_data)

        logger.info(f"从YAML导入数据完成: {result[0]}个Epic, {result[1]}个Story, {result[2]}个Task")
        return result

    def sync_task_from_filesystem(self, task_dir: str) -> Optional[str]:
        """
        从文件系统同步任务到数据库

        Args:
            task_dir: 任务目录

        Returns:
            任务ID，如果失败则返回None
        """
        # 构建任务文件路径
        task_file = os.path.join(task_dir, "task.md")

        # 检查文件是否存在
        if not os.path.exists(task_file):
            logger.error(f"任务文件不存在: {task_file}")
            return None

        # 读取任务文件
        with open(task_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析YAML前言
        try:
            # 查找YAML前言
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index > 0:
                    yaml_content = content[3:end_index].strip()
                    metadata = yaml.safe_load(yaml_content)

                    # 提取描述
                    description = ""
                    header_index = content.find("# ", end_index)
                    if header_index > 0:
                        description_index = content.find("## 任务描述", header_index)
                        if description_index > 0:
                            next_section = content.find("##", description_index + 12)
                            if next_section > 0:
                                description = content[description_index + 12 : next_section].strip()
                            else:
                                description = content[description_index + 12 :].strip()

                    # 准备任务数据
                    task_data = {
                        "id": metadata.get("id", ""),
                        "title": metadata.get("title", ""),
                        "description": description,
                        "story_id": metadata.get("story_id", ""),
                        "status": metadata.get("status", "todo"),
                        "priority": metadata.get("priority", "P2"),
                        "estimate": metadata.get("estimate", 8),
                        "assignee": metadata.get("assignee", ""),
                    }

                    # 提取标签
                    labels = metadata.get("tags", [])

                    # 创建或更新任务
                    if self.db.get_task(task_data["id"]):
                        self.db.update_task(task_data["id"], task_data, labels)
                    else:
                        self.db.create_task(task_data, labels)

                    logger.info(f"从文件系统同步任务完成: {task_data['id']}")
                    return task_data["id"]
        except Exception as e:
            logger.error(f"解析任务文件失败: {e}")

        return None

    def sync_story_from_filesystem(self, story_file: str) -> Optional[str]:
        """
        从文件系统同步故事到数据库

        Args:
            story_file: 故事文件路径

        Returns:
            故事ID，如果失败则返回None
        """
        # 检查文件是否存在
        if not os.path.exists(story_file):
            logger.error(f"故事文件不存在: {story_file}")
            return None

        # 读取故事文件
        with open(story_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析YAML前言
        try:
            # 查找YAML前言
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index > 0:
                    yaml_content = content[3:end_index].strip()
                    metadata = yaml.safe_load(yaml_content)

                    # 提取描述
                    description = ""
                    header_index = content.find("# ", end_index)
                    if header_index > 0:
                        description_index = content.find("## 概述", header_index)
                        if description_index > 0:
                            next_section = content.find("##", description_index + 8)
                            if next_section > 0:
                                description = content[description_index + 8 : next_section].strip()
                            else:
                                description = content[description_index + 8 :].strip()

                    # 准备故事数据
                    story_data = {
                        "id": metadata.get("id", "").strip('"'),
                        "title": metadata.get("title", "").strip('"'),
                        "description": description,
                        "status": metadata.get("status", "planned").strip('"'),
                        "progress": metadata.get("progress", 0),
                        "epic_id": metadata.get("epic", "").strip('"'),
                        "created_at": metadata.get("created_at", datetime.now().isoformat()).strip(
                            '"'
                        ),
                        "updated_at": metadata.get("updated_at", datetime.now().isoformat()).strip(
                            '"'
                        ),
                    }

                    # 创建或更新故事
                    if self.db.get_story(story_data["id"]):
                        self.db.update_story(story_data["id"], story_data)
                    else:
                        self.db.create_story(story_data)

                    logger.info(f"从文件系统同步故事完成: {story_data['id']}")
                    return story_data["id"]
        except Exception as e:
            logger.error(f"解析故事文件失败: {e}")

        return None

    def sync_all_from_filesystem(self) -> Tuple[int, int]:
        """
        从文件系统同步所有数据到数据库

        Returns:
            同步的故事和任务数量
        """
        # 同步故事
        stories_dir = os.path.join(self.ai_dir, "stories")
        story_count = 0
        if os.path.exists(stories_dir):
            for file_name in os.listdir(stories_dir):
                if file_name.endswith(".md"):
                    story_file = os.path.join(stories_dir, file_name)
                    if self.sync_story_from_filesystem(story_file):
                        story_count += 1

        # 同步任务
        tasks_dir = os.path.join(self.ai_dir, "tasks")
        task_count = 0
        if os.path.exists(tasks_dir):
            for dir_name in os.listdir(tasks_dir):
                task_dir = os.path.join(tasks_dir, dir_name)
                if os.path.isdir(task_dir):
                    if self.sync_task_from_filesystem(task_dir):
                        task_count += 1

        logger.info(f"从文件系统同步数据完成: {story_count}个故事, {task_count}个任务")
        return story_count, task_count

    # ===== GitHub同步 =====

    def sync_to_github(self) -> Dict[str, Any]:
        """
        同步数据到GitHub

        调用现有的GitHub同步脚本。
        这里仅作为接口，实际实现需要集成现有GitHub处理逻辑。

        Returns:
            同步结果
        """
        # 先同步到YAML
        yaml_path = self.sync_to_roadmap_yaml()

        # TODO: 调用GitHub同步逻辑
        # 这里需要集成现有的GitHub同步脚本

        result = {
            "success": True,
            "message": "数据已同步到GitHub",
            "yaml_path": yaml_path,
            "created": 0,
            "updated": 0,
        }

        logger.info(f"数据同步到GitHub: {result}")
        return result

    def sync_from_github(self) -> Dict[str, Any]:
        """
        从GitHub同步数据

        调用现有的GitHub同步脚本。
        这里仅作为接口，实际实现需要集成现有GitHub处理逻辑。

        Returns:
            同步结果
        """
        # TODO: 调用GitHub同步逻辑
        # 这里需要集成现有的GitHub同步脚本

        # 同步完成后，从YAML导入数据库
        yaml_path = os.path.join(self.ai_dir, "roadmap", "current.yaml")
        epic_count, story_count, task_count = self.sync_from_roadmap_yaml(yaml_path)

        result = {
            "success": True,
            "message": "从GitHub同步数据完成",
            "yaml_path": yaml_path,
            "epics": epic_count,
            "stories": story_count,
            "tasks": task_count,
        }

        logger.info(f"从GitHub同步数据: {result}")
        return result

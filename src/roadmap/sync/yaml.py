"""
YAML同步服务模块

提供路线图与YAML文件的同步功能。
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class YamlSyncService:
    """YAML同步服务，处理路线图数据与YAML文件的同步"""

    def __init__(self, db_service: DatabaseService):
        """
        初始化YAML同步服务

        Args:
            db_service: 数据库服务
        """
        self.db_service = db_service

        # 确保工作目录存在
        self.work_dir = os.path.expanduser(os.environ.get("VIBE_WORK_DIR", "~/vibe_work"))
        os.makedirs(self.work_dir, exist_ok=True)

    def export_to_yaml(
        self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将路线图导出到YAML文件

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图
            output_path: 输出文件路径，不提供则使用默认路径

        Returns:
            Dict[str, Any]: 导出结果
        """
        roadmap_id = roadmap_id or self.db_service.active_roadmap_id

        # 获取路线图数据
        roadmap = self.db_service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 确定输出路径
        if not output_path:
            roadmap_name = roadmap.get("name", "unknown").lower().replace(" ", "_")
            output_path = os.path.join(self.work_dir, f"roadmap_{roadmap_name}.yaml")

        # 获取完整路线图数据
        data = self._prepare_roadmap_data(roadmap_id)

        try:
            # 导出到YAML文件
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            logger.info(f"路线图已导出到: {output_path}")
            return {
                "success": True,
                "roadmap_id": roadmap_id,
                "roadmap_name": roadmap.get("name"),
                "file_path": output_path,
            }
        except Exception as e:
            logger.exception(f"导出YAML时出错: {str(e)}")
            return {"success": False, "error": f"导出错误: {str(e)}", "roadmap_id": roadmap_id}

    def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从YAML文件导入路线图数据

        Args:
            file_path: YAML文件路径
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 导入结果
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}

        try:
            # 读取YAML文件
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return {"success": False, "error": "YAML文件内容为空"}

            # 导入数据到数据库
            result = self._import_roadmap_data(data, roadmap_id)

            return {
                "success": True,
                "roadmap_id": result.get("roadmap_id"),
                "roadmap_name": result.get("roadmap_name"),
                "file_path": file_path,
                "stats": {
                    "epics": result.get("epics_count", 0),
                    "milestones": result.get("milestones_count", 0),
                    "stories": result.get("stories_count", 0),
                    "tasks": result.get("tasks_count", 0),
                },
            }
        except Exception as e:
            logger.exception(f"导入YAML时出错: {str(e)}")
            return {"success": False, "error": f"导入错误: {str(e)}"}

    def _prepare_roadmap_data(self, roadmap_id: str) -> Dict[str, Any]:
        """
        准备路线图数据用于导出

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 路线图数据
        """
        # 获取路线图基本信息
        roadmap = self.db_service.get_roadmap(roadmap_id)
        if not roadmap:
            raise ValueError(f"未找到路线图: {roadmap_id}")

        # 获取路线图的组成部分
        epics = self.db_service.get_epics(roadmap_id)
        milestones = self.db_service.get_milestones(roadmap_id)
        stories = self.db_service.get_stories(roadmap_id)
        tasks = []

        # 获取所有任务
        for milestone in milestones:
            milestone_tasks = self.db_service.get_milestone_tasks(milestone.get("id"), roadmap_id)
            tasks.extend(milestone_tasks)

        # 构建YAML结构
        data = {
            "roadmap": {
                "id": roadmap.get("id"),
                "name": roadmap.get("name"),
                "description": roadmap.get("description", ""),
                "version": roadmap.get("version", "1.0"),
                "last_updated": datetime.now().isoformat(),
                "author": roadmap.get("author", "VibeCopilot"),
            },
            "epics": epics,
            "milestones": milestones,
            "stories": stories,
            "tasks": tasks,
        }

        return data

    def _import_roadmap_data(
        self, data: Dict[str, Any], roadmap_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导入路线图数据到数据库

        Args:
            data: YAML数据
            roadmap_id: 路线图ID，不提供则创建新路线图

        Returns:
            Dict[str, Any]: 导入结果
        """
        roadmap_data = data.get("roadmap", {})

        # 确定路线图ID
        if roadmap_id:
            # 更新现有路线图
            roadmap = self.db_service.get_roadmap(roadmap_id)
            if not roadmap:
                raise ValueError(f"未找到路线图: {roadmap_id}")

            # 更新路线图信息
            roadmap_data["id"] = roadmap_id
            self.db_service.update_roadmap(roadmap_id, roadmap_data)
            logger.info(f"更新路线图: {roadmap_id}")
        else:
            # 创建新路线图
            roadmap_id = roadmap_data.get("id") or self.db_service.generate_id()
            roadmap_data["id"] = roadmap_id
            self.db_service.create_roadmap(roadmap_data)
            logger.info(f"创建路线图: {roadmap_id}")

        # 清空现有数据
        self._clear_roadmap_data(roadmap_id)

        # 导入数据
        epics = data.get("epics", [])
        milestones = data.get("milestones", [])
        stories = data.get("stories", [])
        tasks = data.get("tasks", [])

        # 导入Epics
        for epic in epics:
            epic["roadmap_id"] = roadmap_id
            self.db_service.create_epic(epic, roadmap_id)

        # 导入里程碑
        for milestone in milestones:
            milestone["roadmap_id"] = roadmap_id
            self.db_service.create_milestone(milestone, roadmap_id)

        # 导入故事
        for story in stories:
            story["roadmap_id"] = roadmap_id
            self.db_service.create_story(story, roadmap_id)

        # 导入任务
        for task in tasks:
            task["roadmap_id"] = roadmap_id
            self.db_service.create_task(task, roadmap_id)

        logger.info(
            f"导入路线图数据完成: {roadmap_id}, Epics: {len(epics)}, 里程碑: {len(milestones)}, 故事: {len(stories)}, 任务: {len(tasks)}"
        )

        return {
            "roadmap_id": roadmap_id,
            "roadmap_name": roadmap_data.get("name"),
            "epics_count": len(epics),
            "milestones_count": len(milestones),
            "stories_count": len(stories),
            "tasks_count": len(tasks),
        }

    def _clear_roadmap_data(self, roadmap_id: str) -> None:
        """
        清空路线图现有数据

        Args:
            roadmap_id: 路线图ID
        """
        logger.info(f"清空路线图数据: {roadmap_id}")

        # 获取现有数据
        tasks = []
        milestones = self.db_service.get_milestones(roadmap_id)

        # 获取所有任务
        for milestone in milestones:
            milestone_tasks = self.db_service.get_milestone_tasks(milestone.get("id"), roadmap_id)
            tasks.extend(milestone_tasks)

        # 删除任务
        for task in tasks:
            self.db_service.delete_task(task.get("id"), roadmap_id)

        # 删除里程碑
        for milestone in milestones:
            self.db_service.delete_milestone(milestone.get("id"), roadmap_id)

        # 删除故事
        stories = self.db_service.get_stories(roadmap_id)
        for story in stories:
            self.db_service.delete_story(story.get("id"), roadmap_id)

        # 删除Epics
        epics = self.db_service.get_epics(roadmap_id)
        for epic in epics:
            self.db_service.delete_epic(epic.get("id"), roadmap_id)

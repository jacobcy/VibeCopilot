"""
路线图服务模块

提供路线图管理的高级服务接口，整合核心功能和同步能力。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository, TaskRepository
from src.roadmap.core import RoadmapManager, RoadmapStatus, RoadmapUpdater
from src.roadmap.sync import GitHubSyncService, YamlSyncService

logger = logging.getLogger(__name__)


class RoadmapService:
    """
    路线图服务，提供完整的路线图管理功能

    整合了核心功能和同步能力，为外部系统提供统一接口
    """

    def __init__(self, session: Optional[Session] = None):
        """
        初始化路线图服务

        Args:
            session: 数据库会话，默认创建内存数据库会话
        """
        # 初始化数据库会话
        if session is None:
            engine = create_engine("sqlite:///:memory:")
            SessionFactory = sessionmaker(bind=engine)
            session = SessionFactory()

        self.session = session
        self._active_roadmap_id = None

        # 初始化仓库
        self.epic_repo = EpicRepository(session)
        self.story_repo = StoryRepository(session)
        self.task_repo = TaskRepository(session)

        # 初始化同步服务
        self.github_sync = GitHubSyncService(self)
        self.yaml_sync = YamlSyncService(self)

        # 初始化核心组件
        self.manager = RoadmapManager(self)
        self.status = RoadmapStatus(self)
        self.updater = RoadmapUpdater(self)

    @property
    def active_roadmap_id(self) -> Optional[str]:
        """获取当前活跃的路线图ID"""
        return self._active_roadmap_id

    def set_active_roadmap(self, roadmap_id: str) -> None:
        """设置当前活跃的路线图

        Args:
            roadmap_id: 路线图ID
        """
        # 验证路线图存在
        if self.get_roadmap(roadmap_id):
            self._active_roadmap_id = roadmap_id
            logger.info(f"设置活跃路线图: {roadmap_id}")
        else:
            logger.error(f"路线图不存在: {roadmap_id}")
            raise ValueError(f"路线图不存在: {roadmap_id}")

    def create_roadmap(
        self, name: str, description: str = "", version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        创建新的路线图

        Args:
            name: 路线图名称
            description: 路线图描述
            version: 路线图版本

        Returns:
            Dict[str, Any]: 创建结果
        """
        # 简化实现 - 返回模拟数据
        roadmap_id = f"roadmap-{name.lower().replace(' ', '-')}"
        self._active_roadmap_id = roadmap_id

        logger.info(f"创建路线图: {name} (ID: {roadmap_id})")
        return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": name}

    def get_roadmap(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """获取路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Optional[Dict[str, Any]]: 路线图数据
        """
        # 简化实现 - 返回模拟数据
        return {"id": roadmap_id, "name": "示例路线图", "description": "这是一个示例路线图", "version": "1.0"}

    def switch_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """
        切换当前活跃路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 切换结果
        """
        # 检查路线图是否存在
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 设置活跃路线图
        self.set_active_roadmap(roadmap_id)

        logger.info(f"切换到路线图: {roadmap.get('name')} (ID: {roadmap_id})")
        return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap.get("name")}

    def get_roadmaps(self) -> List[Dict[str, Any]]:
        """获取所有路线图

        Returns:
            List[Dict[str, Any]]: 路线图列表
        """
        # 简化实现 - 返回模拟数据
        return [
            {"id": "roadmap-123", "name": "示例路线图1", "description": "这是示例路线图1", "version": "1.0"},
            {"id": "roadmap-456", "name": "示例路线图2", "description": "这是示例路线图2", "version": "1.0"},
        ]

    def list_roadmaps(self) -> Dict[str, Any]:
        """
        列出所有路线图

        Returns:
            Dict[str, Any]: 路线图列表结果
        """
        roadmaps = self.get_roadmaps()
        active_id = self.active_roadmap_id

        return {"success": True, "active_id": active_id, "roadmaps": roadmaps}

    def delete_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """
        删除路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 删除结果
        """
        # 检查路线图是否存在
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 检查是否是活跃路线图
        active_id = self.active_roadmap_id
        if roadmap_id == active_id:
            return {"success": False, "error": "不能删除当前活跃路线图，请先切换到其他路线图"}

        # 删除路线图及其所有内容 - 这里简化实现
        roadmap_name = roadmap.get("name")

        logger.info(f"删除路线图: {roadmap_name} (ID: {roadmap_id})")
        return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}

    def get_epics(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取路线图下的所有Epic

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            List[Dict[str, Any]]: Epic列表
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        epics = self.epic_repo.filter(roadmap_id=roadmap_id)
        return [self._object_to_dict(epic) for epic in epics]

    def get_stories(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取路线图下的所有Story

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            List[Dict[str, Any]]: Story列表
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        stories = self.story_repo.filter(roadmap_id=roadmap_id)
        return [self._object_to_dict(story) for story in stories]

    def get_milestones(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取路线图下的所有Milestone

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            List[Dict[str, Any]]: Milestone列表
        """
        # 简化实现 - 返回模拟数据
        return [
            {
                "id": "milestone-123",
                "name": "里程碑1",
                "description": "这是里程碑1",
                "status": "in_progress",
                "progress": 50,
                "roadmap_id": roadmap_id or self.active_roadmap_id,
            },
            {
                "id": "milestone-456",
                "name": "里程碑2",
                "description": "这是里程碑2",
                "status": "planned",
                "progress": 0,
                "roadmap_id": roadmap_id or self.active_roadmap_id,
            },
        ]

    def get_milestone_tasks(
        self, milestone_id: str, roadmap_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取里程碑下的所有任务

        Args:
            milestone_id: 里程碑ID
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        # 简化实现 - 返回模拟数据
        return [
            {"id": f"task-{milestone_id}-1", "name": "任务1", "status": "completed"},
            {"id": f"task-{milestone_id}-2", "name": "任务2", "status": "in_progress"},
        ]

    def list_tasks(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取路线图下的所有任务

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        tasks = self.task_repo.filter(roadmap_id=roadmap_id)
        return [self._object_to_dict(task) for task in tasks]

    def _object_to_dict(self, obj) -> Dict[str, Any]:
        """将对象转换为字典

        Args:
            obj: 数据对象

        Returns:
            Dict[str, Any]: 字典表示
        """
        if hasattr(obj, "__dict__"):
            return {key: value for key, value in obj.__dict__.items() if not key.startswith("_")}
        return {}

    def get_roadmap_info(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取路线图信息

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 路线图信息
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 获取路线图基本信息
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 获取统计信息
        epics = self.get_epics(roadmap_id)
        milestones = self.get_milestones(roadmap_id)
        stories = self.get_stories(roadmap_id)

        tasks_count = 0
        completed_tasks = 0
        for milestone in milestones:
            milestone_tasks = self.get_milestone_tasks(milestone.get("id"), roadmap_id)
            tasks_count += len(milestone_tasks)
            completed_tasks += sum(
                1 for task in milestone_tasks if task.get("status") == "completed"
            )

        # 计算整体进度
        progress = 0.0
        if tasks_count > 0:
            progress = completed_tasks / tasks_count * 100

        # 获取状态信息
        status_info = self.manager.check_roadmap("roadmap", roadmap_id=roadmap_id)

        return {
            "success": True,
            "roadmap": roadmap,
            "stats": {
                "epics_count": len(epics),
                "milestones_count": len(milestones),
                "stories_count": len(stories),
                "tasks_count": tasks_count,
                "completed_tasks": completed_tasks,
                "progress": progress,
            },
            "status": status_info,
        }

    def update_roadmap_status(
        self,
        element_id: str,
        element_type: str = "task",
        status: Optional[str] = None,
        roadmap_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新路线图元素状态

        Args:
            element_id: 元素ID
            element_type: 元素类型
            status: 新状态
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 更新结果
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 更新状态
        result = self.status.update_element(element_id, element_type, status, roadmap_id)

        return {"success": result.get("updated", False), "element": result}

    def check_roadmap_status(
        self,
        check_type: str = "entire",
        element_id: Optional[str] = None,
        roadmap_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        检查路线图状态

        Args:
            check_type: 检查类型，可选值：entire, milestone, task
            element_id: 元素ID，仅当check_type为milestone或task时需要
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 状态信息
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 检查状态
        result = self.manager.check_roadmap(check_type, element_id, roadmap_id)

        return {
            "success": True,
            "check_type": check_type,
            "roadmap_id": roadmap_id,
            "status": result,
        }

    def update_roadmap(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        更新路线图数据

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 更新结果
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 更新路线图
        result = self.updater.update_roadmap(roadmap_id)

        return result

    def sync_to_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        同步路线图到GitHub

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 同步到GitHub
        result = self.github_sync.sync_roadmap_to_github(roadmap_id)

        return result

    def sync_from_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从GitHub同步状态到路线图

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 从GitHub同步
        result = self.github_sync.sync_status_from_github(roadmap_id)

        return result

    def export_to_yaml(
        self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导出路线图到YAML文件

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图
            output_path: 输出文件路径，不提供则使用默认路径

        Returns:
            Dict[str, Any]: 导出结果
        """
        roadmap_id = roadmap_id or self.active_roadmap_id

        # 导出到YAML
        result = self.yaml_sync.export_to_yaml(roadmap_id, output_path)

        return result

    def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从YAML文件导入路线图数据

        Args:
            file_path: YAML文件路径
            roadmap_id: 路线图ID，不提供则创建新路线图

        Returns:
            Dict[str, Any]: 导入结果
        """
        # 导入YAML
        result = self.yaml_sync.import_from_yaml(file_path, roadmap_id)

        return result

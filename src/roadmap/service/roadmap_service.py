"""
路线图服务模块

提供路线图管理的高级服务接口，整合核心功能和同步能力。
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository, TaskRepository
from src.roadmap.core import RoadmapManager, RoadmapStatus, RoadmapUpdater
from src.roadmap.service.roadmap_data import (
    get_epics,
    get_milestone_tasks,
    get_milestones,
    get_roadmap,
    get_roadmap_info,
    get_roadmaps,
    get_stories,
    list_tasks,
)
from src.roadmap.service.roadmap_operations import (
    create_roadmap,
    delete_roadmap,
    export_to_yaml,
    import_from_yaml,
    sync_from_github,
    sync_to_github,
    update_roadmap,
    update_roadmap_status,
)
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
        if get_roadmap(self, roadmap_id):
            self._active_roadmap_id = roadmap_id
            logger.info(f"设置活跃路线图: {roadmap_id}")
        else:
            logger.error(f"路线图不存在: {roadmap_id}")
            raise ValueError(f"路线图不存在: {roadmap_id}")

    def switch_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """
        切换当前活跃路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 切换结果
        """
        # 检查路线图是否存在
        roadmap = get_roadmap(self, roadmap_id)
        if not roadmap:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 设置活跃路线图
        self.set_active_roadmap(roadmap_id)

        logger.info(f"切换到路线图: {roadmap.get('name')} (ID: {roadmap_id})")
        return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap.get("name")}

    def list_roadmaps(self) -> Dict[str, Any]:
        """
        列出所有路线图

        Returns:
            Dict[str, Any]: 路线图列表结果
        """
        roadmaps = get_roadmaps(self)
        active_id = self.active_roadmap_id

        return {"success": True, "active_id": active_id, "roadmaps": roadmaps}

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

    # 数据操作方法，委托给roadmap_data模块
    get_roadmap = get_roadmap
    get_roadmaps = get_roadmaps
    get_epics = get_epics
    get_stories = get_stories
    get_milestones = get_milestones
    get_milestone_tasks = get_milestone_tasks
    list_tasks = list_tasks
    get_roadmap_info = get_roadmap_info

    # 操作方法，委托给roadmap_operations模块
    create_roadmap = create_roadmap
    delete_roadmap = delete_roadmap
    update_roadmap_status = update_roadmap_status
    update_roadmap = update_roadmap
    sync_to_github = sync_to_github
    sync_from_github = sync_from_github
    export_to_yaml = export_to_yaml
    import_from_yaml = import_from_yaml

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

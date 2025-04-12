"""
路线图服务模块

提供路线图管理的高级服务接口，整合核心功能和同步能力。
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db import get_session_factory
from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.system_config_repository import SystemConfigRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db import Epic, Milestone, Roadmap, Story, SystemConfig, Task
from src.parsing.processors.roadmap_processor import RoadmapProcessor
from src.roadmap.core import RoadmapManager, RoadmapStatus, RoadmapUpdater
from src.roadmap.service.roadmap_data import (
    get_epics,
    get_milestone_tasks,
    get_milestones,
    get_roadmap,
    get_roadmap_info,
    get_roadmaps,
    get_stories,
    get_tasks,
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

# 移除循环导入
# from src.roadmap.sync import GitHubSyncService, YamlSyncService

logger = logging.getLogger(__name__)


class RoadmapService:
    """
    路线图服务，提供完整的路线图管理功能

    整合了核心功能和同步能力，为外部系统提供统一接口
    """

    def __init__(self):
        """初始化路线图服务"""
        # 使用全局会话工厂
        self.session_factory = get_session_factory()
        self._active_roadmap_id = None

        # 从数据库加载活动路线图ID
        with self.session_factory() as session:
            self.config_repo = SystemConfigRepository(session)
            config = self.config_repo.get_by_key("active_roadmap_id")
            if config and config.value:
                # 验证路线图存在
                roadmap_repo = RoadmapRepository(session)
                roadmap = roadmap_repo.get_by_id(config.value)
                if roadmap:
                    self._active_roadmap_id = config.value
                    logger.info(f"从数据库加载活动路线图ID: {config.value}")
                else:
                    logger.warning(f"数据库中的活动路线图ID {config.value} 不存在，将清除")
                    # 删除无效的配置
                    self.config_repo.delete_config("active_roadmap_id")

        # 使用懒加载模式初始化其他组件
        self._github_sync = None
        self._yaml_sync = None
        self._manager = None
        self._status = None
        self._updater = None

    @property
    def active_roadmap_id(self) -> Optional[str]:
        """获取当前活跃的路线图ID"""
        return self._active_roadmap_id

    # 使用属性懒加载其他组件
    @property
    def github_sync(self):
        """获取GitHub同步服务（懒加载）"""
        if self._github_sync is None:
            # 延迟导入，避免循环依赖
            from src.roadmap.sync import GitHubSyncService

            self._github_sync = GitHubSyncService(self)
        return self._github_sync

    @property
    def yaml_sync(self):
        """获取YAML同步服务（懒加载）"""
        if self._yaml_sync is None:
            # 延迟导入，避免循环依赖
            from src.roadmap.sync import YamlSyncService

            self._yaml_sync = YamlSyncService(self)
        return self._yaml_sync

    @property
    def manager(self):
        """获取路线图管理器（懒加载）"""
        if self._manager is None:
            from src.roadmap.core import RoadmapManager

            self._manager = RoadmapManager(self)
        return self._manager

    @property
    def status(self):
        """获取路线图状态管理器（懒加载）"""
        if self._status is None:
            from src.roadmap.core import RoadmapStatus

            self._status = RoadmapStatus(self)
        return self._status

    @property
    def updater(self):
        """获取路线图更新器（懒加载）"""
        if self._updater is None:
            from src.roadmap.core import RoadmapUpdater

            self._updater = RoadmapUpdater(self)
        return self._updater

    def set_active_roadmap(self, roadmap_id: str) -> bool:
        """设置当前活跃的路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            bool: 操作是否成功
        """
        try:
            with self.session_factory() as session:
                # 验证路线图存在
                roadmap_repo = RoadmapRepository(session)
                roadmap = roadmap_repo.get_by_id(roadmap_id)
                if not roadmap:
                    logger.error(f"路线图不存在: {roadmap_id}")
                    return False

                # 更新内存中的活动路线图ID
                self._active_roadmap_id = roadmap_id

                # 更新或创建系统配置记录
                config_repo = SystemConfigRepository(session)
                config_repo.set_value(key="active_roadmap_id", value=str(roadmap_id), description="当前活动的路线图ID")

                # 确保提交事务
                session.commit()

                logger.info(f"设置活跃路线图并持久化: {roadmap_id}")
                return True

        except Exception as e:
            logger.error(f"设置活动路线图失败: {e}")
            return False

    def switch_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """
        切换当前活跃路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 切换结果
        """
        try:
            # 检查路线图是否存在
            roadmap = get_roadmap(self, roadmap_id)
            if not roadmap:
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

            # 调用set_active_roadmap持久化设置
            success = self.set_active_roadmap(roadmap_id)
            if not success:
                return {"success": False, "error": f"切换路线图失败: {roadmap_id}"}

            # 优先使用title字段，然后是name字段
            roadmap_name = roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"
            logger.info(f"切换到路线图: {roadmap_name} (ID: {roadmap_id})")
            return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}

        except Exception as e:
            logger.error(f"切换路线图出错: {e}")
            return {"success": False, "error": f"切换路线图出错: {str(e)}"}

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
    get_tasks = get_tasks
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

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """将对象转换为字典

        Args:
            obj: 要转换的对象

        Returns:
            Dict[str, Any]: 转换后的字典
        """
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__table__"):
            # SQLAlchemy模型
            result = {}
            for column in obj.__table__.columns:
                result[column.name] = getattr(obj, column.name)
            return result
        else:
            # 尝试使用vars()
            return vars(obj)

    def get_now(self) -> str:
        """获取当前时间（ISO格式）

        Returns:
            str: ISO格式的当前时间字符串
        """
        from datetime import datetime

        return datetime.now().isoformat()

    def list_elements(
        self,
        type: str = "all",
        status: str = "all",
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        sort_by: str = "id",
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """列出路线图元素

        Args:
            type: 元素类型，可选 'all', 'milestone', 'story', 'task'
            status: 筛选状态
            assignee: 筛选指派人
            labels: 筛选标签列表
            sort_by: 排序字段
            sort_desc: 是否降序排序
            page: 页码
            page_size: 每页数量

        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            # 获取活动路线图
            roadmap_id = self.active_roadmap_id
            if not roadmap_id:
                return {"success": False, "message": "未设置活动路线图", "data": [], "total": 0}

            # 根据类型获取元素
            elements = []
            if type == "all" or type == "milestone":
                # 使用数据层方法获取里程碑
                milestones = self.milestone_repo.get_by_roadmap_id(roadmap_id)
                for milestone in milestones:
                    if status != "all" and milestone.status != status:
                        continue
                    elements.append(
                        {
                            "id": milestone.id,
                            "type": "milestone",
                            "name": milestone.title,  # 使用title作为name，与前端显示一致
                            "title": milestone.title,
                            "status": milestone.status,
                            "priority": "normal",
                            "assignee": "",
                            "labels": [],
                        }
                    )

            if type == "all" or type == "story":
                # 使用数据层方法获取故事
                stories = self.story_repo.get_by_roadmap_id(roadmap_id)
                for story in stories:
                    if status != "all" and story.status != status:
                        continue
                    if assignee and story.assignee != assignee:
                        continue
                    story_labels = story.labels.split(",") if story.labels else []
                    if labels and not any(label in story_labels for label in labels):
                        continue
                    elements.append(
                        {
                            "id": story.id,
                            "type": "story",
                            "name": story.title,  # 使用title作为name，与前端显示一致
                            "title": story.title,
                            "status": story.status,
                            "priority": story.priority,
                            "assignee": story.assignee,
                            "labels": story_labels,
                        }
                    )

            if type == "all" or type == "task":
                # 使用数据层方法获取任务
                tasks = self.task_repo.get_by_roadmap_id(roadmap_id)
                for task in tasks:
                    if status != "all" and task.status != status:
                        continue
                    if assignee and task.assignee != assignee:
                        continue
                    task_labels = (
                        task.labels
                        if isinstance(task.labels, list)
                        else task.labels.split(",")
                        if isinstance(task.labels, str) and task.labels
                        else []
                    )
                    if labels and not any(label in task_labels for label in labels):
                        continue
                    elements.append(
                        {
                            "id": task.id,
                            "type": "task",
                            "name": task.title,  # 使用title作为name，与前端显示一致
                            "title": task.title,
                            "status": task.status,
                            "priority": task.priority,
                            "assignee": task.assignee,
                            "labels": task_labels,
                        }
                    )

            # 排序
            if sort_by in ["id", "title", "status", "priority"]:
                elements.sort(key=lambda x: x.get(sort_by, ""), reverse=sort_desc)

            # 分页
            total = len(elements)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_elements = elements[start_idx:end_idx]

            return {"success": True, "data": paged_elements, "total": total}

        except Exception as e:
            logger.exception(f"获取元素列表时出错: {e}")
            return {"success": False, "message": f"获取元素列表失败: {str(e)}", "data": [], "total": 0}

    async def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """从YAML文件导入路线图

        Args:
            file_path: YAML文件路径
            roadmap_id: 可选的路线图ID，不提供则创建新路线图
            verbose: 是否显示详细信息

        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            # 创建处理器
            processor = RoadmapProcessor()

            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析路线图内容
            data = await processor.parse_roadmap(content)

            if not data:
                return {"success": False, "error": "解析路线图内容失败"}

            field_warnings = []
            # 检查并记录字段类型问题
            for field in ["title", "description", "status"]:
                if field in data and isinstance(data[field], dict):
                    field_warnings.append(f"字段'{field}'期望字符串类型，实际收到字典类型: {data[field]}")

            # 如果提供了roadmap_id，更新现有路线图
            if roadmap_id:
                # 检查路线图是否存在
                roadmap = self.roadmap_repo.get_by_id(roadmap_id)
                if not roadmap:
                    return {"success": False, "error": f"路线图不存在: {roadmap_id}"}

                # 更新路线图
                try:
                    self.update_roadmap(roadmap_id, data)
                    return {"success": True, "roadmap_id": roadmap_id, "field_warnings": field_warnings}
                except Exception as e:
                    return {"success": False, "error": f"更新路线图失败: {str(e)}"}

            # 创建新路线图
            try:
                new_roadmap_id = self.create_roadmap(data)
                if not new_roadmap_id:
                    return {"success": False, "error": "创建路线图失败：未返回ID"}
                return {"success": True, "roadmap_id": new_roadmap_id, "field_warnings": field_warnings}
            except Exception as e:
                return {"success": False, "error": f"创建路线图失败: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fix_yaml_file(self, file_path: str, output_path: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """修复YAML文件格式

        Args:
            file_path: YAML文件路径
            output_path: 可选的输出文件路径
            verbose: 是否显示详细信息

        Returns:
            Dict[str, Any]: 修复结果
        """
        try:
            # 创建处理器
            processor = RoadmapProcessor()

            # 调用处理器的fix_file方法
            success, result = await processor.fix_file(file_path, output_path)

            if success:
                return {"success": True, "fixed_path": result, "message": f"文件已修复并保存到: {result}"}
            else:
                return {"success": False, "error": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_roadmap(self, data: Dict[str, Any]) -> Optional[str]:
        """创建新的路线图

        Args:
            data: 路线图数据

        Returns:
            Optional[str]: 路线图ID，失败则返回None
        """
        with self.session_factory() as session:
            try:
                roadmap_repo = RoadmapRepository(session)
                roadmap = Roadmap(
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    version=data.get("version", "1.0"),
                    status=data.get("status", "active"),
                    created_at=self.get_now(),
                    updated_at=self.get_now(),
                )
                session.add(roadmap)
                session.commit()
                return str(roadmap.id)
            except Exception as e:
                logger.error(f"创建路线图失败: {e}")
                session.rollback()
                return None

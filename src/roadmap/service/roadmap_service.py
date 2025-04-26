"""
路线图服务模块

提供路线图管理的高级服务接口，整合核心功能和同步能力。
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
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
from src.validation.roadmap_validation import RoadmapValidator

# 移除循环导入
# from src.roadmap.sync import GitHubSyncService, YamlSyncService

logger = logging.getLogger(__name__)


class RoadmapService:
    """
    路线图服务，提供完整的路线图管理功能

    整合了核心功能和同步能力，为外部系统提供统一接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化路线图服务"""
        self.config = config or get_config()
        self.github_token = self.config.get("adapters", {}).get("github", {}).get("token")
        # 移除冗余的 github_client 初始化，让 GitHubSyncService 自己处理
        # self.github_client = Github(self.github_token) if self.github_token else None

        # 初始化仓库 (无状态)
        self.roadmap_repo = RoadmapRepository()
        self.epic_repo = EpicRepository()
        self.milestone_repo = MilestoneRepository()
        self.story_repo = StoryRepository()
        # 添加 TaskRepository 初始化
        self.task_repo = TaskRepository()
        # 初始化验证器
        self.validator = RoadmapValidator()

        # 在 __init__ 内部导入并实例化 Status Provider
        from src.status.providers.roadmap_provider import RoadmapStatusProvider

        self.status_provider = RoadmapStatusProvider()
        self.status_provider.set_service(self)
        logger.info("RoadmapService 初始化完成，并已注入到 RoadmapStatusProvider。")

        # 使用懒加载模式初始化其他组件
        self._github_sync = None
        self._yaml_sync = None
        self._manager = None
        self._status = None
        self._updater = None

    @property
    def active_roadmap_id(self) -> Optional[str]:
        """获取当前活动的路线图ID (通过 Status Provider)"""
        # 从 status_provider 获取活动 ID
        return self.status_provider.get_active_roadmap_id()

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

    def set_active_roadmap(self, roadmap_id: Optional[str]) -> bool:
        """设置活动路线图ID (通过 Status Provider)

        Args:
            roadmap_id: 路线图ID，或None来清除

        Returns:
            bool: 操作是否成功
        """
        # 直接委托给 Status Provider 处理持久化和验证
        success = self.status_provider.set_active_roadmap_id(roadmap_id)
        if success:
            logger.info(f"通过 Status Provider 设置活动路线图 ID: {roadmap_id}")
        else:
            logger.error(f"通过 Status Provider 设置活动路线图 ID 失败: {roadmap_id}")
        return success

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
            roadmap_dict = get_roadmap(self, roadmap_id)
            if not roadmap_dict:
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

            # 调用set_active_roadmap持久化设置
            success = self.set_active_roadmap(roadmap_id)
            if not success:
                return {"success": False, "error": f"切换路线图失败: {roadmap_id}"}

            # 优先使用title字段，然后是name字段
            roadmap_name = roadmap_dict.get("title") or roadmap_dict.get("name") or "[未命名路线图]"
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
        roadmap_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        检查路线图状态 (现在直接处理或委托给 provider/repo)
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图"}

        # TODO: Implement status checking logic here or delegate
        # Example: Fetch data using self.get_roadmap_info(roadmap_id)
        #          Calculate health based on stats/progress from repos
        logger.warning("RoadmapService.check_roadmap_status 需要重新实现，不再依赖 RoadmapManager")
        # Placeholder implementation:
        roadmap_info = self.get_roadmap_info(roadmap_id)
        if not roadmap_info.get("success"):
            return roadmap_info  # Return error from get_roadmap_info

        # Basic status based on roadmap info
        return {
            "success": True,
            "check_type": check_type,  # Keep the requested type
            "roadmap_id": roadmap_id,
            "status": roadmap_info.get("stats", {}),  # Return stats as basic status for now
            "message": "状态检查逻辑需要进一步实现",
        }

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
                from src.db.session_manager import session_scope

                milestones = []
                with session_scope() as session:
                    milestones = self.milestone_repo.get_by_roadmap_id(session, roadmap_id)
                for milestone in milestones:
                    # 使用字符串值比较而不是直接比较Column对象
                    milestone_status = str(milestone.status) if milestone.status is not None else ""
                    if status != "all" and milestone_status != status:
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
                from src.db.session_manager import session_scope

                stories = []
                with session_scope() as session:
                    stories = self.story_repo.get_by_roadmap_id(session, roadmap_id)
                for story in stories:
                    # 使用字符串值比较而不是直接比较Column对象
                    story_status = str(story.status) if story.status is not None else ""
                    if status != "all" and story_status != status:
                        continue
                    story_assignee = str(story.assignee) if story.assignee is not None else ""
                    if assignee and story_assignee != assignee:
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
                from src.db.session_manager import session_scope

                tasks = []
                with session_scope() as session:
                    tasks = self.task_repo.get_by_roadmap_id(session, roadmap_id)
                for task in tasks:
                    # 使用字符串值比较而不是直接比较Column对象
                    task_status = str(task.status) if task.status is not None else ""
                    if status != "all" and task_status != status:
                        continue
                    task_assignee = str(task.assignee) if task.assignee is not None else ""
                    if assignee and task_assignee != assignee:
                        continue

                    # 安全处理标签
                    task_labels_value = task.labels
                    if isinstance(task_labels_value, list):
                        task_labels = task_labels_value
                    else:
                        task_labels_str = str(task_labels_value) if task_labels_value is not None else ""
                        task_labels = task_labels_str.split(",") if task_labels_str else []
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

    async def import_from_yaml(
        self, file_path: str, roadmap_id: Optional[str] = None, activate: bool = False, verbose: bool = False
    ) -> Dict[str, Any]:
        """从YAML文件导入路线图

        Args:
            file_path: YAML文件路径
            roadmap_id: 可选的路线图ID，不提供则创建新路线图
            activate: 导入后是否设为活动路线图
            verbose: 是否显示详细信息

        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            # Lazy load import_service
            from ..sync.import_service import RoadmapImportService

            import_service = RoadmapImportService(self)

            # Call the async method using await, remove force_llm
            result = await import_service.import_from_yaml(file_path, roadmap_id, verbose)  # <-- Remove force_llm

            # Handle activation if import was successful and activate=True
            if result.get("success") and activate:
                imported_id = result.get("roadmap_id")
                if imported_id:
                    if self.set_active_roadmap(imported_id):
                        result["activated"] = True
                        logger.info(f"导入成功后已激活路线图: {imported_id}")
                    else:
                        result["activated"] = False
                        result["warning"] = result.get("warning", "") + "导入成功，但激活失败。"
                        logger.warning(f"导入成功，但激活路线图 {imported_id} 失败")
                else:
                    result["activated"] = False
                    result["warning"] = result.get("warning", "") + "导入成功但未返回ID，无法激活。"
                    logger.warning("导入成功但未返回路线图ID，无法激活")
            elif "activated" not in result:  # Ensure 'activated' key exists
                result["activated"] = False

            return result

        except Exception as e:
            logger.error(f"调用 YAML 导入服务时出错: {e}", exc_info=True)
            return {"success": False, "error": f"导入时发生内部错误: {e}"}

    # 删除重复的 delete_roadmap_operation 方法，保留下面的实现

    # 移除 export_to_yaml_operation 方法，直接使用 export_to_yaml 方法

    # Add similar wrapper methods for sync_to_github, sync_from_github if needed
    # Or the CLI handlers can import directly from roadmap_operations.py

    # Remove the internal create_roadmap and update_roadmap if they were defined here previously

    def get_roadmap(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """获取指定路线图详情"""
        return get_roadmap(self, roadmap_id)

    def get_roadmaps(self) -> List[Dict[str, Any]]:
        """获取所有路线图列表"""
        return get_roadmaps(self)

    def get_epics(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取史诗列表"""
        return get_epics(self, roadmap_id)

    def get_milestones(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取里程碑列表"""
        return get_milestones(self, roadmap_id)

    def get_stories(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取故事列表"""
        return get_stories(self, roadmap_id)

    def get_tasks(self, roadmap_id: Optional[str] = None, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取任务列表"""
        return get_tasks(self, roadmap_id, milestone_id)

    def get_milestone_tasks(self, milestone_id: str, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取里程碑任务（如果模型支持）"""
        return get_milestone_tasks(self, milestone_id, roadmap_id)

    def get_roadmap_info(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """获取路线图详细信息和统计"""
        return get_roadmap_info(self, roadmap_id)

    # --- Sync Operations --- #

    def sync_to_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """将路线图同步到GitHub"""
        return self.github_sync.sync_roadmap_to_github(roadmap_id)

    def sync_status_from_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """从GitHub同步状态"""
        return self.github_sync.sync_status_from_github(roadmap_id)

    def sync_from_github(self, repo_name: str, branch: str = "main", theme: Optional[str] = None, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """从GitHub仓库导入"""
        return self.github_sync.sync_from_github(repo_name, branch, theme, roadmap_id)

    def export_to_yaml(self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """导出路线图到YAML"""
        return self.yaml_sync.export_to_yaml(roadmap_id, output_path)

    # --- Operation Passthrough --- #
    # These methods call functions from roadmap_operations.py

    def delete_roadmap_operation(self, roadmap_id: str) -> Dict[str, Any]:
        from . import roadmap_operations  # Lazy import

        return roadmap_operations.delete_roadmap(self, roadmap_id)

    # 其他操作方法可以根据需要添加

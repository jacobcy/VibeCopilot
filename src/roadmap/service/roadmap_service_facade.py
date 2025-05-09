"""
路线图服务门面模块

提供路线图管理的统一门面接口，整合各个子模块功能。
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope
from src.roadmap.service.github_link_operations import find_roadmap_by_github_link, link_roadmap_to_github_project
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
from src.roadmap.service.roadmap_operations import delete_roadmap, list_roadmap_elements, switch_active_roadmap
from src.roadmap.service.service_connector import set_roadmap_service
from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)


class RoadmapServiceFacade:
    """
    路线图服务门面，提供完整的路线图管理功能

    整合了核心功能和同步能力，为外部系统提供统一接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化路线图服务门面"""
        self.config = config or get_config()
        self.github_token = self.config.get("github.api_token")
        self.logger = logging.getLogger(__name__)

        self.roadmap_repo = RoadmapRepository()
        self.epic_repo = EpicRepository()
        self.milestone_repo = MilestoneRepository()
        self.story_repo = StoryRepository()
        self.task_repo = TaskRepository()
        self.validator = RoadmapValidator()

        self.status_provider = None
        self._github_sync = None
        self._yaml_sync = None

        set_roadmap_service(self)
        logger.info("RoadmapServiceFacade已注册到服务连接器. 等待 StatusService 完成连接。")

    @property
    def active_roadmap_id(self) -> Optional[str]:
        """获取当前活动的路线图ID (通过 Status Provider)"""
        if not self.status_provider:
            logger.warning("RoadmapServiceFacade: status_provider 未设置，无法获取 active_roadmap_id")
            # 尝试连接
            from src.roadmap.service.service_connector import connect_services

            connect_services()
            if not self.status_provider:
                return None  # 尝试后仍未设置
        return self.status_provider.get_active_roadmap_id()

    # 使用属性懒加载其他组件
    @property
    def github_sync(self):
        """获取GitHub同步服务（懒加载）"""
        if self._github_sync is None:
            # 延迟导入，避免循环依赖
            from src.sync import GitHubSyncService

            self._github_sync = GitHubSyncService(self)
        return self._github_sync

    @property
    def yaml_sync(self):
        """获取YAML同步服务（懒加载）"""
        if self._yaml_sync is None:
            # 延迟导入，避免循环依赖
            from src.sync import YamlSyncService

            self._yaml_sync = YamlSyncService(self)
        return self._yaml_sync

    def set_active_roadmap(self, roadmap_id: Optional[str]) -> bool:
        """设置活动路线图ID (通过 Status Provider)

        Args:
            roadmap_id: 路线图ID，或None来清除

        Returns:
            bool: 操作是否成功
        """
        if not self.status_provider:
            logger.error("set_active_roadmap: status_provider 未设置。请确保 StatusService 已正确初始化并连接。")
            return False

        # 先获取StatusService中的ProjectState
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            project_state = status_service.project_state

            # 设置当前活动路线图ID前，检查此roadmap_id是否已有关联的GitHub项目配置
            if roadmap_id:
                github_project_id = project_state.get_github_project_id_for_roadmap(roadmap_id)
                logger.info(f"为路线图ID {roadmap_id} 查询关联的GitHub项目: {github_project_id}")

                # 如果找到关联的GitHub项目ID
                if github_project_id:
                    # 尝试查询此GitHub项目的更多信息（如owner, repo）
                    # 先检查GitHub信息提供者
                    github_info = {}
                    try:
                        github_provider = status_service.provider_manager.get_provider("github_info")
                        if github_provider:
                            github_status = github_provider.get_status()
                            if github_status.get("source") != "default":
                                github_info = {
                                    "project_id": github_project_id,
                                    # project_title 可以在这里考虑从 github_status 获取，如果可用
                                    # 例如: "project_title": github_status.get("effective_project_title", "")
                                }
                    except Exception as e:
                        logger.warning(f"获取GitHub信息时出错: {e}")

                    # 构建GitHub配置
                    github_config = {
                        "project_id": github_project_id,
                        # project_title 可以在这里考虑从 github_status 获取，如果可用
                        # 例如: "project_title": github_status.get("effective_project_title", "")
                    }

                    # 更新活动路线图的后端配置
                    # 注意：ProjectState的set_active_roadmap_backend_config期望一个完整的配置字典
                    # 我们需要确保 ProjectState.set_active_roadmap_backend_config 接受这种只包含部分key（如project_id）的配置
                    # 或者在这里构造一个期望的完整结构，但只填充 project_id 和 project_title
                    # current_backend_configs = project_state.get_active_roadmap_backend_config()
                    # if not isinstance(current_backend_configs, dict): current_backend_configs = {}
                    # current_backend_configs["github"] = github_config
                    # project_state.set_active_roadmap_backend_config(current_backend_configs)

                    # 修正：直接设置，ProjectState内部处理保存结构
                    # 我们需要确保 project_state.set_active_roadmap_backend_config 能够正确处理
                    # 传入的 config 只包含部分键值对的情况，或者它期望的是一个包含 'github' 键的完整结构。
                    # 从 project_state.py 的 set_active_roadmap_backend_config 定义来看，它直接替换整个对象。
                    # 因此，我们需要传递一个包含 'github' 键的结构，或者修改 ProjectState 的方法。
                    # 暂时维持传递只包含 project_id 的字典，后续根据 ProjectState 的行为调整。
                    # 假设 project_state.set_active_roadmap_backend_config 被调整为接受 { "github": { "project_id": ... } }
                    # 或者更简单地，我们只更新 github 部分。

                    final_config_to_set = project_state.get_active_roadmap_backend_config()
                    if not isinstance(final_config_to_set, dict):
                        final_config_to_set = {}
                    final_config_to_set["github"] = github_config  # 只更新 github 部分

                    project_state.set_active_roadmap_backend_config(final_config_to_set)
                    logger.info(f"已更新活动路线图的GitHub后端配置(仅含project_id): {final_config_to_set}")
                else:
                    # 未找到GitHub项目配置，清除当前后端配置
                    # project_state.set_active_roadmap_backend_config({})
                    # 清除时也应只清除github部分或确保传递空字典能被正确处理
                    final_config_to_set = project_state.get_active_roadmap_backend_config()
                    if not isinstance(final_config_to_set, dict):
                        final_config_to_set = {}
                    if "github" in final_config_to_set:  # 确保 github key 存在才删除
                        del final_config_to_set["github"]
                    # 或者 final_config_to_set["github"] = {} # 设置为空字典
                    project_state.set_active_roadmap_backend_config(final_config_to_set)

                    logger.info(f"未找到路线图ID {roadmap_id} 关联的GitHub项目，已清除/重置GitHub后端配置: {final_config_to_set}")

        except Exception as e:
            logger.error(f"处理GitHub项目关联时出错: {e}", exc_info=True)

        # 通过StatusProvider设置活动路线图ID
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
        return switch_active_roadmap(self, roadmap_id)

    def list_roadmaps(self) -> Dict[str, Any]:
        """
        列出所有路线图

        Returns:
            Dict[str, Any]: 路线图列表结果
        """
        roadmaps = get_roadmaps()
        active_id = self.active_roadmap_id

        return {"success": True, "active_id": active_id, "roadmaps": roadmaps}

    def check_roadmap_status(self, check_type: str = "roadmap", roadmap_id: Optional[str] = None, element_id: Optional[str] = None) -> Dict[str, Any]:
        """
        检查路线图状态 (现在直接处理或委托给 provider/repo)
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图"}

        # 获取路线图信息
        roadmap_info = self.get_roadmap_info(roadmap_id)
        if not roadmap_info.get("success"):
            return roadmap_info  # 返回get_roadmap_info的错误

        # 确保返回包含基本的路线图信息
        roadmap_data = roadmap_info.get("roadmap", {})

        # 构建状态数据
        status_data = {
            "id": roadmap_id,
            "name": roadmap_data.get("name") or roadmap_data.get("title", "未命名路线图"),
            "description": roadmap_data.get("description", "无描述"),
            "stats": roadmap_info.get("stats", {}),
            "progress": roadmap_info.get("stats", {}).get("progress", 0),
            "active": True,
            "github_link": roadmap_data.get("github_link", None),
        }

        # 返回完整响应
        return {"success": True, "check_type": check_type, "roadmap_id": roadmap_id, "status": status_data}

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
        """获取当前时间ISO格式字符串"""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_or_create_implicit_story_for_milestone(
        self, session, local_milestone_id: str, local_milestone_title: str, local_roadmap_id: str
    ) -> Optional[str]:
        """
        为给定的本地里程碑获取或创建一个隐式的Story。
        这个隐式的Story将作为该里程碑下直接任务的容器。

        Args:
            session: SQLAlchemy 会话对象
            local_milestone_id: 本地里程碑ID
            local_milestone_title: 本地里程碑标题
            local_roadmap_id: 本地路线图ID

        Returns:
            Optional[str]: 隐式Story的ID，如果创建失败则返回None
        """
        # 1. 定义隐式Story的标题
        implicit_story_title = f"[隐式] {local_milestone_title} 下的任务"

        # 2. 尝试查找已存在的隐式Story
        existing_story = self.story_repo.get_by_title_and_roadmap_id(session, implicit_story_title, local_roadmap_id)

        if existing_story:
            logger.info(f"找到里程碑 '{local_milestone_title}' 的已存在的隐式Story: '{implicit_story_title}' (ID: {existing_story.id})")
            return existing_story.id

        # 3. 如果不存在，则创建新的隐式Story
        try:
            story_data = {
                "title": implicit_story_title,
                "description": f"为里程碑 '{local_milestone_title}' (ID: {local_milestone_id}) 自动生成的任务容器。",
                "status": "planned",  # 默认状态
                "priority": "medium",  # 默认优先级
                "is_implicit": True,  # 标记为隐式Story
                "created_at": str(self.get_now()),
                "updated_at": str(self.get_now()),
            }

            # 找到一个关联到该路线图的Epic，用于关联Story
            # 注意：如果需要特定的Epic，这里的逻辑需要调整
            epics = self.epic_repo.get_by_roadmap_id(session, local_roadmap_id)
            if epics:
                # 使用第一个Epic (简化处理)
                story_data["epic_id"] = epics[0].id
                logger.info(f"将隐式Story关联到Epic: {epics[0].title} (ID: {epics[0].id})")
            else:
                # 如果没有Epic，创建一个默认Epic作为隐式Story的容器
                default_epic_title = f"[隐式] {local_roadmap_id} 里程碑任务容器"
                existing_epic = self.epic_repo.get_by_title_and_roadmap_id(session, default_epic_title, local_roadmap_id)

                if existing_epic:
                    story_data["epic_id"] = existing_epic.id
                    logger.info(f"使用现有默认Epic作为隐式Story容器: {default_epic_title} (ID: {existing_epic.id})")
                else:
                    # 创建默认Epic
                    epic_data = {
                        "title": default_epic_title,
                        "description": f"为路线图 {local_roadmap_id} 自动生成的里程碑任务容器",
                        "status": "planned",
                        "roadmap_id": local_roadmap_id,
                        "created_at": str(self.get_now()),
                        "updated_at": str(self.get_now()),
                    }
                    created_epic = self.epic_repo.create(session, **epic_data)
                    if created_epic and hasattr(created_epic, "id"):
                        story_data["epic_id"] = created_epic.id
                        logger.info(f"创建默认Epic作为隐式Story容器: {default_epic_title} (ID: {created_epic.id})")
                    else:
                        logger.error(f"创建默认Epic失败，隐式Story将不关联Epic")

            # 创建Story
            created_story = self.story_repo.create(session, **story_data)
            if created_story and hasattr(created_story, "id"):
                logger.info(f"为里程碑 '{local_milestone_title}' 创建了新的隐式Story: '{implicit_story_title}' (ID: {created_story.id})")
                return created_story.id
            else:
                logger.error(f"为里程碑 '{local_milestone_title}' 创建隐式Story '{implicit_story_title}' 失败，仓库未返回有效对象。")
                return None

        except Exception as e:
            logger.error(f"为里程碑 '{local_milestone_title}' 创建隐式Story '{implicit_story_title}' 时出错: {e}", exc_info=True)
            return None

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
        """列出路线图元素 (调用 operations)

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
        return list_roadmap_elements(
            service=self,
            type=type,
            status=status,
            assignee=assignee,
            labels=labels,
            sort_by=sort_by,
            sort_desc=sort_desc,
            page=page,
            page_size=page_size,
        )

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
            # 直接调用yaml_sync的方法
            result = await self.yaml_sync.import_from_yaml(file_path, roadmap_id, verbose)

            # 如果导入成功且需要激活
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
            elif "activated" not in result:  # 确保'activated'字段存在
                result["activated"] = False

            return result

        except Exception as e:
            logger.error(f"调用 YAML 导入服务时出错: {e}", exc_info=True)
            return {"success": False, "error": f"导入时发生内部错误: {e}"}

    def delete_roadmap_operation(self, roadmap_id: str) -> Dict[str, Any]:
        """删除路线图 (调用 operations)

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 操作结果
        """
        return delete_roadmap(self, roadmap_id)

    def get_roadmap(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """获取单个路线图的详细信息"""
        return get_roadmap(roadmap_id)

    def get_roadmaps(self) -> List[Dict[str, Any]]:
        """获取所有路线图的列表"""
        return get_roadmaps()

    def get_epics(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取特定路线图或所有的史诗列表"""
        epics = get_epics(roadmap_id)

        # 添加本地显示编号
        if epics:
            # 按ID顺序对epics进行排序以保证编号一致性
            epics = sorted(epics, key=lambda x: x.get("id", ""))
            for i, epic in enumerate(epics):
                epic["local_display_number"] = i + 1

        return epics

    def get_milestones(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取里程碑列表"""
        return get_milestones(roadmap_id)

    def get_stories(self, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取特定路线图或所有的故事列表"""
        stories = get_stories(roadmap_id)

        # 添加本地显示编号
        if stories:
            # 按ID顺序对stories进行排序以保证编号一致性
            stories = sorted(stories, key=lambda x: x.get("id", ""))
            for i, story in enumerate(stories):
                story["local_display_number"] = i + 1

        return stories

    def get_tasks(self, roadmap_id: Optional[str] = None, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取任务列表"""
        return get_tasks(roadmap_id, milestone_id)

    def get_milestone_tasks(self, milestone_id: str, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取里程碑任务"""
        return get_milestone_tasks(milestone_id, roadmap_id)

    def get_roadmap_info(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """获取路线图详情"""
        return get_roadmap_info(roadmap_id)

    # --- Sync Operations --- #

    def sync_to_github(self, owner: str, repo: str, roadmap_title: str, roadmap_id: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """将本地路线图更改推送到GitHub项目 (使用注入的服务)"""
        target_roadmap_id = roadmap_id or self.active_roadmap_id
        if not target_roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图"}
        try:
            return self.github_sync.sync_roadmap_to_github(owner, repo, roadmap_title, target_roadmap_id, force=force)
        except Exception as e:
            logger.error(f"Error syncing roadmap {target_roadmap_id} to GitHub: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def sync_status_from_github(self, owner: str, repo: str, roadmap_title: str, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """从GitHub项目同步状态更新到本地路线图 (使用注入的服务)"""
        target_roadmap_id = roadmap_id or self.active_roadmap_id
        if not target_roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图"}
        try:
            return self.github_sync.sync_status_from_github(owner, repo, roadmap_title, target_roadmap_id)
        except Exception as e:
            logger.error(f"Error syncing status from GitHub for roadmap {target_roadmap_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def sync_from_github(
        self, owner: str, repo_name: str, roadmap_title: str, roadmap_id: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """从GitHub项目拉取更新到本地路线图 (使用注入的服务)"""
        target_roadmap_id = roadmap_id or self.active_roadmap_id
        if not target_roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图用于同步目标"}
        try:
            return self.github_sync.sync_roadmap_from_github(owner, repo_name, roadmap_title, target_roadmap_id, force=force)
        except Exception as e:
            logger.error(f"Error syncing from GitHub for roadmap {target_roadmap_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def export_to_yaml(self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """导出路线图到YAML文件

        Args:
            roadmap_id: 路线图ID，默认为活跃路线图
            output_path: 输出文件路径 (可选)

        Returns:
            导出结果字典
        """
        roadmap_id = roadmap_id or self.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "error": "未指定路线图ID且无活动路线图"}

        # 直接使用 YAML 同步服务进行导出
        return self.yaml_sync.export_to_yaml(roadmap_id, output_path)

    # --- GitHub Link Operations --- #

    def link_roadmap_to_github_project(
        self, local_roadmap_id: str, github_owner: str, github_repo: str, github_project_identifier: str
    ) -> Dict[str, Any]:
        """
        将本地路线图与指定的GitHub项目关联。
        实际的 ProjectState 更新由底层的 github_link_operations.link_roadmap_to_github_project 处理。

        Args:
            local_roadmap_id: 本地路线图ID
            github_owner: GitHub仓库所有者
            github_repo: GitHub仓库名称
            github_project_identifier: GitHub项目编号 (UI Number) 或 Node ID

        Returns:
            Dict[str, Any]: 关联结果，直接从底层操作函数返回
        """
        # self (RoadmapServiceFacade 实例) 会传递给 github_link_operations.link_roadmap_to_github_project
        # 它需要 self 来访问例如 github_sync 或其他服务/配置
        link_operation_result = link_roadmap_to_github_project(
            self, local_roadmap_id, github_owner, github_repo, github_project_identifier  # Pass the facade instance
        )

        # 底层函数 link_roadmap_to_github_project (in github_link_operations.py)
        # 已经负责处理 ProjectState 的更新 (包括 active_roadmap_backend_config 和 roadmap_github_mapping).
        # 因此，Facade 层不需要再重复这些更新逻辑。

        if link_operation_result.get("success"):
            self.logger.info(f"路线图 {local_roadmap_id} 与 GitHub 项目的链接操作成功。ProjectState 更新由底层处理。")
        else:
            self.logger.error(f"路线图 {local_roadmap_id} 与 GitHub 项目的链接操作失败: {link_operation_result.get('message')}")

        return link_operation_result

    def find_roadmap_by_github_link(self, owner: str, repo: str, project_identifier: str) -> Optional[str]:
        """
        根据GitHub项目信息查找关联的本地路线图

        Args:
            owner: GitHub用户名或组织名
            repo: GitHub仓库名
            project_identifier: GitHub项目标识符（Number或Node ID）

        Returns:
            Optional[str]: 关联的本地路线图ID，如果未找到则返回None
        """
        return find_roadmap_by_github_link(owner, repo, project_identifier)

    def get_roadmap_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """根据标题获取路线图

        Args:
            title: 路线图标题

        Returns:
            Optional[Dict[str, Any]]: 路线图信息或None
        """
        try:
            with session_scope() as session:
                roadmap = self.roadmap_repo.get_by_title(session, title)
                if roadmap:
                    return self._object_to_dict(roadmap)
                return None
        except Exception as e:
            logger.error(f"通过标题'{title}'获取路线图时出错: {e}", exc_info=True)
            return None

    def create_roadmap(self, title: str, description: str) -> Dict[str, Any]:
        """创建新的路线图

        Args:
            title: 路线图标题
            description: 路线图描述

        Returns:
            Dict[str, Any]: 创建结果，包括成功状态和路线图ID
        """
        try:
            with session_scope() as session:
                # 需要确保 create 方法处理了重复标题的情况或允许重复
                existing_roadmap = self.roadmap_repo.get_by_title(session, title)
                if existing_roadmap:
                    logger.warning(f"尝试创建路线图时发现已存在同名路线图: '{title}' (ID: {existing_roadmap.id})。将返回现有路线图信息。")
                    return {"success": True, "roadmap_id": existing_roadmap.id, "existed": True}

                new_roadmap = self.roadmap_repo.create(session, title=title, description=description)
                if new_roadmap and hasattr(new_roadmap, "id"):
                    return {"success": True, "roadmap_id": new_roadmap.id}
                else:
                    logger.error(f"创建路线图 '{title}' 后未能获取有效ID。")
                    return {"success": False, "error": "创建路线图后未能获取有效ID"}
        except Exception as e:
            logger.error(f"创建路线图 '{title}' 时出错: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

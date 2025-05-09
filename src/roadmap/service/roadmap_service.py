"""
主要路线图服务类。

此类提供高级路线图管理功能，包括与外部系统（如GitHub）的同步操作。
它继承自 RoadmapServiceFacade 以利用基础的路线图操作和数据访问能力。
新代码应优先使用此类来处理路线图相关的业务逻辑和流程编排。
"""

import logging
from typing import Any, Dict, List, Optional

from src.roadmap.service.roadmap_service_facade import RoadmapServiceFacade

# import warnings # No longer needed


logger = logging.getLogger(__name__)


class RoadmapService(RoadmapServiceFacade):
    """
    主要路线图服务类。

    此类提供高级路线图管理功能，包括与外部系统（如GitHub）的同步操作。
    它继承自 RoadmapServiceFacade 以利用基础的路线图操作和数据访问能力。
    新代码应优先使用此类来处理路线图相关的业务逻辑和流程编排。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化路线图服务"""
        super().__init__(config)
        logger.info("RoadmapService 已初始化")

    def _get_github_owner_repo_from_settings(self) -> Dict[str, Optional[str]]:
        """辅助方法：从settings.json获取GitHub owner和repo"""
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            # settings.json 中的 github_info 直接包含 owner 和 repo
            github_settings = status_service.project_state.get_setting("github_info")
            if github_settings and isinstance(github_settings, dict):
                owner = github_settings.get("owner")
                repo = github_settings.get("repo")
                if owner and repo:
                    return {"success": True, "owner": owner, "repo": repo}
        except Exception as e:
            self.logger.error(f"从settings获取github owner/repo失败: {e}", exc_info=True)
        return {"success": False, "owner": None, "repo": None}

    def switch_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """切换当前活动路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 切换结果
        """
        result = {"success": False, "message": ""}
        try:
            self.logger.info(f"验证路线图是否存在: {roadmap_id}")
            roadmap = self.get_roadmap(roadmap_id)  # self.get_roadmap 来自 Facade
            if not roadmap:
                error_msg = f"路线图不存在: {roadmap_id}"
                self.logger.error(error_msg)
                result["message"] = error_msg
                return result

            from src.status.service import StatusService

            status_service = StatusService.get_instance()

            if status_service.project_state.set_current_roadmap_id(roadmap_id):
                self.logger.info(f"活动路线图ID更新成功: {roadmap_id}")

                self.logger.info("尝试更新后端配置 for active roadmap")

                github_project_node_id = status_service.project_state.get_github_project_id_for_roadmap(roadmap_id)

                if github_project_node_id:
                    self.logger.info(f"找到与路线图 {roadmap_id} 关联的GitHub项目Node ID: {github_project_node_id}")

                    # 确保 github_sync 和 api_facade 可用
                    # github_sync 是 Facade 的属性，应该在此可用
                    if self.github_sync and self.github_sync.api_facade:
                        self.logger.info(f"尝试通过API获取GitHub项目详情: {github_project_node_id}")
                        try:
                            gh_project_details = self.github_sync.api_facade.projects_client.get_project_by_node_id(github_project_node_id)

                            if gh_project_details:
                                project_title = gh_project_details.get("title")
                                project_number = gh_project_details.get("number")

                                repo_info = self._get_github_owner_repo_from_settings()
                                if repo_info.get("success"):
                                    owner = repo_info.get("owner")
                                    repo = repo_info.get("repo")

                                    github_config = {
                                        "project_id": github_project_node_id,
                                        "project_number": project_number,
                                        "project_title": project_title,
                                    }

                                    self.logger.info(f"构建的GitHub后端配置 (仅含ID/Number/Title): {github_config}")
                                    # if status_service.project_state.set_active_roadmap_backend_config("github", github_config):
                                    # 修改为只更新 github 部分
                                    current_backend_configs = status_service.project_state.get_active_roadmap_backend_config()
                                    if not isinstance(current_backend_configs, dict):
                                        current_backend_configs = {}
                                    current_backend_configs["github"] = github_config
                                    status_service.project_state.set_active_roadmap_backend_config(current_backend_configs)
                                    self.logger.info("GitHub后端配置(仅含ID/Number/Title)更新成功")
                                    # else:
                                    #     self.logger.warning("GitHub后端配置更新失败")
                                else:
                                    self.logger.warning("无法从settings获取owner/repo，GitHub后端配置将不包含owner/repo信息，这是预期的")
                                    # 清理，因为我们不能只设置部分配置 - 这个逻辑可能需要调整，因为现在我们允许只设置project_id等
                                    # 如果无法获取 owner/repo，我们仍然可以设置 project_id, project_number, project_title
                                    # 如果 github_project_node_id 存在，则至少可以设置它
                                    if github_project_node_id:
                                        github_config = {
                                            "project_id": github_project_node_id,
                                            "project_number": project_number,  # 可能为None
                                            "project_title": project_title,  # 可能为None
                                        }
                                        self.logger.info(f"由于无法获取owner/repo，只设置ID/Number/Title: {github_config}")
                                        current_backend_configs = status_service.project_state.get_active_roadmap_backend_config()
                                        if not isinstance(current_backend_configs, dict):
                                            current_backend_configs = {}
                                        current_backend_configs["github"] = github_config
                                        status_service.project_state.set_active_roadmap_backend_config(current_backend_configs)
                                    else:
                                        # 如果连 github_project_node_id 都没有，才考虑清除
                                        self.logger.warning("无法获取owner/repo且无project_id，将清除GitHub后端配置")
                                        current_backend_configs = status_service.project_state.get_active_roadmap_backend_config()
                                        if not isinstance(current_backend_configs, dict):
                                            current_backend_configs = {}
                                        if "github" in current_backend_configs:
                                            del current_backend_configs["github"]
                                        status_service.project_state.set_active_roadmap_backend_config(current_backend_configs)
                                        self.logger.info("由于无法获取必要信息，已清除活动路线图的GitHub后端配置。")
                            else:
                                self.logger.warning(f"未能获取GitHub项目 {github_project_node_id} 的详细信息。后端配置可能不完整。")
                                status_service.project_state.clear_active_roadmap_backend_config("github")
                                self.logger.info("由于无法获取GitHub项目详情，已清除活动路线图的GitHub后端配置。")

                        except Exception as e:
                            self.logger.error(f"获取GitHub项目详情失败: {e}", exc_info=True)
                            status_service.project_state.clear_active_roadmap_backend_config("github")
                            self.logger.info("由于获取GitHub项目详情时发生错误，已清除活动路线图的GitHub后端配置。")
                    else:
                        self.logger.warning("GitHub sync service 或 API facade 未初始化，无法获取项目详情。")
                        status_service.project_state.clear_active_roadmap_backend_config("github")
                        self.logger.info("由于GitHub同步服务未就绪，已清除活动路线图的GitHub后端配置。")
                else:
                    self.logger.info(f"路线图 {roadmap_id} 未关联到任何GitHub项目。清除活动路线图的GitHub后端配置。")
                    status_service.project_state.clear_active_roadmap_backend_config("github")

                result["success"] = True
                result["message"] = f"已将路线图 {roadmap_id} 设为活动路线图"
                self.logger.info(f"切换活动路线图成功: {roadmap_id}")
                return result
            else:
                error_msg = f"设置活动路线图失败: {roadmap_id}"
                self.logger.error(error_msg)
                result["message"] = error_msg
                return result
        except Exception as e:
            error_msg = f"切换路线图时出错: {e}"
            self.logger.error(error_msg, exc_info=True)
            result["message"] = error_msg
            return result

    # --- 高级同步方法将迁移到这里 --- #
    def push_to_github(self, local_roadmap_id: str, force: bool = False) -> Dict[str, Any]:
        """将指定本地路线图同步到关联的 GitHub Project (高级封装)
        此方法现在在 RoadmapService 中实现。
        """
        self.logger.info(f"====== RoadmapService: 开始 Push 同步: 本地路线图 ID = {local_roadmap_id} ======")
        result = {"status": "error", "message": "", "data": None}

        # 1. 验证服务和配置
        # RoadmapService 继承自 RoadmapServiceFacade, 所以 self.github_sync 应该可用
        if not self.github_sync or not self.github_sync.api_facade:
            result["message"] = "GitHub 同步服务或 API Facade 未初始化。"
            self.logger.error(result["message"])
            return result

        # 获取全局 owner/repo
        try:
            from src.status.service import StatusService  # 确保导入

            status_service = StatusService.get_instance()
            project_state = status_service.project_state
            github_config = status_service.get_domain_status("github_info")
            if not github_config or not github_config.get("configured", False):
                result["message"] = "未找到有效的GitHub配置 (owner/repo)。请运行 'vc status init'。"
                return result
            owner = github_config.get("effective_owner")
            repo = github_config.get("effective_repo")
            if not owner or not repo:
                result["message"] = "GitHub 配置缺少 owner 或 repo。"
                return result
        except Exception as e:
            result["message"] = f"获取GitHub配置失败: {e}"
            self.logger.error(result["message"], exc_info=True)
            return result

        # 2. 验证本地路线图存在
        # self.get_roadmap 来自 RoadmapServiceFacade
        local_roadmap_data = self.get_roadmap(local_roadmap_id)
        if not local_roadmap_data:
            result["message"] = f"未找到本地路线图: {local_roadmap_id}"
            return result
        local_title = local_roadmap_data.get("title") or local_roadmap_data.get("name", "[未知标题]")

        # 3. 检查映射关系 (现在底层 sync_roadmap_to_github 会强制检查)
        # project_state.get_github_project_id_for_roadmap 来自 ProjectState
        project_node_id = project_state.get_github_project_id_for_roadmap(local_roadmap_id)
        if not project_node_id:
            result["message"] = f"本地路线图 '{local_title}' (ID: {local_roadmap_id}) 未与任何 GitHub Project 关联。请先使用 'vc roadmap link' 命令进行关联。"
            self.logger.error(result["message"])
            return result

        self.logger.info(f"找到映射关系: 本地路线图 {local_roadmap_id} -> GitHub Project Node ID {project_node_id}")

        # 4. 调用底层的同步服务 (self.github_sync.sync_roadmap_to_github)
        try:
            self.logger.info(f"RoadmapService: 正在调用 GitHubSyncService.sync_roadmap_to_github for {local_roadmap_id}...")
            sync_result = self.github_sync.sync_roadmap_to_github(roadmap_id=local_roadmap_id, force=force)
            self.logger.info(f"RoadmapService: 底层同步服务返回: {sync_result}")
            return sync_result
        except Exception as e:
            self.logger.error(f"RoadmapService: 调用底层同步服务 push 时出错: {e}", exc_info=True)
            result["message"] = f"同步时发生内部错误: {e}"
            return result

    def pull_from_github(self, remote_project_identifier: str, force: bool = False) -> Dict[str, Any]:
        """从指定的 GitHub Project 拉取数据到关联的本地路线图 (高级封装)
        此方法现在在 RoadmapService 中实现，并调用 GitHubSyncService 中更全面的拉取方法。
        """
        self.logger.info(f"====== RoadmapService: 开始 Pull 同步: 远程 GitHub Project 标识符 = {remote_project_identifier} ======")
        result = {"status": "error", "message": "", "data": None}  # Default error result

        # 1. 验证服务和配置 (github_sync 自身)
        if not self.github_sync or not self.github_sync.api_facade:
            result["message"] = "GitHub 同步服务或 API Facade 未初始化。"
            self.logger.error(result["message"])
            return result

        # 2. 调用 GitHubSyncService 中更全面的 sync_roadmap_from_github 方法
        # 此方法内部会处理 owner/repo 获取、远程项目查找、本地路线图创建/查找、映射以及最终的内容同步
        try:
            self.logger.info(f"RoadmapService: 正在调用 GitHubSyncService.sync_roadmap_from_github for remote identifier {remote_project_identifier}...")
            sync_result = self.github_sync.sync_roadmap_from_github(github_project_identifier=remote_project_identifier, force=force)
            self.logger.info(f"RoadmapService: GitHubSyncService.sync_roadmap_from_github 返回: {sync_result}")
            return sync_result  # 直接返回 GitHubSyncService 的结果

        except Exception as e:
            self.logger.error(f"RoadmapService: 调用 GitHubSyncService.sync_roadmap_from_github 时出错: {e}", exc_info=True)
            result["message"] = f"从 GitHub 拉取数据时发生内部错误: {e}"
            # 避免覆盖 sync_result (如果它被设置了的话), 虽然这里不太可能
            if sync_result and sync_result.get("message"):  # type: ignore
                result["message"] = sync_result.get("message")  # type: ignore
            return result

    # ... (如果还有其他方法如 find_roadmap_by_github_link, 保持它们的原样或根据需要调整)

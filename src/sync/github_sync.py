"""
GitHub 同步服务

负责将本地路线图数据与GitHub项目、里程碑和问题进行双向同步。
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING  # For RoadmapService type hint
from typing import Any, Dict, List, Optional

import requests

from src.db.repositories.mapping_repository import BackendType, EntityMappingRepository, EntityType  # <-- Import EntityMappingRepository
from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, StoryRepository  # <-- Import Repositories
from src.db.session_manager import session_scope  # <-- Import session_scope
from src.sync.github_project import GitHubProjectSync
from src.sync.utils import get_github_sync_config_for_pull, get_github_sync_config_for_push

from .github_api_facade import GitHubApiFacade

# Import the new mapper and facade
from .github_mapper import (
    map_epic_or_story_to_github_issue,
    map_github_issue_to_task_update,
    map_github_milestone_to_milestone_update,
    map_milestone_to_github_milestone,
    map_roadmap_to_github_project,
)

if TYPE_CHECKING:
    from src.roadmap.service import RoadmapService

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """GitHub同步服务

    提供与GitHub项目同步功能
    """

    def __init__(self, roadmap_service: "RoadmapService"):
        """
        初始化GitHub同步服务

        Args:
            roadmap_service: Roadmap服务实例
        """
        self.roadmap_service = roadmap_service
        self._milestone_repo = MilestoneRepository()
        self._epic_repo = EpicRepository()
        self._story_repo = StoryRepository()
        self.mapping_repo = EntityMappingRepository()  # 初始化实体映射仓库

        # GitHub API配置 - 仅获取 token，owner 和 repo 将在每个方法中动态接收
        self.github_token = os.environ.get("GITHUB_TOKEN")

        # 记录Token状态（不打印实际Token）
        if self.github_token:
            token_length = len(self.github_token)
            token_prefix = self.github_token[:4] + "..." if token_length > 4 else ""
            logger.info(f"GitHub Token已配置: 长度 {token_length}, 前缀 {token_prefix}")
        else:
            logger.warning("GitHub Token未在环境变量中找到。同步功能将被禁用。")

        if not self.github_token:
            logger.warning("GitHub token not found in environment variables. Sync functionality will be disabled.")
            self.api_facade = None
        else:
            # 初始化 API 外观，但不传入 owner 和 repo
            self.api_facade = GitHubApiFacade(token=self.github_token)

        self.logger = logging.getLogger(__name__)
        self.logger.info("GitHubSyncService已初始化")

    def is_configured(self) -> bool:
        """检查GitHub同步配置是否完整（仅验证 token 是否存在）"""
        return self.api_facade is not None

    def sync_roadmap_to_github(self, roadmap_id: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        将本地路线图数据同步到GitHub

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图
            force: 是否强制同步

        Returns:
            Dict[str, Any]: 同步结果
        """
        result = {"status": "error", "code": 1, "message": "", "data": None}

        # 获取目标路线图ID，优先使用传入的参数
        target_roadmap_id = roadmap_id
        if not target_roadmap_id:
            target_roadmap_id = self.roadmap_service.active_roadmap_id
            if not target_roadmap_id:
                result["message"] = "未指定路线图ID且无活动路线图可同步"
                result["code"] = 404
                return result
            else:
                logger.info(f"未提供 roadmap_id, 将同步当前活动路线图: {target_roadmap_id}")
        else:
            logger.info(f"准备同步指定路线图: {target_roadmap_id}")

        # 使用工具函数获取和验证配置
        config_result = get_github_sync_config_for_push(target_roadmap_id)
        if not config_result.get("success"):
            result["message"] = config_result.get("message", "获取同步配置失败。")
            result["code"] = 400  # Or another appropriate code
            return result

        owner = config_result["owner"]
        repo = config_result["repo"]
        project_node_id = config_result["project_node_id"]
        project_title = config_result["project_title"]

        if not self.is_configured():
            result["message"] = "GitHub同步未配置 (缺少 GitHub Token)"
            result["code"] = 400
            return result

        # --- Actual Sync Logic ---
        try:
            self.api_facade.clear_cache()  # Clear cache for fresh sync
            stats = {
                "milestones_processed": 0,
                "milestones_created": 0,
                "epics_processed": 0,
                "issues_created": 0,
                "issues_updated": 0,
                "errors": 0,
            }

            # 1. Get Roadmap Data for the target roadmap
            roadmap = self.roadmap_service.get_roadmap(target_roadmap_id)  # 使用 target_roadmap_id
            if not roadmap:
                result["message"] = f"未找到路线图: {target_roadmap_id}"
                result["code"] = 404
                return result

            # 2. Get/Create GitHub Project - 这里应该使用上面确定的 project_title 和 project_node_id
            #    确保 api_facade 使用的是正确的 owner/repo
            #    get_or_create_project 内部逻辑可能需要确认是否需要 owner/repo 参数
            gh_project = self.api_facade.get_or_create_project(owner, repo, project_title, roadmap.get("description", ""))
            if not gh_project:
                result["message"] = f"无法获取或创建GitHub项目: {project_title}"
                stats["errors"] += 1
                return result
            project_url = gh_project.get("html_url", "")
            gh_project_node_id_verified = gh_project.get("id")  # 验证获取/创建的 Node ID

            # 验证 Node ID 是否与预期一致 (如果之前是从映射获取的)
            if project_node_id and gh_project_node_id_verified != project_node_id:
                logger.warning(f"获取/创建的 GitHub 项目 Node ID ({gh_project_node_id_verified}) 与 project_state 中记录的 ({project_node_id}) 不一致！将使用获取/创建的 ID。")
                project_node_id = gh_project_node_id_verified  # 信任实际获取/创建的 ID
                # 可能需要强制更新 project_state 中的映射
                project_state.set_roadmap_github_project(target_roadmap_id, project_node_id)
                if target_roadmap_id == project_state.get_current_roadmap_id():
                    # 更新活动配置...
                    pass

            # 不再需要更新 ProjectState，因为已经在前面处理了映射和活动配置
            # if gh_project_node_id != project_id or ...

            with session_scope() as session:
                # 3. Sync Milestones
                milestones = self.roadmap_service.get_milestones(target_roadmap_id)  # 使用 target_roadmap_id
                gh_milestone_map: Dict[str, int] = {}  # Map local milestone ID to GitHub milestone number
                for ms in milestones:
                    stats["milestones_processed"] += 1
                    ms_payload = map_milestone_to_github_milestone(ms)
                    local_milestone_id = ms["id"]
                    target_title = ms_payload["title"]  # 假设 mapper 生成的 title 是我们要在 GitHub 上使用的

                    # 检查远程是否存在同名 Milestone
                    existing_gh_ms = self.api_facade.get_milestone_by_title(owner, repo, target_title)

                    gh_ms_number = None  # 初始化 gh_ms_number
                    if existing_gh_ms:
                        # 如果存在，更新它
                        milestone_number_to_update = existing_gh_ms["number"]
                        logger.info(f"里程碑 '{target_title}' 已存在 (Number: {milestone_number_to_update})，将尝试更新。")

                        # 准备更新数据
                        update_payload = {
                            "state": ms_payload.get("state", "open"),
                            "description": ms_payload.get("description", "")
                            # 可以根据需要添加 due_on 等其他可更新字段
                        }
                        if ms_payload.get("due_on"):
                            update_payload["due_on"] = ms_payload["due_on"]

                        updated_ms = self.api_facade.update_milestone(
                            owner=owner, repo=repo, milestone_number=milestone_number_to_update, **update_payload  # 传递更新数据
                        )
                        if updated_ms:
                            gh_ms_number = updated_ms["number"]
                            logger.info(f"里程碑 '{target_title}' 更新成功。")
                        else:
                            gh_ms_number = milestone_number_to_update  # 即使更新失败，也记录编号
                            stats["errors"] += 1
                            logger.warning(f"更新里程碑 '{target_title}' (Number: {gh_ms_number}) 失败。")
                    else:
                        # 如果不存在，创建它
                        logger.info(f"里程碑 '{target_title}' 不存在，将尝试创建。")
                        create_payload = {
                            "title": target_title,
                            "state": ms_payload.get("state", "open"),
                            "description": ms_payload.get("description", ""),
                        }
                        if ms_payload.get("due_on"):
                            create_payload["due_on"] = ms_payload["due_on"]

                        created_ms = None  # 初始化 created_ms
                        try:
                            created_ms = self.api_facade.issues_client.create_milestone(
                                owner=owner,
                                repo=repo,
                                title=create_payload["title"],
                                state=create_payload.get("state", "open"),
                                description=create_payload.get("description", ""),
                                due_on=create_payload.get("due_on"),
                            )
                            if created_ms:
                                gh_ms_number = created_ms.get("number")
                                stats["milestones_created"] += 1
                                logger.info(f"里程碑 '{target_title}' 创建成功 (Number: {gh_ms_number})。")
                        except requests.exceptions.HTTPError as e:
                            if e.response is not None and e.response.status_code == 422:
                                error_details_text = e.response.text
                                try:
                                    error_details = e.response.json()
                                    if any(err.get("code") == "already_exists" for err in error_details.get("errors", [])):
                                        logger.warning(f"尝试创建里程碑 '{target_title}' 失败，因为它已存在。将尝试重新获取它。")
                                        refetched_ms = self.api_facade.get_milestone_by_title(owner, repo, target_title)
                                        if refetched_ms:
                                            gh_ms_number = refetched_ms.get("number")
                                            logger.info(f"已成功重新获取到预先存在的里程碑 '{target_title}' (Number: {gh_ms_number})。")
                                        else:
                                            stats["errors"] += 1
                                            logger.error(f"里程碑 '{target_title}' 确认已存在但无法重新获取。")
                                    else:
                                        stats["errors"] += 1
                                        logger.error(f"创建里程碑 '{target_title}' 时发生 422 错误 (非 already_exists): {error_details_text}", exc_info=True)
                                except ValueError:
                                    stats["errors"] += 1
                                    logger.error(f"创建里程碑 '{target_title}' 时发生 422 错误，且响应不是有效的 JSON: {error_details_text}", exc_info=True)
                            else:
                                stats["errors"] += 1
                                logger.error(f"创建里程碑 '{target_title}' 时发生其他 HTTP 错误: {e}", exc_info=True)
                                # Consider re-raising for unexpected HTTP errors if not handled by outer try-except
                                # raise
                        except Exception as e:
                            stats["errors"] += 1
                            logger.error(f"创建里程碑 '{target_title}' 时发生未知错误: {e}", exc_info=True)

                        # 如果 gh_ms_number 仍然是 None (创建失败且重新获取也失败)，记录错误
                        if gh_ms_number is None and not created_ms:  # 确保只在真的失败时记录
                            logger.warning(f"最终未能成功创建或获取里程碑 '{target_title}'。")
                            # 错误计数已在上面的 except 块中处理，此处不再重复增加 stats["errors"]

                    # 记录本地ID到GitHub编号的映射
                    if gh_ms_number is not None:
                        gh_milestone_map[local_milestone_id] = gh_ms_number
                    else:
                        # 如果创建和更新都失败了，记录错误
                        logger.error(f"无法同步里程碑 '{target_title}' (本地ID: {local_milestone_id})，后续关联的 Issue 可能受影响。")
                        # 考虑到 existing_gh_ms 为 None 时 create 也失败的情况
                        if not existing_gh_ms:  # 只有在尝试创建失败时才增加错误计数
                            stats["errors"] += 1

                # 4. Sync Epics/Stories as Issues
                epics = self.roadmap_service.get_epics(target_roadmap_id)  # 使用 target_roadmap_id
                stories = self.roadmap_service.get_stories(target_roadmap_id)  # 使用 target_roadmap_id
                items_to_sync = epics + stories  # Combine Epics and Stories

                for item in items_to_sync:
                    stats["epics_processed"] += 1  # Consider renaming stat if includes stories
                    local_entity_id = item["id"]
                    local_entity_type = item.get("type", "epic" if item in epics else "story")

                    # 获取实体映射
                    mapping = self.mapping_repo.get_mapping_by_local_id(session, local_entity_id, local_entity_type, "github")

                    gh_milestone_number = gh_milestone_map.get(item.get("milestone_id"))
                    issue_payload = map_epic_or_story_to_github_issue(item, owner, repo, gh_milestone_number)

                    item_name = item.get("name") or item.get("title", "") or ""
                    issue_payload["title"] = f"[{local_entity_type.capitalize()}] {item_name[:100]}"

                    if mapping and mapping.remote_entity_number:
                        # 更新现有issue
                        issue_number = int(mapping.remote_entity_number)
                        logger.info(f"更新现有GitHub issue #{issue_number}，本地类型: {local_entity_type}, 本地ID: {local_entity_id}")

                        update_data = {
                            "title": issue_payload.get("title"),
                            "body": issue_payload.get("body"),
                            "state": issue_payload.get("state", "open"),
                        }

                        # Robust Assignees handling
                        assignees_input = issue_payload.get("assignees", [])
                        if isinstance(assignees_input, str):  # Handle if mapper returns a single string
                            assignees_input = [assignees_input] if assignees_input.strip() else []
                        cleaned_assignees = [str(a).strip() for a in assignees_input if isinstance(a, str) and str(a).strip()]
                        update_data["assignees"] = cleaned_assignees

                        # Robust Labels handling
                        labels_input = issue_payload.get("labels", [])
                        if isinstance(labels_input, str):  # Handle if mapper returns a single string
                            labels_input = [labels_input] if labels_input.strip() else []
                        cleaned_labels = [str(l).strip() for l in labels_input if isinstance(l, str) and str(l).strip()]
                        update_data["labels"] = cleaned_labels

                        # Robust Milestone handling: ensure it's an int or None
                        milestone_input = issue_payload.get("milestone")  # This should be GitHub milestone number or None
                        if isinstance(milestone_input, int):
                            update_data["milestone"] = milestone_input
                        elif milestone_input is None:
                            update_data["milestone"] = None  # Explicitly None for clearing
                        else:
                            # If milestone_input is something else (e.g. empty string, 0 not meaning a real milestone 0),
                            # treat as no milestone change or clear, depending on API. For safety, treat as None.
                            logger.warning(f"Invalid milestone_input '{milestone_input}' for issue #{issue_number}, attempting to clear milestone.")
                            update_data["milestone"] = None

                        logger.debug(f"Attempting to update issue #{issue_number} with data: {update_data}")
                        updated = self.api_facade.update_issue(owner, repo, issue_number, update_data)
                        if updated:
                            stats["issues_updated"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        # 创建新issue
                        logger.debug(f"Attempting to create issue with payload: {issue_payload}")  # Log create_issue payload
                        created_issue = self.api_facade.create_issue(
                            owner,
                            repo,
                            issue_payload.get("title"),
                            issue_payload.get("body", ""),
                            issue_payload.get("assignees", []),
                            issue_payload.get("milestone"),
                            issue_payload.get("labels", []),
                        )
                        if created_issue:
                            stats["issues_created"] += 1
                            # 创建实体映射
                            self.mapping_repo.create_mapping(
                                session,
                                local_entity_id=local_entity_id,
                                local_entity_type=local_entity_type,
                                backend_type="github",
                                remote_entity_id=created_issue.get("node_id"),
                                remote_entity_number=str(created_issue.get("number")),
                                local_project_id=target_roadmap_id,  # 使用 target_roadmap_id
                                remote_project_id=project_node_id,  # 使用确定的 project_node_id
                                remote_project_context=project_title,  # 使用确定的 project_title
                            )
                        else:
                            stats["errors"] += 1

            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"路线图 '{roadmap.get('title', target_roadmap_id)}' 已同步到 GitHub: {project_url}"
            result["data"] = {"roadmap_id": target_roadmap_id, "stats": stats}

            # 在成功同步后，强制更新并清理 project_state 中的映射
            if result["status"] == "success":
                # 获取 project_state 实例
                from src.status.service import StatusService

                status_service = StatusService.get_instance()
                project_state = status_service.project_state

                final_project_node_id = gh_project.get("id") if gh_project else project_node_id
                if final_project_node_id:
                    logger.info(
                        f"Finalizing and cleaning project state mapping for local roadmap {target_roadmap_id} to remote {final_project_node_id}."
                    )
                    # 直接调用，不再检查返回值，失败会在 _save_state 中记录日志
                    project_state.set_roadmap_github_project(target_roadmap_id, final_project_node_id)
                    logger.info(f"已尝试更新 ProjectState 中的路线图-GitHub映射。")
                    # 如果是活动路线图，并且我们获得了完整的 gh_project 信息，则更新其后端配置
                    if target_roadmap_id == project_state.get_current_roadmap_id() and gh_project:
                        active_backend_config = {
                            "project_id": final_project_node_id,
                            "project_number": gh_project.get("number"),
                            "project_title": gh_project.get("title"),
                        }
                        # 使用新的API直接设置配置
                        current_total_backend_config = project_state.get_active_roadmap_backend_config()
                        if not isinstance(current_total_backend_config, dict):
                            current_total_backend_config = {}
                        current_total_backend_config["github"] = active_backend_config
                        project_state.set_active_roadmap_backend_config(current_total_backend_config)

                        logger.info(f"Successfully updated active roadmap backend config (excluding owner/repo) for {target_roadmap_id}.")
            return result

        except Exception as e:
            logger.error(f"同步路线图到GitHub时出错: {e}", exc_info=True)
            result["message"] = f"同步路线图到GitHub时出错: {e}"
            result["code"] = 500
            return result

    def sync_status_from_github(
        self, owner: str, repo: str, github_project_node_id: str, target_local_roadmap_id: str, project_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从GitHub同步状态到本地路线图 (不创建或删除本地实体，仅更新状态)

        Args:
            owner: GitHub仓库所有者
            repo: GitHub仓库名称
            github_project_node_id: GitHub Project的Node ID
            target_local_roadmap_id: 目标本地路线图ID
            project_title: GitHub项目标题 (用于创建映射)

        Returns:
            Dict[str, Any]: 同步结果
        """
        self.logger.info(f"====== 开始从GitHub同步数据到路线图 {target_local_roadmap_id} (远程项目Node ID: {github_project_node_id}) ======")
        result = {"status": "error", "code": 1, "message": "", "data": None}

        # 参数已直接传入，不再依赖 project_state.get_active_roadmap_backend_config

        if not self.is_configured():
            result["message"] = "GitHub同步未配置 (缺少 GitHub Token)"
            result["code"] = 400
            return result

        # --- Actual Sync Logic ---
        try:
            self.api_facade.clear_cache()
            stats = {
                "milestones_fetched": 0,
                "milestones_updated_local": 0,
                "issues_fetched": 0,
                "issues_updated_local": 0,
                "new_entities_created": 0,
                "errors": 0,
            }

            with session_scope() as session:
                # 1. Fetch GitHub Milestones
                gh_milestones = self.api_facade.get_milestones(owner, repo)
                stats["milestones_fetched"] = len(gh_milestones)

                for gh_ms in gh_milestones:
                    # 尝试通过映射查找本地里程碑
                    # 注意：里程碑通常不通过全局ID映射，而是通过标题在项目内匹配
                    local_ms = self._milestone_repo.get_by_title_and_roadmap_id(session, gh_ms["title"], target_local_roadmap_id)

                    if local_ms:
                        update_data = map_github_milestone_to_milestone_update(gh_ms)
                        self._milestone_repo.update(session, local_ms.id, update_data)
                        stats["milestones_updated_local"] += 1
                    # else:  是否要根据GitHub里程碑创建本地里程碑？目前不处理

                # 2. Fetch GitHub Issues (for the configured project, if possible)
                # 如果project_id (GitHub Project Node ID)存在，尝试仅获取该项目中的问题
                # 否则获取仓库所有问题，然后根据标签或其他信息筛选
                gh_issues = []
                project_items_fetched = False
                if github_project_node_id:  # 使用传入的 github_project_node_id
                    logger.info(f"正在为GitHub Project Node ID: {github_project_node_id} 获取特定条目 (issues/PRs)...")
                    # get_all_project_items_by_node_id 返回的是 ProjectItem 对象列表
                    # 每个 ProjectItem 的 content 字段才是 Issue 或 PullRequest
                    project_items = self.api_facade.get_all_project_items_by_node_id(github_project_node_id)
                    if project_items:
                        project_items_fetched = True
                        for item in project_items:
                            if item and isinstance(item.get("content"), dict):
                                gh_issues.append(item["content"])  # 提取实际的 Issue/PR 对象
                            else:
                                logger.warning(f"Project item (ID: {item.get('id')}) has no 'content' or content is not a dict. Item: {item}")

                    if not gh_issues:  # 如果从 project items 中没有提取到任何 issue
                        logger.warning(f"未能通过项目Node ID {github_project_node_id} 获取任何特定问题 (或提取内容失败)。可能项目为空或API访问问题。将回退到获取仓库所有问题。")
                        # Fallback only if project_items_fetched was True but gh_issues is empty, or if project_items_fetched was False
                        if not project_items_fetched or not project_items:  # if get_all_project_items_by_node_id returned empty or failed to extract
                            gh_issues = self.api_facade.get_issues(owner, repo, state="all")
                else:
                    logger.info("未提供GitHub Project Node ID，将获取仓库所有问题。")
                    gh_issues = self.api_facade.get_issues(owner, repo, state="all")

                stats["issues_fetched"] = len(gh_issues)

                for gh_issue in gh_issues:  # 现在 gh_issue 应该是实际的 Issue/PR 对象
                    # 确保 gh_issue 是字典并且有 node_id，以防万一 fallback 的 get_issues 返回非预期格式
                    if not isinstance(gh_issue, dict):
                        logger.warning(f"Skipping non-dictionary issue data: {gh_issue}")
                        continue

                    # 使用 content 中的 id (I_... / PR_...) 作为 remote_entity_id
                    remote_entity_id = gh_issue.get("id")
                    if not remote_entity_id:
                        logger.warning(f"Skipping issue because it does not have an 'id'. Issue data: {gh_issue.get('html_url', gh_issue)}")
                        continue
                    remote_entity_id = str(remote_entity_id)
                    # remote_issue_number 仍然来自 content.number
                    remote_issue_number = str(gh_issue.get("number"))

                    # 尝试通过远程ID (I_/PR_) 或编号查找本地实体映射
                    mapping = self.mapping_repo.get_mapping_by_remote_id(session, remote_entity_id, "github")  # 使用 content.id
                    if not mapping and remote_issue_number:
                        # 如果 fallback 到按编号查找，仍然需要 remote_project_node_id 作为上下文
                        mapping = self.mapping_repo.get_mapping_by_remote_number(
                            session, remote_issue_number, "epic", "github", github_project_node_id
                        )
                        if not mapping:
                            mapping = self.mapping_repo.get_mapping_by_remote_number(
                                session, remote_issue_number, "story", "github", github_project_node_id
                            )

                    if mapping:
                        # 更新本地实体
                        local_entity_id = mapping.local_entity_id
                        local_entity_type = mapping.local_entity_type.value
                        update_data = map_github_issue_to_task_update(gh_issue)  # 假设映射到Task/Story/Epic

                        if local_entity_type == "epic":
                            self._epic_repo.update(session, local_entity_id, update_data)
                        elif local_entity_type == "story":
                            self._story_repo.update(session, local_entity_id, update_data)
                        # 添加对Task的更新（如果适用）

                        stats["issues_updated_local"] += 1
                    else:
                        # 如果没有映射，根据GitHub Issue创建新的本地实体 (Epic/Story/Task)
                        # 识别该Issue是否为"纯Task"类型：通过检查其标签和是否关联到GitHub Milestone
                        labels = gh_issue.get("labels", [])
                        label_names = [label.get("name") for label in labels]
                        gh_milestone = gh_issue.get("milestone")

                        # 判断是否为"纯Task"：没有epic或story标签，且关联了Milestone
                        is_pure_task = (
                            gh_milestone is not None
                            and "epic" not in label_names  # 有关联的GitHub Milestone
                            and "story" not in label_names  # 不是Epic  # 不是Story
                        )

                        if is_pure_task:
                            # 1. 获取/同步本地Milestone
                            local_milestone = None
                            milestone_title = gh_milestone.get("title")
                            if milestone_title:
                                local_milestone = self._milestone_repo.get_by_title_and_roadmap_id(session, milestone_title, target_local_roadmap_id)

                                # 如果本地找不到这个Milestone，可以选择创建
                                if not local_milestone:
                                    try:
                                        # 创建Milestone的简化逻辑
                                        ms_data = {
                                            "title": milestone_title,
                                            "description": gh_milestone.get("description", ""),
                                            "status": "planned",
                                            "roadmap_id": target_local_roadmap_id,  # 使用 target_local_roadmap_id
                                            "created_at": str(self.roadmap_service.get_now()),
                                            "updated_at": str(self.roadmap_service.get_now()),
                                        }
                                        local_milestone = self._milestone_repo.create(session, **ms_data)
                                        logger.info(f"为GitHub里程碑'{milestone_title}'创建了本地里程碑 (ID: {local_milestone.id})")
                                    except Exception as ms_err:
                                        logger.error(f"创建本地里程碑失败: {ms_err}", exc_info=True)

                            if local_milestone:
                                # 2. 获取/创建隐式Story
                                implicit_story_id = self.roadmap_service.get_or_create_implicit_story_for_milestone(
                                    session, local_milestone.id, local_milestone.title, target_local_roadmap_id  # 使用 target_local_roadmap_id
                                )

                                if implicit_story_id:
                                    # 3. 创建本地Task
                                    task_data = map_github_issue_to_task_update(gh_issue)
                                    task_data.update(
                                        {
                                            "story_id": implicit_story_id,
                                            "created_at": str(self.roadmap_service.get_now()),
                                            "updated_at": str(self.roadmap_service.get_now()),
                                        }
                                    )

                                    try:
                                        created_task = self.roadmap_service.task_repo.create(session, **task_data)
                                        if created_task and hasattr(created_task, "id"):
                                            # 4. 创建实体映射
                                            self.mapping_repo.create_mapping(
                                                session,
                                                local_entity_id=created_task.id,
                                                local_entity_type="task",
                                                backend_type="github",
                                                remote_entity_id=remote_entity_id,  # 使用 content.id
                                                remote_entity_number=remote_issue_number,
                                                local_project_id=target_local_roadmap_id,
                                                remote_project_id=github_project_node_id,
                                                remote_project_context=project_title or f"Project {github_project_node_id}",  # 使用传入的project_title
                                            )

                                            logger.info(
                                                f"已为GitHub Issue #{gh_issue['number']} ('{gh_issue['title']}') 创建本地Task (ID: {created_task.id})"
                                            )
                                            stats["new_entities_created"] += 1
                                        else:
                                            logger.error(f"创建本地Task失败，未获得有效的Task对象")
                                            stats["errors"] += 1
                                    except Exception as task_err:
                                        logger.error(f"创建本地Task出错: {task_err}", exc_info=True)
                                        stats["errors"] += 1
                                else:
                                    logger.error(f"为里程碑'{local_milestone.title}'创建隐式Story失败，无法创建Task")
                                    stats["errors"] += 1
                            else:
                                logger.warning(f"无法找到或创建与GitHub里程碑对应的本地里程碑，跳过创建Task")
                        else:
                            # 对于非纯Task类型(可能是Epic或Story)或无关联Milestone的Issue，记录日志
                            logger.info(f"找到GitHub Issue #{gh_issue['number']} ('{gh_issue['title']}')，但没有本地映射且不符合纯Task条件，跳过创建。")

            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"从GitHub同步状态到路线图 '{target_local_roadmap_id}' 成功"
            result["data"] = {"roadmap_id": target_local_roadmap_id, "stats": stats}
            self.logger.info(f"====== 从GitHub同步到路线图 {target_local_roadmap_id} 完成 ======")
            return result

        except Exception as e:
            logger.error(f"从GitHub同步状态时出错: {e}", exc_info=True)
            result["message"] = f"从GitHub同步状态时出错: {e}"
            result["code"] = 500
            return result

    def sync_roadmap_from_github(self, github_project_identifier: str, force: bool = False) -> Dict[str, Any]:
        """
        从GitHub同步项目数据到本地路线图

        Args:
            github_project_identifier: GitHub Project的Node ID或编号
            force: 是否强制同步

        Returns:
            Dict[str, Any]: 同步结果
        """
        result = {"status": "error", "code": 1, "message": "", "data": None}

        try:
            config_result = get_github_sync_config_for_pull(github_project_identifier)
            if not config_result.get("success"):
                result["message"] = config_result.get("message", "获取 pull 同步配置失败。")
                result["code"] = 400
                return result

            owner = config_result["owner"]
            repo = config_result["repo"]
            remote_project_node_id = config_result["remote_project_node_id"]
            remote_project_title = config_result["remote_project_title"]
            # project_state = config_result["project_state"] # <--- REMOVE THIS LINE
            # 获取 project_state 的新方式:
            project_state = self.roadmap_service.project_state
            if not project_state:
                logger.error("无法通过 self.roadmap_service.project_state 获取 ProjectStateService 实例。")
                result["message"] = "内部错误：无法访问项目状态服务。"
                result["code"] = 500
                return result

            remote_project_number = config_result.get("remote_project_number")  # Get number also

            if not self.is_configured():
                result["message"] = "GitHub同步未配置 (缺少 GitHub Token)"
                result["code"] = 400
                return result

            # 查找或创建本地路线图并建立映射
            target_local_roadmap_id = None
            all_mappings = project_state.get_all_roadmap_github_mappings()
            for local_id, github_id_map_val in all_mappings.items():
                if github_id_map_val == remote_project_node_id:
                    target_local_roadmap_id = local_id
                    logger.info(f"找到已映射的本地路线图ID: {target_local_roadmap_id} -> GitHub项目ID: {remote_project_node_id}")
                    break

            if not target_local_roadmap_id:
                logger.info(f"未找到本地路线图映射到远程项目 {remote_project_node_id} ('{remote_project_title}')。将尝试创建新的本地路线图。")
                existing_roadmap_by_title = self.roadmap_service.get_roadmap_by_title(remote_project_title)
                if existing_roadmap_by_title:
                    target_local_roadmap_id = existing_roadmap_by_title["id"]
                    logger.info(f"找到现有同名本地路线图 '{remote_project_title}' (ID: {target_local_roadmap_id})。将使用此路线图并建立映射。")
                else:
                    create_roadmap_result = self.roadmap_service.create_roadmap(
                        title=remote_project_title, description=f"本地路线图，关联到 GitHub Project '{remote_project_title}' (ID: {remote_project_node_id})"
                    )
                    if create_roadmap_result.get("success"):
                        target_local_roadmap_id = create_roadmap_result.get("roadmap_id")
                        logger.info(f"成功创建新的本地路线图 '{remote_project_title}' (ID: {target_local_roadmap_id})。")
                    else:
                        result["message"] = f"创建本地路线图 '{remote_project_title}' 失败: {create_roadmap_result.get('error')}"
                        result["code"] = 500
                        return result

                if not project_state.set_roadmap_github_project(target_local_roadmap_id, remote_project_node_id):
                    logger.warning(f"为本地路线图 {target_local_roadmap_id} 和远程项目 {remote_project_node_id} 设置映射失败。同步可能不一致。")
            else:
                logger.info(f"找到已映射的本地路线图 (ID: {target_local_roadmap_id}) 对应远程项目 {remote_project_node_id} ('{remote_project_title}')。")

            sync_result = self.sync_status_from_github(
                owner=owner,
                repo=repo,
                github_project_node_id=remote_project_node_id,
                target_local_roadmap_id=target_local_roadmap_id,
                project_title=remote_project_title,
            )

            if sync_result["status"] == "success":
                result["status"] = "success"
                result["message"] = f"已成功从GitHub项目 '{remote_project_title}' 同步数据到本地路线图 '{target_local_roadmap_id}'"
                result["data"] = {
                    "local_roadmap_id": target_local_roadmap_id,
                    "remote_project_details": {
                        "node_id": remote_project_node_id,
                        "title": remote_project_title,
                        "number": remote_project_number,  # Use the fetched number
                    },
                    "stats": sync_result.get("data", {}).get("stats", {}),
                }
                result["code"] = 200
            else:
                result["status"] = sync_result.get("status", "error")
                result[
                    "message"
                ] = f"从GitHub项目 '{remote_project_title}' 同步到本地路线图 '{target_local_roadmap_id}' 时发生错误或部分成功: {sync_result.get('message', '未知错误')}"
                result["data"] = {
                    "local_roadmap_id": target_local_roadmap_id,
                    "remote_project_details": {
                        "node_id": remote_project_node_id,
                        "title": remote_project_title,
                        "number": remote_project_number,  # Use the fetched number
                    },
                }
                result["code"] = sync_result.get("code", 500)

            return result

        except Exception as e:
            logger.error(f"从GitHub同步项目数据到本地路线图时出错: {e}", exc_info=True)
            # Ensure result is a dict before trying to update it, or just create a new one for error
            error_result = {"status": "error", "code": 500, "message": "", "data": None}
            error_result["message"] = f"从GitHub同步项目数据到本地路线图时出错: {e}"
            return error_result

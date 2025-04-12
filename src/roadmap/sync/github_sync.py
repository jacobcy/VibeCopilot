"""
GitHub 同步服务

负责将本地路线图数据与GitHub项目、里程碑和问题进行双向同步。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

# Import local services and models (adjust paths if necessary)
from src.db.service import DatabaseService  # Needed for updating local data

from .github_api_facade import GitHubApiFacade

# Import the new mapper and facade
from .github_mapper import (
    map_epic_or_story_to_github_issue,
    map_github_issue_to_task_update,
    map_github_milestone_to_milestone_update,
    map_milestone_to_github_milestone,
    map_roadmap_to_github_project,
)

# 修改为字符串类型注解，避免循环导入
# from src.roadmap.service import RoadmapService  # 导入 RoadmapService

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """GitHub同步服务，协调本地路线图与GitHub的数据同步"""

    def __init__(self, roadmap_service: "RoadmapService", db_service: Optional[DatabaseService] = None):
        """
        初始化GitHub同步服务

        Args:
            roadmap_service: Roadmap服务实例
            db_service: 数据库服务实例 (for updating local data)
        """
        self.roadmap_service = roadmap_service
        self.db_service = db_service  # Store db_service

        # GitHub API配置
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_owner = os.environ.get("GITHUB_OWNER")
        self.github_repo = os.environ.get("GITHUB_REPO")

        if not all([self.github_token, self.github_owner, self.github_repo]):
            logger.warning("GitHub sync configuration (token, owner, repo) is incomplete. Sync functionality will be disabled.")
            self.api_facade = None
        else:
            self.api_facade = GitHubApiFacade(token=self.github_token, owner=self.github_owner, repo=self.github_repo)

        self._mock_mode = os.environ.get("MOCK_SYNC", "false").lower() == "true"

    def is_configured(self) -> bool:
        """检查GitHub同步配置是否完整"""
        return self.api_facade is not None

    def sync_roadmap_to_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        将本地路线图数据同步到GitHub

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        result = {"status": "error", "code": 1, "message": "", "data": None}
        roadmap_id = roadmap_id or self.roadmap_service.get_active_roadmap_id()
        if not roadmap_id:
            result["message"] = "没有活动的路线图可同步"
            result["code"] = 404
            return result

        if not self.is_configured():
            result["message"] = "GitHub同步未配置 (缺少环境变量)"
            result["code"] = 400
            return result

        # Mock mode handling
        if self._mock_mode:
            logger.info(f"[MOCK] 同步路线图 {roadmap_id} 到 GitHub")
            roadmap = self.roadmap_service.get_roadmap(roadmap_id)
            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"模拟同步路线图 '{roadmap.get('title', roadmap_id) or roadmap.get('name', roadmap_id) or '[未命名路线图]'} 到 GitHub 成功"
            result["data"] = {
                "note": "使用模拟数据",
                "roadmap_id": roadmap_id,
                "stats": {"milestones_synced": 1, "epics_synced": 2, "issues_created": 3},
            }
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

            # 1. Get Roadmap Data
            roadmap = self.roadmap_service.get_roadmap(roadmap_id)
            if not roadmap:
                result["message"] = f"未找到路线图: {roadmap_id}"
                result["code"] = 404
                return result

            # 2. Get/Create GitHub Project
            project_payload = map_roadmap_to_github_project(roadmap)
            gh_project = self.api_facade.get_or_create_project(project_payload["title"], project_payload["description"])
            if not gh_project:
                result["message"] = f"无法获取或创建GitHub项目: {project_payload['title']}"
                stats["errors"] += 1
                # Continue syncing milestones/issues even if project fails?
                # For now, let's stop if project fails.
                return result
            project_url = gh_project.get("html_url", "")

            # 3. Sync Milestones
            milestones = self.roadmap_service.get_milestones(roadmap_id)
            gh_milestone_map: Dict[str, int] = {}  # Map local milestone ID to GitHub milestone number
            for ms in milestones:
                stats["milestones_processed"] += 1
                ms_payload = map_milestone_to_github_milestone(ms)
                gh_ms = self.api_facade.get_or_create_milestone(
                    title=ms_payload["title"],
                    local_id=ms["id"],  # Pass local ID for caching
                    description=ms_payload["description"],
                    state=ms_payload["state"]
                    # Add due_on if mapped
                )
                if gh_ms:
                    gh_milestone_map[ms["id"]] = gh_ms.get("number")  # Use number for linking issues
                else:
                    stats["errors"] += 1
                    logger.warning(f"无法同步里程碑: {ms.get('title') or ms.get('name')}")

            # 4. Sync Epics/Stories as Issues
            epics = self.roadmap_service.get_epics(roadmap_id)
            stories = self.roadmap_service.get_stories(roadmap_id)  # Assuming this method exists

            items_to_sync = epics + stories  # Combine Epics and Stories

            for item in items_to_sync:
                stats["epics_processed"] += 1  # Consider renaming stat if includes stories
                gh_milestone_number = gh_milestone_map.get(item.get("milestone_id"))

                issue_payload = map_epic_or_story_to_github_issue(item, self.github_owner, self.github_repo, gh_milestone_number)

                # Try to find existing issue (e.g., based on title part or stored link)
                # Simplistic search for now, needs improvement (e.g., using labels or body refs)
                issue_title_search = f"[{item.get('type', 'item').capitalize()}] {item.get('name')[:30]}"  # Search based on type/name prefix
                existing_gh_issue = self.api_facade.find_issue_by_title(issue_title_search)

                if existing_gh_issue:
                    # Update existing issue
                    issue_number = existing_gh_issue.get("number")
                    # Only update fields that might change (state, milestone, assignee, labels?)
                    update_data = {
                        "state": issue_payload["state"],
                        "milestone": issue_payload.get("milestone"),  # Ensure this maps to number
                        "labels": issue_payload.get("labels", [])
                        # Add assignee update if needed
                    }
                    updated = self.api_facade.update_issue(issue_number, update_data)
                    if updated:
                        stats["issues_updated"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    # Create new issue
                    created_issue = self.api_facade.create_issue(issue_payload)
                    if created_issue:
                        stats["issues_created"] += 1
                        # TODO: Store the created issue number/id back to the local item (Epic/Story)
                        # self.db_service.update_epic(item['id'], {"github_issue_number": created_issue.get("number")})
                    else:
                        stats["errors"] += 1

                # TODO: Add issue to project if needed
                # if created_issue or existing_gh_issue:
                #     issue_node_id = (created_issue or existing_gh_issue).get('node_id')
                #     if issue_node_id and gh_project:
                #         self.api_facade.add_issue_to_project(gh_project.get('id'), issue_node_id)

            result["status"] = "success"
            result["code"] = 0
            # 优先使用title字段，然后是name字段
            roadmap_name = roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"
            result["message"] = f"路线图 '{roadmap_name}' 同步到 GitHub 完成"
            result["data"] = {
                "roadmap_id": roadmap_id,
                "github_project_url": project_url,
                "stats": stats,
            }
            return result

        except Exception as e:
            logger.exception(f"同步路线图 {roadmap_id} 到 GitHub 时出错: {e}")
            result["message"] = f"同步到 GitHub 错误: {e}"
            result["code"] = 500
            result["data"] = {"roadmap_id": roadmap_id, "stats": stats}
            return result

    def sync_status_from_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从GitHub同步状态回本地路线图

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        result = {"status": "error", "code": 1, "message": "", "data": None}
        roadmap_id = roadmap_id or self.roadmap_service.get_active_roadmap_id()
        if not roadmap_id:
            result["message"] = "没有活动的路线图可同步状态"
            result["code"] = 404
            return result

        if not self.is_configured():
            result["message"] = "GitHub同步未配置 (缺少环境变量)"
            result["code"] = 400
            return result

        # Mock mode handling
        if self._mock_mode:
            logger.info(f"[MOCK] 从 GitHub 同步状态到路线图 {roadmap_id}")
            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"模拟从 GitHub 同步状态到路线图 {roadmap_id} 成功"
            result["data"] = {
                "note": "使用模拟数据",
                "roadmap_id": roadmap_id,
                "stats": {"tasks_updated": 5, "milestones_updated": 1},
            }
            return result

        # --- Actual Sync Logic ---
        try:
            self.api_facade.clear_cache()
            stats = {
                "milestones_checked": 0,
                "milestones_updated": 0,
                "issues_checked": 0,
                "items_updated": 0,
                "errors": 0,
            }

            # 1. Get local roadmap data (needed for context? maybe just milestones/epics/stories)
            roadmap = self.roadmap_service.get_roadmap(roadmap_id)
            if not roadmap:
                result["message"] = f"未找到路线图: {roadmap_id}"
                result["code"] = 404
                return result

            # 2. Fetch GitHub Milestones and update local ones
            # This requires local milestones to have a stored link (e.g., github_milestone_number)
            local_milestones = self.roadmap_service.get_milestones(roadmap_id)
            gh_milestones = self.api_facade.issues_client.get_milestones(self.owner, self.repo)
            gh_milestone_map_by_title = {m.get("title"): m for m in gh_milestones}

            for local_ms in local_milestones:
                stats["milestones_checked"] += 1
                gh_ms = gh_milestone_map_by_title.get(local_ms.get("title"))  # Match by title
                if gh_ms:
                    update_data = map_github_milestone_to_milestone_update(gh_ms)
                    # Use db_service to update the local milestone
                    updated = self.db_service.update_milestone(local_ms["id"], update_data)  # Assuming db_service has update_milestone
                    if updated:
                        stats["milestones_updated"] += 1
                    else:
                        logger.warning(f"无法更新本地里程碑状态: {local_ms.get('title') or local_ms.get('name')}")
                        stats["errors"] += 1
                else:
                    logger.info(f"本地里程碑 '{local_ms.get('title') or local_ms.get('name')}' 在 GitHub 上未找到对应项")

            # 3. Fetch GitHub Issues and update local Epics/Stories/Tasks
            # This requires local items to store the corresponding github_issue_number
            local_items = self.roadmap_service.get_epics(roadmap_id) + self.roadmap_service.get_stories(roadmap_id)
            # TODO: Include Tasks if they are also synced as issues?

            for item in local_items:
                github_issue_number = item.get("github_issue_number")  # Assuming this link exists
                if github_issue_number:
                    stats["issues_checked"] += 1
                    gh_issue = self.api_facade.get_issue(github_issue_number)
                    if gh_issue:
                        update_data = map_github_issue_to_task_update(gh_issue)  # Use task mapper for basic status/assignee
                        # Update the correct local entity type (Epic or Story)
                        update_method = getattr(self.db_service, f"update_{item.get('type', 'item')}", None)
                        if update_method:
                            updated = update_method(item["id"], update_data)
                            if updated:
                                stats["items_updated"] += 1
                            else:
                                logger.warning(f"无法更新本地 {item.get('type')} 状态: {item.get('name')}")
                                stats["errors"] += 1
                        else:
                            logger.error(f"数据库服务缺少更新方法: update_{item.get('type')}")
                            stats["errors"] += 1
                    else:
                        logger.warning(f"在 GitHub 上未找到本地 {item.get('type')} '{item.get('name')}' 对应的 Issue #{github_issue_number}")
                        stats["errors"] += 1
                # else: logger.debug(f"Local item '{item.get('name')}' not linked to GitHub issue.")

            result["status"] = "success"
            result["code"] = 0
            # 优先使用title字段，然后是name字段
            roadmap_name = roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"
            result["message"] = f"从 GitHub 同步状态到路线图 '{roadmap_name}' 完成"
            result["data"] = {"roadmap_id": roadmap_id, "stats": stats}
            return result

        except Exception as e:
            logger.exception(f"从 GitHub 同步状态时出错 (Roadmap: {roadmap_id}): {e}")
            result["message"] = f"从 GitHub 同步状态错误: {e}"
            result["code"] = 500
            result["data"] = {"roadmap_id": roadmap_id, "stats": stats}
            return result

    def sync_from_github(self, repo_name: str, branch: str = "main", theme: Optional[str] = None, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从GitHub仓库同步数据到本地路线图

        Args:
            repo_name: GitHub仓库名称（格式：owner/repo）
            branch: 要同步的分支名称，默认为main
            theme: GitHub项目主题标签，用于筛选特定主题的问题
            roadmap_id: 路线图ID，不提供则使用活跃路线图或创建新路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        result = {"status": "error", "code": 1, "message": "", "data": None}

        # 验证参数
        if not repo_name or "/" not in repo_name:
            result["message"] = "无效的仓库名称，格式应为：所有者/仓库名"
            result["code"] = 400
            return result

        # 解析仓库信息
        owner, repo = repo_name.split("/", 1)

        # 创建临时API外观
        temp_api = GitHubApiFacade(token=self.github_token, owner=owner, repo=repo)

        # 初始化统计信息
        stats = {"milestones_imported": 0, "issues_imported": 0, "tasks_created": 0, "errors": 0}

        # Mock mode handling
        if self._mock_mode:
            logger.info(f"[MOCK] 从GitHub仓库 {repo_name} 同步数据")
            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"模拟从 GitHub 仓库 {repo_name} 同步数据成功"
            result["data"] = {
                "note": "使用模拟数据",
                "roadmap_id": roadmap_id or "new_roadmap",
                "stats": {
                    "milestones_imported": 2,
                    "issues_imported": 5,
                    "tasks_created": 10,
                },
            }
            return result

        try:
            # 1. 获取GitHub仓库信息
            repo_info = temp_api.get_repo_info()
            if not repo_info:
                result["message"] = f"无法获取仓库信息: {repo_name}"
                result["code"] = 404
                return result

            # 2. 创建或获取本地路线图
            if not roadmap_id:
                # 创建新路线图
                new_roadmap = self.roadmap_service.create_roadmap(
                    name=f"从GitHub导入: {repo_info.get('name', repo_name)}", description=repo_info.get("description", f"从GitHub仓库 {repo_name} 导入的路线图")
                )
                if not new_roadmap.get("success", False):
                    result["message"] = "创建路线图失败"
                    result["code"] = 500
                    return result
                roadmap_id = new_roadmap.get("roadmap_id")

            # 3. 获取里程碑数据
            milestones = temp_api.list_milestones()
            milestone_map = {}  # GitHub里程碑编号到本地里程碑ID的映射

            for ms in milestones:
                milestone_data = {
                    "name": ms.get("title"),
                    "description": ms.get("description", ""),
                    "status": "completed" if ms.get("state") == "closed" else "in_progress",
                    "due_date": ms.get("due_on", "").split("T")[0] if ms.get("due_on") else None,
                    "roadmap_id": roadmap_id,
                }

                # 创建里程碑
                new_milestone = self.roadmap_service.create_milestone(roadmap_id, milestone_data)
                if new_milestone.get("success", False):
                    milestone_map[ms.get("number")] = new_milestone.get("milestone_id")
                    stats["milestones_imported"] += 1
                else:
                    stats["errors"] += 1

            # 4. 获取问题数据（可选过滤主题标签）
            issues_params = {"state": "all"}
            if theme:
                issues_params["labels"] = theme

            issues = temp_api.list_issues(params=issues_params)

            for issue in issues:
                # 跳过拉取请求
                if "pull_request" in issue:
                    continue

                # 确定类型（Epic或Story）
                is_epic = any(label.get("name") == "epic" for label in issue.get("labels", []))

                # 获取里程碑ID
                milestone_id = None
                if issue.get("milestone"):
                    milestone_number = issue.get("milestone", {}).get("number")
                    milestone_id = milestone_map.get(milestone_number)

                # 确定状态
                status = "completed" if issue.get("state") == "closed" else "in_progress"
                if any(label.get("name") == "blocked" for label in issue.get("labels", [])):
                    status = "blocked"

                # 提取标签
                labels = [label.get("name") for label in issue.get("labels", [])]

                # 创建Epic或Story
                item_data = {
                    "name": issue.get("title"),
                    "description": issue.get("body", ""),
                    "type": "epic" if is_epic else "story",
                    "status": status,
                    "milestone_id": milestone_id,
                    "labels": labels,
                    "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
                    "roadmap_id": roadmap_id,
                    "github_url": issue.get("html_url"),
                    "github_number": issue.get("number"),
                }

                # 创建条目
                if is_epic:
                    new_item = self.roadmap_service.create_epic(roadmap_id, item_data)
                else:
                    new_item = self.roadmap_service.create_story(roadmap_id, item_data)

                if new_item.get("success", False):
                    stats["issues_imported"] += 1
                else:
                    stats["errors"] += 1

            # 5. 设置为活动路线图
            self.roadmap_service.set_active_roadmap(roadmap_id)

            result["status"] = "success"
            result["code"] = 0
            # 优先使用title字段，然后是name字段
            roadmap_name = roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"
            result["message"] = f"从GitHub仓库 {repo_name} 同步数据成功"
            result["data"] = {"roadmap_id": roadmap_id, "stats": stats}
            return result

        except Exception as e:
            logger.exception(f"从GitHub仓库 {repo_name} 同步数据时出错: {e}")
            result["message"] = f"从GitHub同步错误: {e}"
            result["code"] = 500
            result["data"] = {"roadmap_id": roadmap_id, "stats": stats}
            return result

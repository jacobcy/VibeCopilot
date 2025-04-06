"""
GitHub同步服务模块

提供路线图与GitHub的同步功能，连接路线图数据与GitHub项目。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from adapters.github_project.api.issues_client import GitHubIssuesClient
from adapters.github_project.api.projects_client import GitHubProjectsClient

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """GitHub同步服务，提供路线图与GitHub的同步功能"""

    def __init__(self, service):
        """
        初始化GitHub同步服务

        Args:
            service: 路线图服务
        """
        self.service = service

        # GitHub API配置
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.github_owner = os.environ.get("GITHUB_OWNER", "")
        self.github_repo = os.environ.get("GITHUB_REPO", "")

        # 初始化API客户端
        self.projects_client = GitHubProjectsClient(token=self.github_token)
        self.issues_client = GitHubIssuesClient(token=self.github_token)

        # 缓存项目数据
        self._project_cache = {}
        self._milestone_cache = {}

        # 调试模式设置
        self._debug_mode = os.environ.get("DEBUG_SYNC", "false").lower() == "true"
        self._mock_mode = os.environ.get("MOCK_SYNC", "false").lower() == "true"

    def sync_roadmap_to_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        同步路线图到GitHub

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        roadmap_id = roadmap_id or self.service.active_roadmap_id

        # 检查GitHub配置
        if not self._check_github_config():
            return {
                "success": False,
                "error": "GitHub配置不完整，请设置GITHUB_TOKEN、GITHUB_OWNER和GITHUB_REPO环境变量",
            }

        # 检查路线图是否存在
        try:
            roadmap = self.service.get_roadmap(roadmap_id)
            if not roadmap:
                logger.error(f"未找到路线图: {roadmap_id}")
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

            # 如果开启模拟模式，返回模拟数据
            if self._mock_mode:
                logger.info(f"模拟同步路线图到GitHub: {roadmap_id}")
                return {
                    "success": True,
                    "roadmap_id": roadmap_id,
                    "roadmap_name": roadmap.get("name"),
                    "github_project": f"https://github.com/{self.github_owner}/{self.github_repo}/projects/1",
                    "stats": {
                        "milestones_synced": 3,
                        "epics_synced": 5,
                        "issues_created": 2,
                        "issues_updated": 3,
                    },
                    "note": "使用模拟数据",
                }

            # 获取路线图的里程碑和任务
            try:
                milestones = self.service.get_milestones(roadmap_id)
                epics = self.service.get_epics(roadmap_id)
            except Exception as e:
                logger.error(f"获取路线图数据时出错: {str(e)}")
                return {"success": False, "error": f"获取路线图数据失败: {str(e)}"}

            # 同步到GitHub项目
            try:
                result = self._sync_data_to_github(roadmap, milestones, epics)
                return {
                    "success": True,
                    "roadmap_id": roadmap_id,
                    "roadmap_name": roadmap.get("name"),
                    "github_project": result.get("project_url", ""),
                    "stats": {
                        "milestones_synced": len(milestones),
                        "epics_synced": len(epics),
                        "issues_created": result.get("issues_created", 0),
                        "issues_updated": result.get("issues_updated", 0),
                    },
                }
            except Exception as e:
                logger.exception(f"同步到GitHub时出错: {str(e)}")
                return {"success": False, "error": f"同步错误: {str(e)}", "roadmap_id": roadmap_id}

        except Exception as e:
            logger.error(f"同步到GitHub时发生错误: {str(e)}")
            return {"success": False, "error": f"同步错误: {str(e)}"}

    def sync_status_from_github(self, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
        """
        从GitHub同步状态到路线图

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 同步结果
        """
        roadmap_id = roadmap_id or self.service.active_roadmap_id

        # 检查GitHub配置
        if not self._check_github_config():
            return {
                "success": False,
                "error": "GitHub配置不完整，请设置GITHUB_TOKEN、GITHUB_OWNER和GITHUB_REPO环境变量",
            }

        # 如果开启模拟模式，返回模拟数据
        if self._mock_mode:
            logger.info(f"模拟从GitHub同步状态到路线图: {roadmap_id}")
            return {
                "success": True,
                "roadmap_id": roadmap_id,
                "roadmap_name": "路线图",
                "stats": {
                    "tasks_updated": 3,
                    "milestones_updated": 1,
                },
                "note": "使用模拟数据",
            }

        # 检查路线图是否存在
        try:
            roadmap = self.service.get_roadmap(roadmap_id)
            if not roadmap:
                logger.error(f"未找到路线图: {roadmap_id}")
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

            # 从GitHub获取状态并更新到数据库
            try:
                result = self._fetch_status_from_github(roadmap_id)
                return {
                    "success": True,
                    "roadmap_id": roadmap_id,
                    "roadmap_name": roadmap.get("name"),
                    "stats": {
                        "tasks_updated": result.get("tasks_updated", 0),
                        "milestones_updated": result.get("milestones_updated", 0),
                    },
                }
            except Exception as e:
                logger.exception(f"从GitHub同步状态时出错: {str(e)}")
                return {"success": False, "error": f"同步错误: {str(e)}", "roadmap_id": roadmap_id}

        except Exception as e:
            logger.error(f"从GitHub同步状态时发生错误: {str(e)}")
            return {"success": False, "error": f"同步错误: {str(e)}", "roadmap_id": roadmap_id}

    def _check_github_config(self) -> bool:
        """
        检查GitHub配置是否完整

        Returns:
            bool: 配置是否完整
        """
        return all([self.github_token, self.github_owner, self.github_repo])

    def _get_or_create_project(self, roadmap: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        获取或创建GitHub项目

        Args:
            roadmap: 路线图数据

        Returns:
            Tuple[Dict[str, Any], bool]: 项目数据和是否新创建的标志
        """
        # 检查缓存
        roadmap_id = roadmap.get("id")
        if roadmap_id in self._project_cache:
            return self._project_cache[roadmap_id], False

        # 获取仓库的项目列表
        projects = self.projects_client.get_projects(self.github_owner, self.github_repo)

        # 查找匹配路线图名称的项目
        roadmap_name = roadmap.get("name", "路线图")
        for project in projects:
            if project.get("name") == roadmap_name:
                self._project_cache[roadmap_id] = project
                return project, False

        # 如果没有找到，创建新项目
        project_data = {
            "name": roadmap_name,
            "body": roadmap.get("description", f"{roadmap_name}项目跟踪"),
        }
        new_project = self.projects_client.create_project(
            self.github_owner, self.github_repo, project_data
        )

        # 创建默认列
        self._project_cache[roadmap_id] = new_project
        return new_project, True

    def _get_or_create_milestone(self, milestone: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        获取或创建GitHub里程碑

        Args:
            milestone: 里程碑数据

        Returns:
            Tuple[Dict[str, Any], bool]: 里程碑数据和是否新创建的标志
        """
        # 检查缓存
        milestone_id = milestone.get("id")
        if milestone_id in self._milestone_cache:
            return self._milestone_cache[milestone_id], False

        # 获取仓库的里程碑列表
        milestones = self.issues_client.get_milestones(self.github_owner, self.github_repo)

        # 查找匹配里程碑标题的里程碑
        milestone_title = milestone.get("name", f"M{milestone.get('id', '')}")
        for gh_milestone in milestones:
            if gh_milestone.get("title") == milestone_title:
                self._milestone_cache[milestone_id] = gh_milestone
                return gh_milestone, False

        # 如果没有找到，创建新里程碑
        milestone_data = {
            "title": milestone_title,
            "state": "open",
            "description": milestone.get("description", ""),
            "due_on": milestone.get("due_date", None),
        }

        new_milestone = self.issues_client.create_milestone(
            self.github_owner, self.github_repo, **milestone_data
        )

        self._milestone_cache[milestone_id] = new_milestone
        return new_milestone, True

    def _sync_data_to_github(
        self, roadmap: Dict[str, Any], milestones: List[Dict[str, Any]], epics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        将数据同步到GitHub

        Args:
            roadmap: 路线图数据
            milestones: 里程碑列表
            epics: Epic列表

        Returns:
            Dict[str, Any]: 同步结果
        """
        # 获取或创建项目
        project, project_created = self._get_or_create_project(roadmap)
        project_url = f"https://github.com/{self.github_owner}/{self.github_repo}/projects/{project.get('number')}"

        # 同步里程碑
        milestone_map = {}
        for milestone in milestones:
            gh_milestone, milestone_created = self._get_or_create_milestone(milestone)
            milestone_map[milestone.get("id")] = gh_milestone

        # 同步Epic和任务
        issues_created = 0
        issues_updated = 0

        # 获取现有issues
        existing_issues = self.issues_client.get_issues(
            self.github_owner, self.github_repo, state="all"
        )
        issue_map = {issue.get("title"): issue for issue in existing_issues}

        # 同步每个Epic
        for epic in epics:
            epic_title = epic.get("name", f"Epic-{epic.get('id', '')}")
            milestone_id = epic.get("milestone_id")

            # 准备issue数据
            issue_data = {
                "title": epic_title,
                "body": epic.get("description", ""),
                "labels": ["epic"],
            }

            # 添加里程碑
            if milestone_id and milestone_id in milestone_map:
                issue_data["milestone"] = milestone_map[milestone_id].get("number")

            # 检查是否存在
            if epic_title in issue_map:
                # 更新现有issue
                existing_issue = issue_map[epic_title]
                issue_number = existing_issue.get("number")

                self.issues_client.update_issue(
                    self.github_owner, self.github_repo, issue_number, issue_data
                )
                issues_updated += 1
            else:
                # 创建新issue
                new_issue = self.issues_client.create_issue(
                    self.github_owner, self.github_repo, issue_data
                )
                issues_created += 1

        return {
            "project_url": project_url,
            "issues_created": issues_created,
            "issues_updated": issues_updated,
        }

    def _fetch_status_from_github(self, roadmap_id: str) -> Dict[str, Any]:
        """
        从GitHub获取状态更新

        Args:
            roadmap_id: 路线图ID

        Returns:
            Dict[str, Any]: 同步结果
        """
        # 获取GitHub issues
        issues = self.issues_client.get_issues(self.github_owner, self.github_repo, state="all")

        # 获取路线图的Epic
        epics = self.service.get_epics(roadmap_id)
        epic_map = {epic.get("name"): epic for epic in epics}

        # 同步状态
        tasks_updated = 0
        milestones_updated = 0

        # 更新每个Epic的状态
        for issue in issues:
            issue_title = issue.get("title", "")
            if issue_title in epic_map:
                epic = epic_map[issue_title]

                # 从issue状态映射到Epic状态
                issue_state = issue.get("state")
                epic_status = "in_progress"

                if issue_state == "closed":
                    epic_status = "completed"
                elif len(issue.get("labels", [])) > 0:
                    for label in issue.get("labels", []):
                        if label.get("name") == "blocked":
                            epic_status = "blocked"
                            break

                # 更新Epic状态
                if epic.get("status") != epic_status:
                    # 使用更新元素状态的方法
                    self.service.update_roadmap_status(
                        element_id=epic.get("id"),
                        element_type="epic",
                        status=epic_status,
                        roadmap_id=roadmap_id,
                    )
                    tasks_updated += 1

        return {"tasks_updated": tasks_updated, "milestones_updated": milestones_updated}

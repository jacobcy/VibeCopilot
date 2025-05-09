"""
GitHub API Facade Module

Provides a simplified interface for interacting with GitHub Projects and Issues APIs
relevant to roadmap synchronization.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import requests  # 导入requests模块用于异常处理

# 直接从实际模块导入
from src.sync.clients.issues_client import GitHubIssuesClient
from src.sync.clients.projects_client import GitHubProjectsClient
from src.sync.clients.projects_items import GitHubProjectItemsClient

logger = logging.getLogger(__name__)


class GitHubApiFacade:
    """Facade for GitHub Projects and Issues API interactions."""

    def __init__(self, token: str):
        if not token:
            raise ValueError("GitHub token must be provided.")

        self.token = token
        self.projects_client = GitHubProjectsClient(token=self.token)
        self.issues_client = GitHubIssuesClient(token=self.token)
        self.project_items_client = GitHubProjectItemsClient(token=self.token)

        # Simple in-memory cache for frequently accessed items during a sync operation
        self._project_cache: Dict[str, Dict] = {}  # Cache by owner/repo/name -> project data
        self._milestone_cache: Dict[str, Dict] = {}  # Cache by owner/repo/local_id -> gh milestone data
        self._issue_cache: Dict[str, Dict] = {}  # Cache by owner/repo/local_id -> gh issue data

    def clear_cache(self):
        """Clears the internal cache."""
        self._project_cache = {}
        self._milestone_cache = {}
        self._issue_cache = {}

    def get_or_create_project(self, owner: str, repo: str, name: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Gets a GitHub project by name for a specific repo, or creates it if not found."""
        cache_key = f"{owner}/{repo}/{name}"
        if cache_key in self._project_cache:
            return self._project_cache[cache_key]

        try:
            projects = self.projects_client.get_projects(owner, repo)
            for project in projects:
                if project.get("title") == name:
                    self._project_cache[cache_key] = project
                    logger.info(f"Found existing GitHub project: '{name}' in {owner}/{repo} (ID: {project.get('id')})")
                    return project

            logger.info(f"GitHub project '{name}' not found in {owner}/{repo}. Creating...")
            new_project = self.projects_client.create_project(owner, repo, name, body or f"{name} - Project Tracking")
            if new_project:
                self._project_cache[cache_key] = new_project
            return new_project
        except Exception as e:
            logger.error(f"Error getting or creating GitHub project '{name}' in {owner}/{repo}: {e}", exc_info=True)
            return None

    def get_or_create_milestone(
        self,
        owner: str,
        repo: str,
        title: str,
        local_id: str,
        description: Optional[str] = None,
        state: str = "open",
        due_on: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Gets a GitHub milestone by title for a specific repo, or creates it if not found."""
        cache_key = f"{owner}/{repo}/{local_id}"
        if cache_key in self._milestone_cache:
            return self._milestone_cache[cache_key]

        try:
            milestones = self.issues_client.get_milestones(owner, repo)
            for gh_milestone in milestones:
                if gh_milestone.get("title") == title:
                    self._milestone_cache[cache_key] = gh_milestone
                    logger.info(f"Found existing GitHub milestone: '{title}' in {owner}/{repo} (ID: {gh_milestone.get('id')})")
                    return gh_milestone

            logger.info(f"GitHub milestone '{title}' not found in {owner}/{repo}. Creating...")
            milestone_data = {
                "title": title,
                "state": state,
                "description": description or "",
            }
            if due_on:
                milestone_data["due_on"] = due_on

            try:
                new_milestone = self.issues_client.create_milestone(
                    owner=owner,
                    repo=repo,
                    title=milestone_data["title"],
                    state=milestone_data.get("state", "open"),
                    description=milestone_data.get("description"),
                    due_on=milestone_data.get("due_on"),
                )
                if new_milestone:
                    self._milestone_cache[cache_key] = new_milestone
                return new_milestone
            except Exception as e:
                # 检查是否是422错误且是"已存在"错误
                # 这里修改为检查异常对象的结构和属性
                is_already_exists = False

                # 检查是否为 HTTPError 且状态码为 422
                if isinstance(e, requests.exceptions.HTTPError) and hasattr(e, "response") and e.response.status_code == 422:
                    try:
                        # 尝试获取错误详情
                        error_details = e.response.json()
                        errors = error_details.get("errors", [])
                        # 检查是否存在 already_exists 错误码
                        for error in errors:
                            if error.get("code") == "already_exists":
                                is_already_exists = True
                                break
                    except (ValueError, KeyError, AttributeError):
                        # 解析错误详情失败时，记录但继续处理
                        logger.warning(f"无法解析GitHub API 422错误详情: {e}")

                if is_already_exists:
                    # 已存在错误处理 - 重新获取并查找已存在的里程碑
                    logger.warning(f"里程碑 '{title}' 已存在。尝试重新获取...")
                    try:
                        # 重新获取所有里程碑
                        refreshed_milestones = self.issues_client.get_milestones(owner, repo)
                        # 查找匹配标题的里程碑
                        for gh_milestone in refreshed_milestones:
                            if gh_milestone.get("title") == title:
                                logger.info(f"找到已存在的里程碑 '{title}' (编号: {gh_milestone.get('number')})!")
                                self._milestone_cache[cache_key] = gh_milestone  # 更新缓存
                                return gh_milestone

                        # 仍未找到 (极少情况)
                        logger.error(f"里程碑 '{title}' 应该存在，但无法找到。可能是API延迟或其他问题。")
                        # 作为最后的补救措施，可能可以查询特定标题的里程碑
                        return None
                    except Exception as refresh_error:
                        logger.error(f"重新获取里程碑时出错: {refresh_error}")
                        return None
                else:
                    # 其他错误 - 记录并处理
                    logger.error(f"创建里程碑 '{title}' 时出错: {e}")
                    return None
        except Exception as e:
            logger.error(f"获取或创建 GitHub 里程碑 '{title}' 在 {owner}/{repo} 时出错: {e}", exc_info=True)
            return None

    def get_milestone_by_title(self, owner: str, repo: str, title: str) -> Optional[Dict[str, Any]]:
        """通过标题查找 GitHub 里程碑"""
        try:
            # 获取所有状态的里程碑，以确保能找到已存在的 closed 状态的里程碑
            all_milestones = self.issues_client.get_milestones(owner, repo, state="all")
            for milestone in all_milestones:
                if milestone.get("title") == title:
                    logger.info(f"找到标题为 '{title}' 的里程碑 (Number: {milestone.get('number')})")
                    return milestone
            logger.info(f"未找到标题为 '{title}' 的里程碑")
            return None
        except Exception as e:
            logger.error(f"通过标题 '{title}' 查找里程碑时出错: {e}", exc_info=True)
            return None

    def update_milestone(self, owner: str, repo: str, milestone_number: int, **kwargs) -> Optional[Dict[str, Any]]:
        """更新现有的 GitHub 里程碑"""
        try:
            # 假设 self.issues_client 有 update_milestone 方法
            updated_milestone = self.issues_client.update_milestone(owner, repo, milestone_number, **kwargs)
            if updated_milestone:
                logger.info(f"成功更新里程碑 #{milestone_number}")
            return updated_milestone
        except AttributeError:
            logger.error(f"底层 issues_client 没有 update_milestone 方法！")
            raise NotImplementedError("GitHubIssuesClient 需要实现 update_milestone 方法。")
        except Exception as e:
            logger.error(f"更新里程碑 #{milestone_number} 时出错: {e}", exc_info=True)
            return None

    def find_issue_by_title(self, owner: str, repo: str, title_part: str) -> Optional[Dict[str, Any]]:
        """Finds the first open GitHub issue containing a specific title part in a repo."""
        try:
            # 不使用search_issues，改用get_issues并在本地过滤
            issues = self.issues_client.get_issues(owner, repo, state="open")

            # 在本地过滤包含title_part的issue
            matching_issues = []
            for issue in issues:
                issue_title = issue.get("title", "")
                if title_part.lower() in issue_title.lower():
                    matching_issues.append(issue)

            if matching_issues:
                logger.info(f"找到匹配标题的issue: '{title_part}' in {owner}/{repo}: ID {matching_issues[0].get('number')}")
                return matching_issues[0]

            logger.info(f"未找到匹配标题的issue: '{title_part}' in {owner}/{repo}")
            return None
        except Exception as e:
            logger.error(
                f"Error searching for GitHub issue with title part '{title_part}' in {owner}/{repo}: {e}",
                exc_info=True,
            )
            return None

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建一个GitHub issue。

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            title: issue标题
            body: issue正文
            assignees: 分配者列表
            milestone: 里程碑ID
            labels: 标签列表

        Returns:
            Optional[Dict[str, Any]]: 创建的issue数据或None
        """
        try:
            new_issue = self.issues_client.create_issue(owner, repo, title, body=body, assignees=assignees, milestone=milestone, labels=labels)
            logger.info(f"创建GitHub issue '{title}' 在 {owner}/{repo} (ID: {new_issue.get('number') if new_issue else 'N/A'})")
            return new_issue
        except Exception as e:
            logger.error(f"创建GitHub issue '{title}' 在 {owner}/{repo} 时出错: {e}", exc_info=True)
            return None

    def update_issue(self, owner: str, repo: str, issue_number: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates an existing GitHub issue in a specific repo."""
        try:
            # 不直接传递 update_data 字典，而是解包为单独的参数
            title = update_data.get("title")
            body = update_data.get("body")
            state = update_data.get("state")
            assignees = update_data.get("assignees")
            milestone = update_data.get("milestone")
            labels = update_data.get("labels")

            # 记录详细的参数信息
            logger.debug(
                f"Updating GitHub issue #{issue_number} in {owner}/{repo} with extracted params: "
                f"title={title}, body=truncated, state={state}, "
                f"assignees={assignees}, milestone={milestone}, labels={labels}"
            )

            # 调用客户端方法时传递解包后的各个参数
            updated_issue = self.issues_client.update_issue(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                title=title,
                body=body,
                state=state,
                assignees=assignees,
                milestone=milestone,
                labels=labels,
            )

            logger.info(f"Updated GitHub issue #{issue_number} in {owner}/{repo}")
            return updated_issue
        except Exception as e:
            # Enhanced error logging for 422 errors
            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    f"Error updating GitHub issue #{issue_number} in {owner}/{repo}. Status: {e.response.status_code}. URL: {e.response.url}"
                )
                if e.response.status_code == 422:
                    try:
                        error_details = e.response.json()
                        logger.error(f"GitHub API 422 Error Details for Issue #{issue_number}: {error_details}")
                    except ValueError:
                        logger.error(f"GitHub API 422 Response (non-JSON): {e.response.text}")
            else:
                logger.error(f"Error updating GitHub issue #{issue_number} in {owner}/{repo}: {e}", exc_info=True)
            return None

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Gets details for a specific GitHub issue in a specific repo."""
        try:
            issue = self.issues_client.get_issue(owner, repo, issue_number)
            return issue
        except Exception as e:
            logger.error(f"Error getting GitHub issue #{issue_number} in {owner}/{repo}: {e}", exc_info=True)
            return None

    def get_issues_by_milestone(self, owner: str, repo: str, milestone_number: int, state: str = "all") -> List[Dict[str, Any]]:
        """Gets all issues associated with a specific milestone in a specific repo."""
        try:
            issues = self.issues_client.get_issues_for_milestone(owner, repo, milestone_number, state=state)
            return issues
        except Exception as e:
            logger.error(f"Error getting issues for GitHub milestone #{milestone_number} in {owner}/{repo}: {e}", exc_info=True)
            return []

    def get_project_by_number(self, owner: str, repo: str, project_identifier: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        通过项目编号或Node ID获取GitHub项目

        Args:
            owner: GitHub仓库所有者
            repo: GitHub仓库名称
            project_identifier: 项目编号(int)或Node ID(str)

        Returns:
            Optional[Dict[str, Any]]: 项目信息或None
        """
        try:
            # 判断标识符类型
            is_node_id = isinstance(project_identifier, str) and (project_identifier.startswith("PVT_") or project_identifier.startswith("PVTPROJ_"))

            logger.info(f"获取GitHub项目，标识符: {project_identifier}，类型: {'Node ID' if is_node_id else '项目编号'}")

            if is_node_id:
                # 处理Node ID - 获取所有项目并查找匹配项
                projects = self.projects_client.get_projects(owner, repo)
                for project in projects:
                    if project.get("id") == project_identifier:
                        logger.info(f"通过Node ID {project_identifier} 找到GitHub项目: {project.get('title')}")
                        return project

                # 如果直接查找失败，尝试通过GraphQL查询
                # 这部分可以根据需要实现具体逻辑
                logger.warning(f"未能通过直接列表查找找到Node ID为 {project_identifier} 的项目")
                return None
            else:
                # 处理项目编号
                # 确保转换为整数
                try:
                    project_number_int = int(project_identifier)
                except (ValueError, TypeError):
                    logger.error(f"项目编号转换失败: {project_identifier}")
                    raise ValueError(f"无效的项目编号: {project_identifier}")

                # 首先尝试使用repository.projectV2路径查询
                try:
                    project = self.projects_client.get_project_v2(owner, repo, project_number_int)
                    if project:
                        logger.info(f"通过repository.projectV2找到GitHub项目 (#{project_number_int}): {project.get('title')}")
                        return project
                except Exception as repository_error:
                    logger.warning(f"通过repository.projectV2获取项目失败: {repository_error}")

                # 如果失败，尝试使用viewer.projectV2路径
                logger.info(f"尝试通过viewer.projectV2获取项目 #{project_number_int}")
                project = self.projects_client.get_project_v2_by_viewer(project_number_int)
                if project:
                    logger.info(f"通过viewer.projectV2找到GitHub项目 (#{project_number_int}): {project.get('title')}")
                else:
                    logger.warning(f"未找到GitHub项目 (#{project_number_int})")
                return project
        except Exception as e:
            logger.error(f"获取GitHub项目出错: {e}", exc_info=True)
            return None

    def get_milestones(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Gets all open milestones for a specific repo."""
        try:
            return self.issues_client.get_milestones(owner, repo)
        except Exception as e:
            logger.error(f"Error getting milestones for {owner}/{repo}: {e}", exc_info=True)
            return []

    def get_issues(self, owner: str, repo: str, state: str = "all") -> List[Dict[str, Any]]:
        """Gets all issues for a specific repo in the specified state."""
        try:
            return self.issues_client.get_issues(owner, repo, state=state)
        except Exception as e:
            logger.error(f"Error getting issues for {owner}/{repo}: {e}", exc_info=True)
            return []

    def get_issues_for_milestone(self, owner: str, repo: str, milestone_number: int, state: str = "all") -> List[Dict[str, Any]]:
        """获取特定里程碑的所有问题

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            milestone_number: 里程碑编号
            state: 问题状态过滤器

        Returns:
            List[Dict[str, Any]]: 问题列表
        """
        try:
            params = {"milestone": str(milestone_number), "state": state}
            return self.issues_client._core.get_issues(owner, repo, state=state, params=params)
        except Exception as e:
            logger.error(f"获取里程碑 #{milestone_number} 的问题列表在 {owner}/{repo} 时出错: {e}", exc_info=True)
            return []

    # Add methods for adding issues to projects if needed
    # def add_issue_to_project(self, owner: str, repo: str, project_id: int, issue_node_id: str) -> bool:
    #     ...

    # def get_project_columns(self, owner: str, repo: str, project_id: int) -> List[Dict]:
    #     ...

    def get_all_project_items_by_node_id(self, project_node_id: str) -> List[Dict[str, Any]]:
        """
        通过项目Node ID获取所有项目条目

        Args:
            project_node_id: 项目Node ID

        Returns:
            List[Dict[str, Any]]: 项目条目列表
        """
        try:
            # 使用ProjectItemsClient获取项目条目
            items = self.project_items_client.get_project_items_by_node_id(project_node_id)
            if items:
                logger.info(f"找到 {len(items)} 个项目条目")
            else:
                logger.warning(f"未找到项目条目")
            return items or []
        except Exception as e:
            logger.error(f"通过Node ID获取项目条目时出错: {e}", exc_info=True)
            return []

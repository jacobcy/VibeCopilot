#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Issues API客户端模块.

提供与GitHub Issues API交互的整合功能，组合多个专门的Issue子模块客户端。
"""

import logging
from typing import Any, Dict, List, Optional

from .github_client import GitHubClient
from .issues.comments import GitHubIssueCommentsClient
from .issues.core import GitHubIssuesCoreClient
from .issues.labels import GitHubIssueLabelsClient
from .issues.milestones import GitHubIssueMilestonesClient


class GitHubIssuesClient(GitHubClient):
    """GitHub Issues API客户端.

    集成多个专门的Issues子客户端，提供完整的Issues管理功能。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

        # 初始化子客户端
        self._core = GitHubIssuesCoreClient(token, base_url)
        self._comments = GitHubIssueCommentsClient(token, base_url)
        self._labels = GitHubIssueLabelsClient(token, base_url)
        self._milestones = GitHubIssueMilestonesClient(token, base_url)

    # 核心Issue方法 (从Core子客户端)
    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        since: Optional[str] = None,
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """获取仓库的问题列表."""
        return self._core.get_issues(owner, repo, state, labels, since, per_page, page)

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """获取特定问题的详细信息."""
        return self._core.get_issue(owner, repo, issue_number)

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
        """创建新问题."""
        return self._core.create_issue(owner, repo, title, body, assignees, milestone, labels)

    def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新问题."""
        return self._core.update_issue(
            owner, repo, issue_number, title, body, state, assignees, milestone, labels
        )

    # 评论方法 (从Comments子客户端)
    def add_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Optional[Dict[str, Any]]:
        """添加评论到问题."""
        return self._comments.add_comment(owner, repo, issue_number, body)

    def get_comments(
        self, owner: str, repo: str, issue_number: int, per_page: int = 100, page: int = 1
    ) -> List[Dict[str, Any]]:
        """获取问题的评论列表."""
        return self._comments.get_comments(owner, repo, issue_number, per_page, page)

    def update_comment(
        self, owner: str, repo: str, comment_id: int, body: str
    ) -> Optional[Dict[str, Any]]:
        """更新评论."""
        return self._comments.update_comment(owner, repo, comment_id, body)

    def delete_comment(self, owner: str, repo: str, comment_id: int) -> bool:
        """删除评论."""
        return self._comments.delete_comment(owner, repo, comment_id)

    # 标签方法 (从Labels子客户端)
    def add_labels(
        self, owner: str, repo: str, issue_number: int, labels: List[str]
    ) -> List[Dict[str, Any]]:
        """添加标签到问题."""
        return self._labels.add_labels(owner, repo, issue_number, labels)

    def remove_label(
        self, owner: str, repo: str, issue_number: int, label: str
    ) -> List[Dict[str, Any]]:
        """从问题中移除标签."""
        return self._labels.remove_label(owner, repo, issue_number, label)

    def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建标签."""
        return self._labels.create_label(owner, repo, name, color, description)

    def get_labels(
        self, owner: str, repo: str, per_page: int = 100, page: int = 1
    ) -> List[Dict[str, Any]]:
        """获取仓库的所有标签."""
        return self._labels.get_labels(owner, repo, per_page, page)

    def get_issue_labels(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """获取问题的标签."""
        return self._labels.get_issue_labels(owner, repo, issue_number)

    def update_label(
        self,
        owner: str,
        repo: str,
        name: str,
        new_name: Optional[str] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新标签."""
        return self._labels.update_label(owner, repo, name, new_name, color, description)

    def delete_label(self, owner: str, repo: str, name: str) -> bool:
        """删除标签."""
        return self._labels.delete_label(owner, repo, name)

    # 里程碑方法 (从Milestones子客户端)
    def create_milestone(
        self,
        owner: str,
        repo: str,
        title: str,
        state: str = "open",
        description: Optional[str] = None,
        due_on: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建里程碑."""
        return self._milestones.create_milestone(owner, repo, title, state, description, due_on)

    def get_milestones(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        sort: str = "due_on",
        direction: str = "asc",
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """获取里程碑列表."""
        return self._milestones.get_milestones(owner, repo, state, sort, direction, per_page, page)

    def get_milestone(
        self, owner: str, repo: str, milestone_number: int
    ) -> Optional[Dict[str, Any]]:
        """获取特定里程碑."""
        return self._milestones.get_milestone(owner, repo, milestone_number)

    def update_milestone(
        self,
        owner: str,
        repo: str,
        milestone_number: int,
        title: Optional[str] = None,
        state: Optional[str] = None,
        description: Optional[str] = None,
        due_on: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新里程碑."""
        return self._milestones.update_milestone(
            owner, repo, milestone_number, title, state, description, due_on
        )

    def delete_milestone(self, owner: str, repo: str, milestone_number: int) -> bool:
        """删除里程碑."""
        return self._milestones.delete_milestone(owner, repo, milestone_number)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues核心功能模块.

提供Issues基本操作，如获取、创建和更新Issue。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ...github_client import GitHubClient


class GitHubIssuesCoreClient(GitHubClient):
    """GitHub Issues核心功能客户端."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

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
        """获取仓库的问题列表.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            state: 问题状态（"open", "closed", "all"）
            labels: 标签筛选，逗号分隔的字符串
            since: ISO 8601格式的日期时间，仅返回此日期之后更新的问题
            per_page: 每页结果数
            page: 页码

        Returns:
            List[Dict[str, Any]]: 问题列表
        """
        endpoint = f"repos/{owner}/{repo}/issues"
        params = {
            "state": state,
            "per_page": per_page,
            "page": page,
        }

        if labels:
            params["labels"] = labels
        if since:
            params["since"] = since

        try:
            response = self.get(endpoint, params=params)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取问题列表失败: {e}")
            return []

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """获取特定问题的详细信息.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号

        Returns:
            Optional[Dict[str, Any]]: 问题详情
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
        try:
            return self.get(endpoint)
        except requests.HTTPError as e:
            self.logger.error(f"获取问题详情失败: {e}")
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
        """创建新问题.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            title: 问题标题
            body: 问题内容
            assignees: 指派人列表
            milestone: 里程碑ID
            labels: 标签列表

        Returns:
            Optional[Dict[str, Any]]: 创建的问题
        """
        endpoint = f"repos/{owner}/{repo}/issues"
        data: Dict[str, Any] = {"title": title}

        if body:
            data["body"] = body
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone
        if labels:
            data["labels"] = labels

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"创建问题失败: {e}")
            return None

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
        """更新问题.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号
            title: 新标题
            body: 新内容
            state: 新状态 ("open" or "closed")
            assignees: 新指派人列表
            milestone: 新里程碑ID
            labels: 新标签列表

        Returns:
            Optional[Dict[str, Any]]: 更新后的问题
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}"
        data: Dict[str, Any] = {}

        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        if assignees:
            data["assignees"] = assignees
        if milestone is not None:  # 允许设置为 0 来清除里程碑
            data["milestone"] = milestone
        if labels:
            data["labels"] = labels

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"更新问题失败: {e}")
            return None

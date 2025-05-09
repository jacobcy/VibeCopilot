#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues核心模块.

提供Issues相关的核心功能，如获取、创建和更新Issues。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ..github_client import GitHubClientBase


class GitHubIssuesCoreClient(GitHubClientBase):
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

        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if assignees is not None:
            data["assignees"] = assignees
        if milestone is not None:
            data["milestone"] = milestone
        if labels is not None:
            data["labels"] = labels

        if not data:
            self.logger.info(f"没有为 Issue #{issue_number} 提供更新数据，跳过 PATCH 请求。")
            return None

        self.logger.debug(f"发送 PATCH 请求到 {endpoint} 以更新 Issue #{issue_number}，数据: {data}")
        try:
            return self.patch(endpoint, json=data)
        except requests.HTTPError as e:
            if e.response is not None:
                self.logger.error(f"HTTPError 更新 Issue #{issue_number} in {owner}/{repo}. Status: {e.response.status_code}. URL: {e.response.url}")
                if e.response.status_code == 422:
                    try:
                        error_details = e.response.json()
                        self.logger.error(f"GitHub API 422 Error Details for updating Issue #{issue_number}: {error_details}")
                    except ValueError:
                        self.logger.error(f"GitHub API 422 Response (non-JSON) for updating Issue #{issue_number}: {e.response.text}")
            else:
                self.logger.error(f"HTTPError 更新 Issue #{issue_number} in {owner}/{repo} (no response object): {e}")
            return None
        except Exception as e:
            self.logger.error(f"更新 Issue #{issue_number} in {owner}/{repo} 时发生一般错误: {e}", exc_info=True)
            return None

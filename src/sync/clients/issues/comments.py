#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues评论模块.

提供Issues评论相关的功能，如添加和获取评论。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ..github_client import GitHubClientBase


class GitHubIssueCommentsClient(GitHubClientBase):
    """GitHub Issues评论客户端."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

    def add_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Optional[Dict[str, Any]]:
        """添加评论到问题.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号
            body: 评论内容

        Returns:
            Optional[Dict[str, Any]]: 创建的评论
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {"body": body}

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"添加评论失败: {e}")
            return None

    def get_comments(self, owner: str, repo: str, issue_number: int, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """获取问题的评论列表.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号
            per_page: 每页结果数
            page: 页码

        Returns:
            List[Dict[str, Any]]: 评论列表
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/comments"

        params = {
            "per_page": per_page,
            "page": page,
        }

        try:
            response = self.get(endpoint, params=params)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取评论失败: {e}")
            return []

    def update_comment(self, owner: str, repo: str, comment_id: int, body: str) -> Optional[Dict[str, Any]]:
        """更新评论.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            comment_id: 评论ID
            body: 新的评论内容

        Returns:
            Optional[Dict[str, Any]]: 更新后的评论
        """
        endpoint = f"repos/{owner}/{repo}/issues/comments/{comment_id}"
        data = {"body": body}

        try:
            return self.patch(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"更新评论失败: {e}")
            return None

    def delete_comment(self, owner: str, repo: str, comment_id: int) -> bool:
        """删除评论.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            comment_id: 评论ID

        Returns:
            bool: 是否成功删除
        """
        endpoint = f"repos/{owner}/{repo}/issues/comments/{comment_id}"

        try:
            self.delete(endpoint)
            return True
        except requests.HTTPError as e:
            self.logger.error(f"删除评论失败: {e}")
            return False

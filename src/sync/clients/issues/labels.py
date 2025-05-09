#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues标签模块.

提供Issues标签相关的功能，如添加、删除和获取标签。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ..github_client import GitHubClientBase


class GitHubIssueLabelsClient(GitHubClientBase):
    """GitHub Issues标签客户端."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

    def add_labels(self, owner: str, repo: str, issue_number: int, labels: List[str]) -> List[Dict[str, Any]]:
        """添加标签到问题.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号
            labels: 标签列表

        Returns:
            List[Dict[str, Any]]: 问题的所有标签
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/labels"
        data = {"labels": labels}

        try:
            response = self.post(endpoint, json=data)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"添加标签失败: {e}")
            return []

    def remove_label(self, owner: str, repo: str, issue_number: int, label: str) -> List[Dict[str, Any]]:
        """从问题中移除标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号
            label: 要移除的标签名称

        Returns:
            List[Dict[str, Any]]: 问题的剩余标签
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
        try:
            # 删除标签后，GitHub返回剩余的标签列表
            response = self.delete(endpoint)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"移除标签失败: {e}")
            return []

    def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            name: 标签名称
            color: 标签颜色 (十六进制，不含#前缀)
            description: 标签描述

        Returns:
            Optional[Dict[str, Any]]: 创建的标签
        """
        endpoint = f"repos/{owner}/{repo}/labels"
        data: Dict[str, Any] = {"name": name, "color": color}

        if description:
            data["description"] = description

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"创建标签失败: {e}")
            return None

    def get_labels(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """获取仓库的所有标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            per_page: 每页结果数
            page: 页码

        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        endpoint = f"repos/{owner}/{repo}/labels"

        params = {
            "per_page": per_page,
            "page": page,
        }

        try:
            response = self.get(endpoint, params=params)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取标签失败: {e}")
            return []

    def get_issue_labels(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """获取问题的标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号

        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/labels"

        try:
            response = self.get(endpoint)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取问题标签失败: {e}")
            return []

    def update_label(
        self,
        owner: str,
        repo: str,
        name: str,
        new_name: Optional[str] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            name: 标签名称
            new_name: 新的标签名称
            color: 新的标签颜色
            description: 新的标签描述

        Returns:
            Optional[Dict[str, Any]]: 更新后的标签
        """
        endpoint = f"repos/{owner}/{repo}/labels/{name}"
        data: Dict[str, Any] = {}

        if new_name:
            data["new_name"] = new_name
        if color:
            data["color"] = color
        if description:
            data["description"] = description

        if not data:
            self.logger.warning("未提供任何更新数据")
            return None

        try:
            return self.patch(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"更新标签失败: {e}")
            return None

    def delete_label(self, owner: str, repo: str, name: str) -> bool:
        """删除标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            name: 标签名称

        Returns:
            bool: 是否成功删除
        """
        endpoint = f"repos/{owner}/{repo}/labels/{name}"

        try:
            self.delete(endpoint)
            return True
        except requests.HTTPError as e:
            self.logger.error(f"删除标签失败: {e}")
            return False

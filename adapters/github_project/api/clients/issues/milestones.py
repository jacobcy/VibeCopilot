#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues里程碑模块.

提供Issues里程碑相关的功能，如创建、获取和更新里程碑。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ...github_client import GitHubClient


class GitHubIssueMilestonesClient(GitHubClient):
    """GitHub Issues里程碑客户端."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

    def create_milestone(
        self,
        owner: str,
        repo: str,
        title: str,
        state: str = "open",
        description: Optional[str] = None,
        due_on: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建里程碑.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            title: 里程碑标题
            state: 状态 ("open" or "closed")
            description: 描述
            due_on: 截止日期，ISO 8601格式

        Returns:
            Optional[Dict[str, Any]]: 创建的里程碑
        """
        endpoint = f"repos/{owner}/{repo}/milestones"
        data: Dict[str, Any] = {"title": title, "state": state}

        if description:
            data["description"] = description
        if due_on:
            data["due_on"] = due_on

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"创建里程碑失败: {e}")
            return None

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
        """获取里程碑列表.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            state: 状态 ("open", "closed", "all")
            sort: 排序字段 ("due_on", "completeness")
            direction: 排序方向 ("asc", "desc")
            per_page: 每页结果数
            page: 页码

        Returns:
            List[Dict[str, Any]]: 里程碑列表
        """
        endpoint = f"repos/{owner}/{repo}/milestones"
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
            "page": page,
        }

        try:
            response = self.get(endpoint, params=params)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取里程碑失败: {e}")
            return []

    def get_milestone(
        self, owner: str, repo: str, milestone_number: int
    ) -> Optional[Dict[str, Any]]:
        """获取特定里程碑.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            milestone_number: 里程碑编号

        Returns:
            Optional[Dict[str, Any]]: 里程碑详情
        """
        endpoint = f"repos/{owner}/{repo}/milestones/{milestone_number}"

        try:
            return self.get(endpoint)
        except requests.HTTPError as e:
            self.logger.error(f"获取里程碑详情失败: {e}")
            return None

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
        """更新里程碑.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            milestone_number: 里程碑编号
            title: 新标题
            state: 新状态 ("open" or "closed")
            description: 新描述
            due_on: 新截止日期，ISO 8601格式

        Returns:
            Optional[Dict[str, Any]]: 更新后的里程碑
        """
        endpoint = f"repos/{owner}/{repo}/milestones/{milestone_number}"
        data: Dict[str, Any] = {}

        if title:
            data["title"] = title
        if state:
            data["state"] = state
        if description:
            data["description"] = description
        if due_on:
            data["due_on"] = due_on

        if not data:
            self.logger.warning("未提供任何更新数据")
            return None

        try:
            return self.patch(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"更新里程碑失败: {e}")
            return None

    def delete_milestone(self, owner: str, repo: str, milestone_number: int) -> bool:
        """删除里程碑.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            milestone_number: 里程碑编号

        Returns:
            bool: 是否成功删除
        """
        endpoint = f"repos/{owner}/{repo}/milestones/{milestone_number}"

        try:
            self.delete(endpoint)
            return True
        except requests.HTTPError as e:
            self.logger.error(f"删除里程碑失败: {e}")
            return False

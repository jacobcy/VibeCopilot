#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues API客户端模块.

提供与GitHub Issues API交互的功能，包括问题创建、查询和管理。
"""

from typing import Any, Dict, List, Optional

import requests

from .github_client import GitHubClient


class GitHubIssuesClient(GitHubClient):
    """GitHub Issues API客户端."""

    def delete(self, endpoint: str, **kwargs: Any) -> Any:
        """发送DELETE请求到GitHub REST API.

        Args:
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self._make_rest_request("DELETE", endpoint, **kwargs)

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
            print(f"获取问题列表失败: {e}")
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
            print(f"获取问题详情失败: {e}")
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
            print(f"创建问题失败: {e}")
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
            print(f"更新问题失败: {e}")
            return None

    def add_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> Optional[Dict[str, Any]]:
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
            print(f"添加评论失败: {e}")
            return None

    def get_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """获取问题的评论列表.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            issue_number: 问题编号

        Returns:
            List[Dict[str, Any]]: 评论列表
        """
        endpoint = f"repos/{owner}/{repo}/issues/{issue_number}/comments"
        try:
            response = self.get(endpoint)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            print(f"获取评论失败: {e}")
            return []

    def add_labels(
        self, owner: str, repo: str, issue_number: int, labels: List[str]
    ) -> List[Dict[str, Any]]:
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
            print(f"添加标签失败: {e}")
            return []

    def remove_label(
        self, owner: str, repo: str, issue_number: int, label: str
    ) -> List[Dict[str, Any]]:
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
            print(f"移除标签失败: {e}")
            return []

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
            print(f"创建里程碑失败: {e}")
            return None

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
            print(f"创建标签失败: {e}")
            return None


if __name__ == "__main__":
    # 简单的使用示例
    client = GitHubIssuesClient()
    try:
        # 获取仓库问题列表
        owner = "octocat"
        repo = "hello-world"
        issues = client.get_issues(owner, repo, state="all", per_page=5)
        print(f"找到 {len(issues)} 个问题")

        # 如果有问题，获取第一个问题的详情
        if issues:
            issue_number = int(issues[0].get("number", 0))
            if issue_number > 0:
                issue = client.get_issue(owner, repo, issue_number)
                if issue:
                    print(f"问题标题: {issue.get('title')}")

                    # 获取问题评论
                    comments = client.get_comments(owner, repo, issue_number)
                    print(f"问题有 {len(comments)} 条评论")
    except Exception as e:
        print(f"示例失败: {e}")

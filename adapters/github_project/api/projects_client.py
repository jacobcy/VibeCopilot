#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Projects API客户端兼容层.

为保持向后兼容，此模块重定向到新的子模块。新代码应直接使用clients包。
"""

from typing import Any, Dict, List, Optional, Union

from .clients.projects_client import GitHubProjectsClient as BaseProjectsClient
from .clients.projects_fields import GitHubProjectFieldsClient
from .clients.projects_items import GitHubProjectItemsClient


class GitHubProjectsClient(BaseProjectsClient):
    """GitHub Projects API客户端兼容层.

    为保持向后兼容，此类组合了多个专门的客户端功能。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self._fields_client = GitHubProjectFieldsClient(token, base_url)
        self._items_client = GitHubProjectItemsClient(token, base_url)

    def get_project_fields(
        self, owner: str, repo: str, project_number: int
    ) -> List[Dict[str, Any]]:
        """获取项目字段.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号

        Returns:
            List[Dict[str, Any]]: 字段列表
        """
        return self._fields_client.get_project_fields(owner, repo, project_number)

    def add_issue_to_project(self, owner: str, repo: str, project_id: str, issue_id: str) -> bool:
        """将Issue添加到项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_id: 项目ID
            issue_id: Issue ID

        Returns:
            bool: 是否成功
        """
        return self._items_client.add_issue_to_project(owner, repo, project_id, issue_id)

    def update_project_item_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: Union[str, int, Dict[str, Any]],
    ) -> bool:
        """更新项目条目字段值.

        Args:
            project_id: 项目ID
            item_id: 条目ID
            field_id: 字段ID
            value: 字段值

        Returns:
            bool: 是否成功
        """
        return self._items_client.update_project_item_field(project_id, item_id, field_id, value)

    def add_field(
        self,
        project_id: str,
        name: str,
        field_type: str,
        options: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """向项目添加自定义字段.

        Args:
            project_id: 项目ID
            name: 字段名称
            field_type: 字段类型，如 "TEXT", "NUMBER", "DATE", "SINGLE_SELECT" 等
            options: 用于单选字段的选项列表，每个选项包含name和color

        Returns:
            Optional[str]: 创建的字段ID，如果失败则返回None
        """
        return self._fields_client.add_field(project_id, name, field_type, options)


# 对于需要支持的旧代码，可以保留这个仅用于说明的部分
if __name__ == "__main__":
    # 简单的使用示例
    client = GitHubProjectsClient()
    try:
        # 获取仓库项目列表
        owner = "octocat"
        repo = "hello-world"
        projects = client.get_projects(owner, repo)
        print(f"找到 {len(projects)} 个项目")

        # 如果有项目，获取第一个项目的字段
        if projects:
            project_number = int(projects[0].get("number", 0))
            if project_number > 0:
                fields = client.get_project_fields(owner, repo, project_number)
                print(f"项目有 {len(fields)} 个字段")
    except Exception as e:
        print(f"示例失败: {e}")

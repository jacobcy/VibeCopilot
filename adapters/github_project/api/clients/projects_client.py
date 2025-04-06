#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目管理核心模块.

提供与GitHub Projects相关的基本操作，如获取和创建项目。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from ..github_client import GitHubClient


class GitHubProjectsClient(GitHubClient):
    """GitHub Projects API客户端.

    专注于项目的基本操作，如获取和创建项目。更细粒度的功能委托给专门的客户端模块。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)

    def get_projects(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """获取仓库的所有项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        endpoint = f"repos/{owner}/{repo}/projects"
        try:
            response = self.get(endpoint)
            # 确保返回的是列表类型
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取项目失败: {e}")
            return []

    def get_project_v2(
        self, owner: str, repo: str, project_number: int
    ) -> Optional[Dict[str, Any]]:
        """使用GraphQL API获取项目v2数据.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号

        Returns:
            Optional[Dict[str, Any]]: 项目数据
        """
        query = """
        query($owner:String!, $repo:String!, $number:Int!) {
          repository(owner: $owner, name: $repo) {
            projectV2(number: $number) {
              title
              shortDescription
              url
              id
              closed
              createdAt
              updatedAt
              number
              items(first: 100) {
                nodes {
                  id
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field { ... on ProjectV2FieldCommon { name } }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field { ... on ProjectV2FieldCommon { name } }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field { ... on ProjectV2FieldCommon { name } }
                      }
                    }
                  }
                  content {
                    ... on Issue {
                      title
                      state
                      number
                      url
                      createdAt
                      updatedAt
                      labels(first: 10) {
                        nodes {
                          name
                          color
                        }
                      }
                      assignees(first: 5) {
                        nodes {
                          login
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo, "number": project_number}

        try:
            return self.graphql(query, variables)
        except Exception as e:
            self.logger.error(f"获取项目v2数据失败: {e}")
            return None

    def create_project(
        self, owner: str, repo: str, name: str, body: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """创建项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            name: 项目名称
            body: 项目描述

        Returns:
            Optional[Dict[str, Any]]: 创建的项目
        """
        endpoint = f"repos/{owner}/{repo}/projects"
        data: Dict[str, Any] = {"name": name}
        if body:
            data["body"] = body

        try:
            return self.post(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"创建项目失败: {e}")
            return None

    def get_organization_projects(self, org: str) -> List[Dict[str, Any]]:
        """获取组织的所有项目.

        Args:
            org: 组织名称

        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        endpoint = f"orgs/{org}/projects"
        try:
            response = self.get(endpoint)
            return response if isinstance(response, list) else []
        except requests.HTTPError as e:
            self.logger.error(f"获取组织项目失败: {e}")
            return []

    def update_project(
        self,
        owner: str,
        repo: str,
        project_id: int,
        name: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_id: 项目ID
            name: 新项目名称
            body: 新项目描述
            state: 新项目状态 ("open" 或 "closed")

        Returns:
            Optional[Dict[str, Any]]: 更新后的项目
        """
        endpoint = f"repos/{owner}/{repo}/projects/{project_id}"
        data: Dict[str, Any] = {}

        if name:
            data["name"] = name
        if body:
            data["body"] = body
        if state:
            data["state"] = state

        if not data:
            self.logger.warning("未提供任何更新数据")
            return None

        try:
            return self.patch(endpoint, json=data)
        except requests.HTTPError as e:
            self.logger.error(f"更新项目失败: {e}")
            return None

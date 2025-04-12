#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目管理核心模块.

提供与GitHub Projects相关的基本操作，如获取和创建项目。
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from .github_client import GitHubClientBase


class GitHubProjectsClient(GitHubClientBase):
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

    def get_owner_id(self, owner: str) -> Optional[str]:
        """获取所有者的node ID.

        Args:
            owner: 所有者登录名

        Returns:
            Optional[str]: 所有者的node ID
        """
        # First try as a user
        query = """
        query($owner:String!) {
          user(login: $owner) {
            id
          }
        }
        """
        variables = {"owner": owner}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response and response["data"]["user"]:
                return response["data"]["user"]["id"]
        except Exception as e:
            self.logger.debug(f"作为用户查询失败: {e}")

        # If not found as a user, try as an organization
        query = """
        query($owner:String!) {
          organization(login: $owner) {
            id
          }
        }
        """

        try:
            response = self.graphql(query, variables)
            if response and "data" in response and response["data"]["organization"]:
                return response["data"]["organization"]["id"]
        except Exception as e:
            self.logger.debug(f"作为组织查询失败: {e}")

        self.logger.error(f"无法找到所有者 '{owner}' 的ID")
        return None

    def get_repository_id(self, owner: str, repo: str) -> Optional[str]:
        """获取仓库的node ID.

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Optional[str]: 仓库的node ID
        """
        query = """
        query($owner:String!, $repo:String!) {
          repository(owner: $owner, name: $repo) {
            id
          }
        }
        """
        variables = {"owner": owner, "repo": repo}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response and response["data"]["repository"]:
                return response["data"]["repository"]["id"]
            return None
        except Exception as e:
            self.logger.error(f"获取仓库ID失败: {e}")
            return None

    def get_projects(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """获取仓库的所有项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        query = """
        query($owner:String!, $repo:String!) {
          repository(owner: $owner, name: $repo) {
            projectsV2(first: 20) {
              nodes {
                id
                title
                shortDescription
                url
                closed
                createdAt
                updatedAt
                number
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response:
                return response["data"]["repository"]["projectsV2"]["nodes"]
            return []
        except Exception as e:
            self.logger.error(f"获取项目失败: {e}")
            return []

    def get_project_v2(self, owner: str, repo: str, project_number: int) -> Optional[Dict[str, Any]]:
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
            response = self.graphql(query, variables)
            if response and "data" in response:
                return response["data"]["repository"]["projectV2"]
            return None
        except Exception as e:
            self.logger.error(f"获取项目v2数据失败: {e}")
            return None

    def create_project(self, owner: str, repo: str, name: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """创建项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            name: 项目名称
            body: 项目描述

        Returns:
            Optional[Dict[str, Any]]: 创建的项目
        """
        # 首先获取所有者和仓库的node ID
        owner_id = self.get_owner_id(owner)
        repo_id = self.get_repository_id(owner, repo)

        if not owner_id or not repo_id:
            self.logger.error("无法获取所有者或仓库ID")
            return None

        # 创建项目
        query = """
        mutation($input: CreateProjectV2Input!) {
          createProjectV2(input: $input) {
            projectV2 {
              id
              title
              shortDescription
              url
              closed
              createdAt
              updatedAt
              number
            }
          }
        }
        """
        variables = {"input": {"ownerId": owner_id, "title": name, "repositoryId": repo_id}}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response:
                project = response["data"]["createProjectV2"]["projectV2"]

                # 如果提供了描述，则更新项目
                if body and project.get("id"):
                    updated_project = self.update_project(owner, repo, project["id"], body=body)
                    if updated_project:
                        return updated_project

                return project
            return None
        except Exception as e:
            self.logger.error(f"创建项目失败: {e}")
            return None

    def get_organization_projects(self, org: str) -> List[Dict[str, Any]]:
        """获取组织的所有项目.

        Args:
            org: 组织名称

        Returns:
            List[Dict[str, Any]]: 项目列表
        """
        query = """
        query($org:String!) {
          organization(login: $org) {
            projectsV2(first: 20) {
              nodes {
                id
                title
                shortDescription
                url
                closed
                createdAt
                updatedAt
                number
              }
            }
          }
        }
        """
        variables = {"org": org}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response:
                return response["data"]["organization"]["projectsV2"]["nodes"]
            return []
        except Exception as e:
            self.logger.error(f"获取组织项目失败: {e}")
            return []

    def update_project(
        self,
        owner: str,
        repo: str,
        project_id: str,  # Changed from int to str as it's now a node ID
        name: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_id: 项目ID (GraphQL node ID)
            name: 新项目名称
            body: 新项目描述
            state: 新项目状态 ("open" 或 "closed")

        Returns:
            Optional[Dict[str, Any]]: 更新后的项目
        """
        query = """
        mutation($input: UpdateProjectV2Input!) {
          updateProjectV2(input: $input) {
            projectV2 {
              id
              title
              shortDescription
              url
              closed
              createdAt
              updatedAt
              number
            }
          }
        }
        """
        input_data = {"projectId": project_id}
        if name:
            input_data["title"] = name
        if body:
            input_data["shortDescription"] = body
        if state:
            input_data["closed"] = state.lower() == "closed"

        variables = {"input": input_data}

        try:
            response = self.graphql(query, variables)
            if response and "data" in response:
                return response["data"]["updateProjectV2"]["projectV2"]
            return None
        except Exception as e:
            self.logger.error(f"更新项目失败: {e}")
            return None

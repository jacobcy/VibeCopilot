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

    def get_project_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """直接通过Node ID查询项目，避免使用repository路径"""
        query = """
        query($node_id:ID!) {
          node(id: $node_id) {
            ... on ProjectV2 {
              id
              title
              shortDescription
              url
              closed
              createdAt
              updatedAt
              number
              # Add other fields as needed, similar to get_project_v2
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
                      # Add other Issue fields as needed
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"node_id": node_id}
        self.logger.info(f"GraphQL请求: get_project_by_node_id, 变量: {variables}")
        try:
            response = self.graphql(query, variables)
            if response and "data" in response and response["data"].get("node"):
                project_data = response["data"]["node"]
                if project_data:  # Ensure node is a ProjectV2
                    self.logger.info(f"通过Node ID {node_id} 成功获取项目: {project_data.get('title')}")
                    return project_data
                else:
                    self.logger.warning(f"Node ID {node_id} 解析成功，但不是 ProjectV2 类型或数据为空。")
                    return None
            self.logger.warning(f"通过Node ID {node_id} 获取项目失败，响应中无有效数据: {response}")
            return None
        except Exception as e:
            self.logger.error(f"通过Node ID {node_id} 获取项目时发生GraphQL错误: {e}", exc_info=True)
            return None

    def get_project_v2(self, owner: str, repo: str, project_number: int) -> Optional[Dict[str, Any]]:
        """使用GraphQL API获取项目v2数据.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号

        Returns:
            Optional[Dict[str, Any]]: 项目数据
        """
        # 添加详细的调试日志
        self.logger.info(
            f"get_project_v2调用参数: owner={owner}, repo={repo}, project_number={project_number}, token_length={len(self.token or '') if self.token else 0}"
        )

        # 确保project_number是整数
        try:
            project_number = int(project_number)
        except (TypeError, ValueError) as e:
            self.logger.error(f"project_number 转换为整数时出错: {e}, 原始值: {project_number}, 类型: {type(project_number)}")
            raise ValueError(f"项目编号必须是整数: {project_number}")

        project_fields_fragment = """
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
                      # Add other field value types if necessary
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
                    # Add ... on PullRequest if needed
                  }
                }
              }
        """

        # 1. 尝试通过仓库路径查询
        repo_query = f"""
        query($owner:String!, $repo:String!, $number:Int!) {{
          repository(owner: $owner, name: $repo) {{
            projectV2(number: $number) {{
              {project_fields_fragment}
            }}
          }}
        }}
        """
        variables = {"owner": owner, "repo": repo, "number": project_number}
        self.logger.info(f"GraphQL请求 (repository): get_project_v2, 变量: {variables}")

        try:
            response = self.graphql(repo_query, variables)
            if response and "data" in response and response["data"].get("repository") and response["data"]["repository"].get("projectV2"):
                project_data = response["data"]["repository"]["projectV2"]
                self.logger.info(f"成功通过repository路径获取项目v2数据: {project_data.get('title')}")
                return project_data
            self.logger.warning(f"通过repository路径查询GraphQL响应中没有找到项目数据: {response}")
        except Exception as e:
            self.logger.error(f"通过repository路径获取项目v2数据失败: {e}", exc_info=True)

        # 2. 如果仓库路径失败，尝试通过用户路径查询
        self.logger.info(f"Repository路径查询失败，尝试User路径查询项目 #{project_number} (owner: {owner})")
        user_query = f"""
        query($owner:String!, $number:Int!) {{
          user(login: $owner) {{
            projectV2(number: $number) {{
              {project_fields_fragment}
            }}
          }}
        }}
        """
        variables_user = {"owner": owner, "number": project_number}
        try:
            response_user = self.graphql(user_query, variables_user)
            if response_user and "data" in response_user and response_user["data"].get("user") and response_user["data"]["user"].get("projectV2"):
                project_data_user = response_user["data"]["user"]["projectV2"]
                self.logger.info(f"成功通过User路径获取项目v2数据: {project_data_user.get('title')}")
                return project_data_user
            self.logger.warning(f"通过User路径查询GraphQL响应中没有找到项目数据: {response_user}")
        except Exception as e:
            self.logger.error(f"通过User路径获取项目v2数据失败: {e}", exc_info=True)

        # 3. 如果用户路径失败，尝试通过组织路径查询
        self.logger.info(f"User路径查询失败，尝试Organization路径查询项目 #{project_number} (owner: {owner})")
        org_query = f"""
        query($owner:String!, $number:Int!) {{
          organization(login: $owner) {{
            projectV2(number: $number) {{
              {project_fields_fragment}
            }}
          }}
        }}
        """
        variables_org = {"owner": owner, "number": project_number}
        try:
            response_org = self.graphql(org_query, variables_org)
            if (
                response_org
                and "data" in response_org
                and response_org["data"].get("organization")
                and response_org["data"]["organization"].get("projectV2")
            ):
                project_data_org = response_org["data"]["organization"]["projectV2"]
                self.logger.info(f"成功通过Organization路径获取项目v2数据: {project_data_org.get('title')}")
                return project_data_org
            self.logger.warning(f"通过Organization路径查询GraphQL响应中没有找到项目数据: {response_org}")
        except Exception as e:
            self.logger.error(f"通过Organization路径获取项目v2数据失败: {e}", exc_info=True)

        self.logger.error(f"所有路径查询项目 #{project_number} (owner: {owner}) 均失败。")
        return None

    def get_project_v2_by_viewer(self, project_number: int) -> Optional[Dict[str, Any]]:
        """使用viewer查询获取ProjectV2数据.

        Args:
            project_number: 项目编号

        Returns:
            Optional[Dict[str, Any]]: 项目数据
        """
        # 添加详细的调试日志
        self.logger.info(f"get_project_v2_by_viewer调用参数: project_number={project_number}")

        # 确保project_number是整数
        try:
            project_number = int(project_number)
        except (TypeError, ValueError) as e:
            self.logger.error(f"project_number 转换为整数时出错: {e}, 原始值: {project_number}, 类型: {type(project_number)}")
            raise ValueError(f"项目编号必须是整数: {project_number}")

        query = """
        query($number:Int!) {
          viewer {
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
        variables = {"number": project_number}

        # 打印GraphQL请求详情
        self.logger.info(f"GraphQL请求变量: {variables}")

        try:
            response = self.graphql(query, variables)
            if response and "data" in response and response["data"]["viewer"]["projectV2"]:
                project_data = response["data"]["viewer"]["projectV2"]
                self.logger.info(f"成功获取项目v2数据: {project_data.get('title') if project_data else 'None'}")
                return project_data
            self.logger.warning(f"GraphQL响应中没有找到项目数据: {response}")
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

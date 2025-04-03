#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Projects API客户端模块.

提供与GitHub Projects API交互的功能，包括项目创建、查询和管理。
"""

import json
from typing import Any, Dict, List, Optional, Union

import requests

from .github_client import GitHubClient


class GitHubProjectsClient(GitHubClient):
    """GitHub Projects API客户端."""

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
            print(f"获取项目失败: {e}")
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
            print(f"获取项目v2数据失败: {e}")
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
            print(f"创建项目失败: {e}")
            return None

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
        query = """
        query($owner:String!, $repo:String!, $number:Int!) {
          repository(owner: $owner, name: $repo) {
            projectV2(number: $number) {
              fields(first: 50) {
                nodes {
                  ... on ProjectV2FieldCommon {
                    id
                    name
                    dataType
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    dataType
                    options {
                      id
                      name
                      color
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
            fields = (
                response.get("data", {})
                .get("repository", {})
                .get("projectV2", {})
                .get("fields", {})
                .get("nodes", [])
            )
            return fields
        except Exception as e:
            print(f"获取项目字段失败: {e}")
            return []

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
        mutation = """
        mutation($projectId:ID!, $contentId:ID!) {
          addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}) {
            item {
              id
            }
          }
        }
        """
        variables = {"projectId": project_id, "contentId": issue_id}

        try:
            response = self.graphql(mutation, variables)
            return "data" in response and "addProjectV2ItemById" in response["data"]
        except Exception as e:
            print(f"添加Issue到项目失败: {e}")
            return False

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
        mutation = """
        mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $value:String!) {
          updateProjectV2ItemFieldValue(
            input:{
              projectId:$projectId,
              itemId:$itemId,
              fieldId:$fieldId,
              value:{
                text:$value
              }
            }
          ) {
            projectV2Item {
              id
            }
          }
        }
        """
        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": str(value) if not isinstance(value, dict) else value,
        }

        try:
            response = self.graphql(mutation, variables)
            return "data" in response and "updateProjectV2ItemFieldValue" in response["data"]
        except Exception as e:
            print(f"更新项目条目字段值失败: {e}")
            return False

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
        # 确定正确的GraphQL变异操作
        if field_type == "SINGLE_SELECT":
            if not options:
                print("错误: 单选字段必须提供选项")
                return None

            mutation = """
            mutation($projectId:ID!, $name:String!, $options:[CreateProjectV2FieldOptionInput!]!) {
              createProjectV2SingleSelectField(
                input:{
                  projectId:$projectId,
                  name:$name,
                  options:$options
                }
              ) {
                field {
                  id
                }
              }
            }
            """

            # 准备选项数据
            formatted_options = []
            for option in options:
                formatted_option = {
                    "name": option["name"],
                    "color": option.get("color", "GRAY"),  # 默认灰色
                }
                formatted_options.append(formatted_option)

            variables = {"projectId": project_id, "name": name, "options": formatted_options}

            result_path = ["createProjectV2SingleSelectField", "field", "id"]

        else:  # 其他类型的字段
            mutation = """
            mutation($projectId:ID!, $name:String!, $dataType:ProjectV2FieldType!) {
              createProjectV2Field(
                input:{
                  projectId:$projectId,
                  name:$name,
                  dataType:$dataType
                }
              ) {
                field {
                  id
                }
              }
            }
            """

            # 映射字段类型
            data_type_map = {
                "TEXT": "TEXT",
                "NUMBER": "NUMBER",
                "DATE": "DATE",
                "SINGLE_SELECT": "SINGLE_SELECT",
                "ITERATION": "ITERATION",
            }

            data_type = data_type_map.get(field_type.upper(), "TEXT")

            variables = {"projectId": project_id, "name": name, "dataType": data_type}

            result_path = ["createProjectV2Field", "field", "id"]

        try:
            response = self.graphql(mutation, variables)

            # 提取字段ID
            result = response.get("data", {})
            for key in result_path:
                result = result.get(key, {})

            if isinstance(result, str):
                return result
            return None

        except Exception as e:
            print(f"添加字段失败: {e}")
            return None


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

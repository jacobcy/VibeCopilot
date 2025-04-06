#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目字段管理模块.

提供与GitHub Projects字段相关的API交互功能。
"""

from typing import Any, Dict, List, Optional

from ..github_client import GitHubClient


class GitHubProjectFieldsClient(GitHubClient):
    """GitHub项目字段客户端."""

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

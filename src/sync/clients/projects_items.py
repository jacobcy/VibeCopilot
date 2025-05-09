#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目条目管理模块.

提供与GitHub Projects条目（如任务、工作项等）相关的API交互功能。
"""

import logging
from typing import Any, Dict, List, Optional, Union

import requests

from .github_client import GitHubClientBase


class GitHubProjectItemsClient(GitHubClientBase):
    """GitHub项目条目客户端."""

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

    def get_project_items(self, project_id: str, cursor: str = None, page_size: int = 100) -> Dict[str, Any]:
        """获取项目中的条目.

        Args:
            project_id: 项目ID
            cursor: 分页游标
            page_size: 每页条目数量

        Returns:
            Dict[str, Any]: 项目条目和分页信息
        """
        query = """
        query($projectId:ID!, $cursor:String, $pageSize:Int!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: $pageSize, after: $cursor) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  id
                  fieldValues(first: 20) {
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
                      id
                      title
                      number
                      state
                      updatedAt
                    }
                    ... on PullRequest {
                      id
                      title
                      number
                      state
                      updatedAt
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"projectId": project_id, "cursor": cursor, "pageSize": page_size}

        try:
            response = self.graphql(query, variables)
            return response.get("data", {}).get("node", {}).get("items", {})
        except Exception as e:
            print(f"获取项目条目失败: {e}")
            return {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}

    def get_project_items_by_node_id(self, project_node_id: str) -> List[Dict[str, Any]]:
        """
        通过Node ID获取项目的所有条目，自动处理分页

        Args:
            project_node_id: 项目的Node ID

        Returns:
            List[Dict[str, Any]]: 所有项目条目列表
        """
        logger = logging.getLogger(__name__)
        all_items = []
        cursor = None
        total_pages = 0

        logger.info(f"开始获取项目 {project_node_id} 的所有条目")

        while True:
            total_pages += 1
            try:
                # 使用现有的get_project_items方法获取一页数据
                page_result = self.get_project_items(project_node_id, cursor=cursor, page_size=100)

                # 提取当前页的条目并添加到结果列表
                nodes = page_result.get("nodes", [])
                all_items.extend(nodes)

                # 检查是否有下一页
                page_info = page_result.get("pageInfo", {})
                if page_info.get("hasNextPage"):
                    cursor = page_info.get("endCursor")
                    logger.debug(f"获取下一页，游标: {cursor}")
                else:
                    # 没有更多页，退出循环
                    break
            except Exception as e:
                logger.error(f"获取项目条目页面 {total_pages} 时出错: {e}", exc_info=True)
                break

        logger.info(f"共获取 {len(all_items)} 个项目条目，共 {total_pages} 页")
        return all_items

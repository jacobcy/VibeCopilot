#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入路线图数据到GitHub Projects脚本.

此脚本读取本地YAML格式的路线图数据，
并将其导入到GitHub Projects中，创建对应的milestone、issues和项目视图。
"""

import os
import sys
import yaml
import json
import argparse
from typing import Dict, List, Any, Optional

import requests
from datetime import datetime


class GitHubImporter:
    """GitHub Projects导入工具类."""

    def __init__(self, token: Optional[str] = None) -> None:
        """初始化GitHub导入工具.

        Args:
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("错误: 未提供GitHub令牌，无法导入数据")
            sys.exit(1)

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}"
        }
        self.graphql_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.rest_api = "https://api.github.com"
        self.graphql_api = "https://api.github.com/graphql"

    def load_roadmap_data(self, yaml_file: str) -> Dict[str, Any]:
        """加载YAML格式的路线图数据.

        Args:
            yaml_file: YAML文件路径

        Returns:
            路线图数据字典
        """
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            print(f"错误: 无法加载路线图数据 - {e}")
            sys.exit(1)

    def create_milestone(
        self, owner: str, repo: str, milestone_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """在GitHub仓库创建里程碑.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            milestone_data: 里程碑数据

        Returns:
            创建的里程碑响应
        """
        url = f"{self.rest_api}/repos/{owner}/{repo}/milestones"

        # 准备Milestone数据
        payload = {
            "title": f"{milestone_data['id']}: {milestone_data['name']}",
            "state": "open" if milestone_data["status"] != "completed" else "closed",
            "description": milestone_data["description"],
            "due_on": f"{milestone_data['end_date']}T23:59:59Z"
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201:
            print(f"成功创建里程碑: {milestone_data['id']} - {milestone_data['name']}")
            return response.json()
        else:
            print(f"创建里程碑失败: {response.status_code} - {response.text}")
            print(f"里程碑数据: {json.dumps(payload, ensure_ascii=False)}")
            return None

    def create_issue(
        self,
        owner: str,
        repo: str,
        task_data: Dict[str, Any],
        milestone_number: int
    ) -> Optional[Dict[str, Any]]:
        """在GitHub仓库创建Issue.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            task_data: 任务数据
            milestone_number: 里程碑编号

        Returns:
            创建的Issue响应
        """
        url = f"{self.rest_api}/repos/{owner}/{repo}/issues"

        # 根据优先级映射标签
        priority_labels = {
            "P0": "priority:critical",
            "P1": "priority:high",
            "P2": "priority:medium",
            "P3": "priority:low"
        }

        # 根据状态映射标签
        status_labels = {
            "completed": "status:completed",
            "in_progress": "status:in-progress",
            "todo": "status:todo",
            "planned": "status:planned"
        }

        # 准备标签
        labels = [
            f"milestone:{task_data['milestone']}",
            priority_labels.get(task_data['priority'], "priority:medium"),
            status_labels.get(task_data['status'], "status:planned")
        ]

        # 准备Issue数据
        payload = {
            "title": f"{task_data['id']}: {task_data['title']}",
            "body": task_data["description"],
            "milestone": milestone_number,
            "labels": labels,
            "assignees": task_data.get("assignees", [])
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201:
            print(f"成功创建Issue: {task_data['id']} - {task_data['title']}")
            return response.json()
        else:
            print(f"创建Issue失败: {response.status_code} - {response.text}")
            print(f"Issue数据: {json.dumps(payload, ensure_ascii=False)}")
            return None

    def create_project(
        self, owner: str, title: str, description: str
    ) -> Optional[Dict[str, Any]]:
        """创建GitHub Project.

        Args:
            owner: 组织或用户名
            title: 项目标题
            description: 项目描述

        Returns:
            创建的项目信息
        """
        # 使用GraphQL API创建项目
        query = """
        mutation createProject($input: CreateProjectV2Input!) {
          createProjectV2(input: $input) {
            projectV2 {
              id
              title
              url
              number
            }
          }
        }
        """

        variables = {
            "input": {
                "ownerId": owner,
                "title": title,
                "description": description,
                "repositoryId": None
            }
        }

        # 先获取用户或组织的节点ID
        user_query = """
        query($login: String!) {
          user(login: $login) {
            id
          }
          organization(login: $login) {
            id
          }
        }
        """

        user_response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": user_query, "variables": {"login": owner}}
        )

        if user_response.status_code != 200:
            print(f"获取用户/组织ID失败: {user_response.status_code} - {user_response.text}")
            return None

        user_data = user_response.json()
        if user_data.get("data", {}).get("user", {}).get("id"):
            variables["input"]["ownerId"] = user_data["data"]["user"]["id"]
        elif user_data.get("data", {}).get("organization", {}).get("id"):
            variables["input"]["ownerId"] = user_data["data"]["organization"]["id"]
        else:
            print(f"找不到用户或组织: {owner}")
            return None

        # 创建项目
        response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": query, "variables": variables}
        )

        if response.status_code == 200 and "errors" not in response.json():
            project = response.json().get("data", {}).get("createProjectV2", {}).get("projectV2", {})
            print(f"成功创建项目: {title}")
            print(f"项目URL: {project.get('url')}")
            return project
        else:
            print(f"创建项目失败: {response.status_code} - {response.text}")
            return None

    def add_custom_fields(
        self, project_id: str
    ) -> Dict[str, str]:
        """添加自定义字段到项目.

        Args:
            project_id: 项目ID

        Returns:
            字段ID字典
        """
        field_queries = {
            "milestone": """
            mutation($projectId: ID!) {
              createProjectV2Field(input: {
                projectId: $projectId,
                dataType: SINGLE_SELECT,
                name: "里程碑",
                options: ["M1", "M2", "M3", "M4", "M5"]
              }) {
                projectV2Field { id }
              }
            }
            """,
            "priority": """
            mutation($projectId: ID!) {
              createProjectV2Field(input: {
                projectId: $projectId,
                dataType: SINGLE_SELECT,
                name: "优先级",
                options: ["P0", "P1", "P2", "P3"]
              }) {
                projectV2Field { id }
              }
            }
            """,
            "status": """
            mutation($projectId: ID!) {
              createProjectV2Field(input: {
                projectId: $projectId,
                dataType: SINGLE_SELECT,
                name: "状态",
                options: ["计划中", "待办", "进行中", "已完成"]
              }) {
                projectV2Field { id }
              }
            }
            """
        }

        field_ids = {}

        for field_name, query in field_queries.items():
            response = requests.post(
                self.graphql_api,
                headers=self.graphql_headers,
                json={"query": query, "variables": {"projectId": project_id}}
            )

            if response.status_code == 200 and "errors" not in response.json():
                field_id = (
                    response.json()
                    .get("data", {})
                    .get("createProjectV2Field", {})
                    .get("projectV2Field", {})
                    .get("id")
                )
                if field_id:
                    field_ids[field_name] = field_id
                    print(f"成功添加字段: {field_name}")
            else:
                print(f"添加字段 {field_name} 失败: {response.text}")

        return field_ids

    def add_items_to_project(
        self,
        project_id: str,
        issue_ids: List[Dict[str, Any]],
        field_ids: Dict[str, str],
        task_mapping: Dict[str, Any]
    ) -> None:
        """添加项目到GitHub Project并设置字段值.

        Args:
            project_id: 项目ID
            issue_ids: Issue ID列表
            field_ids: 字段ID映射
            task_mapping: 任务映射，用于设置字段值
        """
        # 添加Items到项目
        for issue_id in issue_ids:
            issue_node_id = issue_id["node_id"]
            issue_number = issue_id["number"]
            issue_title = issue_id["title"]

            # 安全地提取任务ID，防止格式不一致导致的问题
            try:
                task_id = issue_title.split(":", 1)[0].strip()
            except (IndexError, AttributeError):
                print(f"无法解析任务ID，跳过设置字段值: {issue_title}")
                task_id = ""

            # 添加到项目
            add_query = """
            mutation($projectId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {
                projectId: $projectId,
                contentId: $contentId
              }) {
                item {
                  id
                }
              }
            }
            """

            add_response = requests.post(
                self.graphql_api,
                headers=self.graphql_headers,
                json={"query": add_query, "variables": {
                    "projectId": project_id,
                    "contentId": issue_node_id
                }}
            )

            if add_response.status_code != 200 or "errors" in add_response.json():
                print(f"添加Issue到项目失败: {issue_title} - {add_response.text}")
                continue

            item_id = (
                add_response.json()
                .get("data", {})
                .get("addProjectV2ItemById", {})
                .get("item", {})
                .get("id")
            )

            if not item_id:
                print(f"无法获取项目项ID: {issue_title}")
                continue

            print(f"成功添加Issue到项目: {issue_title}")

            # 如果有对应的任务数据，设置字段值
            if task_id in task_mapping:
                task_data = task_mapping[task_id]

                # 设置里程碑字段
                if "milestone" in field_ids and "milestone" in task_data:
                    self.set_field_value(
                        project_id,
                        item_id,
                        field_ids["milestone"],
                        task_data["milestone"],
                        issue_title
                    )

                # 设置优先级字段
                if "priority" in field_ids and "priority" in task_data:
                    self.set_field_value(
                        project_id,
                        item_id,
                        field_ids["priority"],
                        task_data["priority"],
                        issue_title
                    )

                # 设置状态字段
                if "status" in field_ids and "status" in task_data:
                    status_map = {
                        "completed": "已完成",
                        "in_progress": "进行中",
                        "todo": "待办",
                        "planned": "计划中"
                    }
                    status_value = status_map.get(task_data["status"], "计划中")
                    self.set_field_value(
                        project_id,
                        item_id,
                        field_ids["status"],
                        status_value,
                        issue_title
                    )

    def set_field_value(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: str,
        item_title: str
    ) -> None:
        """设置项目字段值.

        Args:
            project_id: 项目ID
            item_id: 项目项ID
            field_id: 字段ID
            value: 字段值
            item_title: 项目项标题，用于日志
        """
        query = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: {
              singleSelectOptionId: $value
            }
          }) {
            projectV2Item {
              id
            }
          }
        }
        """

        # 首先获取选项ID
        options_query = """
        query($projectId: ID!, $fieldId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              field(id: $fieldId) {
                ... on ProjectV2SingleSelectField {
                  options {
                    id
                    name
                  }
                }
              }
            }
          }
        }
        """

        options_response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": options_query, "variables": {
                "projectId": project_id,
                "fieldId": field_id
            }}
        )

        if options_response.status_code != 200 or "errors" in options_response.json():
            print(f"获取字段选项失败: {item_title} - {options_response.text}")
            return

        options = (
            options_response.json()
            .get("data", {})
            .get("node", {})
            .get("field", {})
            .get("options", [])
        )

        option_id = None
        for option in options:
            if option.get("name") == value:
                option_id = option.get("id")
                break

        if not option_id:
            print(f"找不到选项 {value} 对应的ID: {item_title}")
            return

        # 设置字段值
        update_response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": query, "variables": {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "value": option_id
            }}
        )

        if update_response.status_code == 200 and "errors" not in update_response.json():
            print(f"成功设置字段值 {value}: {item_title}")
        else:
            print(f"设置字段值失败: {item_title} - {update_response.text}")

    def create_labels(self, owner: str, repo: str) -> None:
        """创建标准标签.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
        """
        labels = [
            {"name": "milestone:M1", "color": "C5DEF5", "description": "准备阶段"},
            {"name": "milestone:M2", "color": "C5DEF5", "description": "核心功能开发阶段"},
            {"name": "milestone:M3", "color": "C5DEF5", "description": "功能扩展阶段"},
            {"name": "milestone:M4", "color": "C5DEF5", "description": "集成与测试阶段"},
            {"name": "milestone:M5", "color": "C5DEF5", "description": "发布与迭代阶段"},

            {"name": "priority:critical", "color": "B60205", "description": "最高优先级 (P0)"},
            {"name": "priority:high", "color": "D93F0B", "description": "高优先级 (P1)"},
            {"name": "priority:medium", "color": "FBCA04", "description": "中优先级 (P2)"},
            {"name": "priority:low", "color": "0E8A16", "description": "低优先级 (P3)"},

            {"name": "status:planned", "color": "BFD4F2", "description": "计划中"},
            {"name": "status:todo", "color": "D4C5F9", "description": "待办"},
            {"name": "status:in-progress", "color": "FEF2C0", "description": "进行中"},
            {"name": "status:completed", "color": "C2E0C6", "description": "已完成"},

            {"name": "type:feature", "color": "006B75", "description": "新功能"},
            {"name": "type:bug", "color": "EE0701", "description": "缺陷"},
            {"name": "type:docs", "color": "1D76DB", "description": "文档"},
            {"name": "type:enhancement", "color": "5319E7", "description": "改进"}
        ]

        for label in labels:
            url = f"{self.rest_api}/repos/{owner}/{repo}/labels"
            response = requests.post(url, headers=self.headers, json=label)

            if response.status_code == 201:
                print(f"成功创建标签: {label['name']}")
            elif response.status_code == 422:  # 标签已存在
                print(f"标签已存在: {label['name']}")
            else:
                print(f"创建标签失败: {label['name']} - {response.status_code} - {response.text}")


def main() -> None:
    """主函数."""
    parser = argparse.ArgumentParser(description="将路线图数据导入到GitHub Projects")
    parser.add_argument("-t", "--token", help="GitHub个人访问令牌")
    parser.add_argument("-o", "--owner", default="jacobcy", help="仓库所有者")
    parser.add_argument("-r", "--repo", default="VibeCopilot", help="仓库名称")
    parser.add_argument(
        "-f", "--file",
        default="data/roadmap.yaml",
        help="YAML格式的路线图数据文件路径"
    )
    parser.add_argument(
        "--create-project",
        action="store_true",
        help="是否创建新的GitHub Project"
    )
    parser.add_argument(
        "--project-title",
        default="VibeCopilot Roadmap",
        help="GitHub Project标题"
    )

    args = parser.parse_args()

    importer = GitHubImporter(args.token)

    # 加载路线图数据
    roadmap_data = importer.load_roadmap_data(args.file)
    print(f"成功加载路线图数据: {roadmap_data['title']}")

    # 创建标签
    importer.create_labels(args.owner, args.repo)

    # 创建里程碑
    milestones = {}
    for milestone in roadmap_data["milestones"]:
        milestone_resp = importer.create_milestone(args.owner, args.repo, milestone)
        if milestone_resp:
            milestones[milestone["id"]] = milestone_resp["number"]

    # 创建Issue
    issues = []
    task_mapping = {}
    for task in roadmap_data["tasks"]:
        milestone_number = milestones.get(task["milestone"])
        if milestone_number:
            issue = importer.create_issue(args.owner, args.repo, task, milestone_number)
            if issue is not None:
                issues.append(issue)
                task_mapping[task["id"]] = task

    # 如果需要创建项目
    if args.create_project:
        project = importer.create_project(
            args.owner,
            args.project_title,
            roadmap_data["description"]
        )

        if project:
            # 添加自定义字段
            field_ids = importer.add_custom_fields(project["id"])

            # 将Issue添加到项目并设置字段值
            importer.add_items_to_project(
                project["id"],
                issues,
                field_ids,
                task_mapping
            )


if __name__ == "__main__":
    main()
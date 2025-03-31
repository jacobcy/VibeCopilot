#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入路线图数据到GitHub Projects脚本.

此脚本读取本地YAML格式的路线图数据，
并将其导入到GitHub Projects中，创建对应的milestone、issues和项目视图。

使用方法:
1. 复制 .env.sample 为 .env 并填入您的GitHub令牌
2. 运行: python scripts/import_roadmap_to_github.py

或者直接指定参数:
python scripts/import_roadmap_to_github.py --owner <账户名> --repo <仓库名> --file <数据文件路径>
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests
import yaml

# 尝试导入dotenv库用于加载环境变量
try:
    from dotenv import load_dotenv

    # 加载.env文件中的环境变量
    load_dotenv()
except ImportError:
    print("提示: 未安装dotenv库，将不会从.env文件加载环境变量")
    print("可以运行 'pip install python-dotenv' 安装该库")


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
            "Authorization": f"Bearer {self.token}",
        }
        self.graphql_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
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
                # 明确指定返回类型，避免Any类型
                result: Dict[str, Any] = data
            return result
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
            "due_on": f"{milestone_data['end_date']}T23:59:59Z",
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201:
            print(f"成功创建里程碑: {milestone_data['id']} - {milestone_data['name']}")
            # 明确指定返回类型，避免Any类型
            milestone_response: Dict[str, Any] = response.json()
            return milestone_response
        else:
            print(f"创建里程碑失败: {response.status_code} - {response.text}")
            print(f"里程碑数据: {json.dumps(payload, ensure_ascii=False)}")
            return None

    def create_issue(
        self, owner: str, repo: str, task_data: Dict[str, Any], milestone_number: int
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
            "P3": "priority:low",
        }

        # 根据状态映射标签
        status_labels = {
            "completed": "status:completed",
            "in_progress": "status:in-progress",
            "todo": "status:todo",
            "planned": "status:planned",
        }

        # 准备标签
        labels = [
            f"milestone:{task_data['milestone']}",
            priority_labels.get(task_data["priority"], "priority:medium"),
            status_labels.get(task_data["status"], "status:planned"),
        ]

        # 准备Issue数据
        payload = {
            "title": f"{task_data['id']}: {task_data['title']}",
            "body": task_data["description"],
            "milestone": milestone_number,
            "labels": labels,
            "assignees": task_data.get("assignees", []),
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 201:
            print(f"成功创建Issue: {task_data['id']} - {task_data['title']}")
            # 明确指定返回类型，避免Any类型
            issue_response: Dict[str, Any] = response.json()
            return issue_response
        else:
            print(f"创建Issue失败: {response.status_code} - {response.text}")
            print(f"Issue数据: {json.dumps(payload, ensure_ascii=False)}")
            return None

    def create_project(self, owner: str, title: str, description: str) -> Optional[Dict[str, Any]]:
        """创建GitHub Project.

        Args:
            owner: 组织或用户名
            title: 项目标题
            description: 项目描述 (注意: GitHub API已不支持创建时设置描述)

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
                # description字段已不再被支持
                "repositoryId": None,
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

        print(f"尝试获取用户/组织ID: {owner}")
        user_response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": user_query, "variables": {"login": owner}},
        )

        print(f"用户/组织查询状态码: {user_response.status_code}")
        print(f"用户/组织查询响应: {user_response.text}")

        if user_response.status_code != 200:
            print(f"获取用户/组织ID失败: {user_response.status_code} - {user_response.text}")
            return None

        user_data = user_response.json()
        # 只在找不到用户也找不到组织时报错，而不是出现任何错误就报错
        if "data" not in user_data or (
            user_data.get("data", {}).get("user", {}).get("id") is None
            and user_data.get("data", {}).get("organization", {}).get("id") is None
        ):
            print(f"找不到用户或组织 {owner} 的ID")
            return None

        if user_data.get("data", {}).get("user", {}).get("id"):
            variables["input"]["ownerId"] = user_data["data"]["user"]["id"]
            print(f"已获取用户ID: {variables['input']['ownerId']}")
        elif user_data.get("data", {}).get("organization", {}).get("id"):
            variables["input"]["ownerId"] = user_data["data"]["organization"]["id"]
            print(f"已获取组织ID: {variables['input']['ownerId']}")
        else:
            print(f"找不到用户或组织: {owner}")
            return None

        # 创建项目
        print(f"尝试创建项目，请求数据: {json.dumps(variables)}")
        response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={"query": query, "variables": variables},
        )

        print(f"创建项目响应状态码: {response.status_code}")
        print(f"创建项目响应: {response.text}")

        if response.status_code == 200 and "errors" not in response.json():
            project_json = response.json()
            project_data = (
                project_json.get("data", {}).get("createProjectV2", {}).get("projectV2", {})
            )
            # 明确指定返回类型，避免Any类型
            project: Dict[str, Any] = {
                "id": project_data.get("id"),
                "title": project_data.get("title"),
                "url": project_data.get("url"),
                "number": project_data.get("number"),
            }
            print(f"成功创建项目: {title}")
            print(f"项目URL: {project.get('url')}")
            return project
        else:
            print(f"创建项目失败: {response.status_code} - {response.text}")
            return None

    def add_custom_fields(self, project_id: str) -> Dict[str, str]:
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
            """,
        }

        field_ids = {}

        for field_name, query in field_queries.items():
            response = requests.post(
                self.graphql_api,
                headers=self.graphql_headers,
                json={"query": query, "variables": {"projectId": project_id}},
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
        task_mapping: Dict[str, Any],
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
            # 使用issue_number变量
            issue_data_number = issue_id.get("number")
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
                json={
                    "query": add_query,
                    "variables": {"projectId": project_id, "contentId": issue_node_id},
                },
            )

            if add_response.status_code != 200 or "errors" in add_response.json():
                print(f"添加Issue #{issue_data_number}到项目失败: {issue_title} - {add_response.text}")
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

            print(f"成功添加Issue #{issue_data_number}到项目: {issue_title}")

            # GitHub Projects现在内置了Status、Milestone等字段，无需再创建自定义字段
            # 我们需要通过API查询这些内置字段的ID，然后设置值

            # 先查询项目字段信息
            fields_query = """
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2Field {
                        id
                        name
                      }
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options {
                          id
                          name
                        }
                      }
                    }
                  }
                }
              }
            }
            """

            fields_response = requests.post(
                self.graphql_api,
                headers=self.graphql_headers,
                json={"query": fields_query, "variables": {"projectId": project_id}},
            )

            if fields_response.status_code != 200 or "errors" in fields_response.json():
                print(f"获取项目字段失败: {fields_response.text}")
                continue

            fields = (
                fields_response.json()
                .get("data", {})
                .get("node", {})
                .get("fields", {})
                .get("nodes", [])
            )

            # 查找Status和Milestone字段
            status_field = None
            # 保存milestone_field变量以备后用
            # 当前未使用，保留变量名备将来实现
            _ = None

            for field in fields:
                if field.get("name") == "Status":
                    status_field = field
                elif field.get("name") == "Milestone":
                    # milestone_field = field  # 暂时不使用
                    pass

            # 如果找到Status字段，设置状态
            if status_field and "options" in status_field and task_id in task_mapping:
                status_map = {
                    "completed": "Done",
                    "in_progress": "In Progress",
                    "todo": "Todo",
                    "planned": "Todo",  # 没有"Planned"状态，用"Todo"代替
                }

                task_status = task_mapping[task_id].get("status", "planned")
                status_value = status_map.get(task_status)

                if status_value:
                    # 查找对应的选项ID
                    option_id = None
                    for option in status_field.get("options", []):
                        if option.get("name") == status_value:
                            option_id = option.get("id")
                            break

                    if option_id:
                        self.update_field_value(
                            project_id, item_id, status_field["id"], option_id, issue_title
                        )

            # TODO: 将来实现设置Milestone字段的功能

    def update_field_value(
        self, project_id: str, item_id: str, field_id: str, option_id: str, item_title: str
    ) -> None:
        """更新项目项的字段值.

        Args:
            project_id: 项目ID
            item_id: 项目项ID
            field_id: 字段ID
            option_id: 选项ID
            item_title: 项目项标题，用于日志
        """
        query = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: {
              singleSelectOptionId: $optionId
            }
          }) {
            projectV2Item {
              id
            }
          }
        }
        """

        response = requests.post(
            self.graphql_api,
            headers=self.graphql_headers,
            json={
                "query": query,
                "variables": {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": field_id,
                    "optionId": option_id,
                },
            },
        )

        if response.status_code == 200 and "errors" not in response.json():
            print(f"成功设置字段值: {item_title}")
        else:
            print(f"设置字段值失败: {item_title} - {response.text}")

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
            {"name": "type:enhancement", "color": "5319E7", "description": "改进"},
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
    parser.add_argument(
        "-o", "--owner", default=os.environ.get("GITHUB_OWNER", "jacobcy"), help="仓库所有者"
    )
    parser.add_argument(
        "-r", "--repo", default=os.environ.get("GITHUB_REPO", "VibeCopilot"), help="仓库名称"
    )
    parser.add_argument(
        "-f",
        "--file",
        default=os.environ.get("ROADMAP_DATA_FILE", "data/roadmap.yaml"),
        help="YAML格式的路线图数据文件路径",
    )
    parser.add_argument("--create-project", action="store_true", help="是否创建新的GitHub Project")
    parser.add_argument(
        "--project-title",
        default=os.environ.get("ROADMAP_PROJECT_TITLE", "VibeCopilot Roadmap"),
        help="GitHub Project标题",
    )

    args = parser.parse_args()

    # 如果命令行没有提供token，尝试从环境变量获取
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("错误: 未提供GitHub令牌，请设置GITHUB_TOKEN环境变量或使用--token参数")
        sys.exit(1)

    importer = GitHubImporter(token)

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
            args.owner, args.project_title, roadmap_data["description"]
        )

        if project:
            # 添加自定义字段
            field_ids = importer.add_custom_fields(project["id"])

            # 将Issue添加到项目并设置字段值
            importer.add_items_to_project(project["id"], issues, field_ids, task_mapping)


if __name__ == "__main__":
    main()

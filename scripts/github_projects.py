#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Projects路线图数据获取脚本.

该脚本用于从GitHub Projects API获取VibeCopilot项目路线图数据，
并将其转换为结构化格式，可用于进度报告和可视化。
"""

import json
import os
from argparse import ArgumentParser
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


class GitHubProjectsClient:
    """GitHub Projects API客户端."""

    def __init__(self, token: Optional[str] = None) -> None:
        """初始化GitHub Projects客户端.

        Args:
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("警告: 未提供GitHub令牌，API请求可能受到限制")

        self.headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.graphql_url = "https://api.github.com/graphql"
        self.rest_url = "https://api.github.com"

    def get_projects(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """获取仓库的所有项目.

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            项目列表
        """
        url = f"{self.rest_url}/repos/{owner}/{repo}/projects"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"获取项目失败: {response.status_code} {response.text}")
            return []
        return response.json()  # type: ignore

    def get_project_v2(
        self, owner: str, repo: str, project_number: int
    ) -> Optional[Dict[str, Any]]:
        """使用GraphQL API获取项目v2数据.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号

        Returns:
            项目数据
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

        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json={"query": query, "variables": variables},
        )

        if response.status_code != 200:
            print(f"获取项目数据失败: {response.status_code} {response.text}")
            return None

        return response.json()  # type: ignore

    def process_roadmap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理路线图数据，提取关键信息.

        Args:
            data: 从API获取的原始数据

        Returns:
            结构化的路线图数据
        """
        if not data or "data" not in data:
            return {"error": "无效的数据格式"}

        project_data = data.get("data", {}).get("repository", {}).get("projectV2", {})
        if not project_data:
            return {"error": "找不到项目数据"}

        items = project_data.get("items", {}).get("nodes", [])
        if not items:
            return {"error": "项目中没有任务"}

        # 提取里程碑和任务
        milestones: Dict[str, Dict[str, Any]] = {}
        tasks_by_milestone: Dict[str, List[Dict[str, Any]]] = {}

        for item in items:
            content = item.get("content", {})
            if not content:
                continue

            # 提取任务基本信息
            task: Dict[str, Any] = {
                "title": content.get("title", ""),
                "state": content.get("state", ""),
                "number": content.get("number", 0),
                "url": content.get("url", ""),
                "created_at": content.get("createdAt", ""),
                "updated_at": content.get("updatedAt", ""),
                "labels": [
                    node.get("name", "") for node in content.get("labels", {}).get("nodes", [])
                ],
                "assignees": [
                    assignee.get("login", "")
                    for assignee in (content.get("assignees", {}).get("nodes", []))
                ],
            }

            # 提取自定义字段
            field_values = item.get("fieldValues", {}).get("nodes", [])
            for field_value in field_values:
                field_name = field_value.get("field", {}).get("name", "")
                if "里程碑" in field_name and "name" in field_value:
                    milestone = field_value.get("name", "")
                    task["milestone"] = milestone

                    # 将任务添加到对应里程碑
                    if milestone not in tasks_by_milestone:
                        tasks_by_milestone[milestone] = []
                    tasks_by_milestone[milestone].append(task)

                    # 更新里程碑信息
                    if milestone not in milestones:
                        milestones[milestone] = {
                            "name": milestone,
                            "total_tasks": 0,
                            "completed_tasks": 0,
                        }

                    milestones[milestone]["total_tasks"] += 1
                    if task["state"] == "CLOSED":
                        milestones[milestone]["completed_tasks"] += 1

                elif "状态" in field_name and "name" in field_value:
                    task["status"] = field_value.get("name", "")

                elif "优先级" in field_name and "name" in field_value:
                    task["priority"] = field_value.get("name", "")

                elif "截止日期" in field_name and "date" in field_value:
                    task["due_date"] = field_value.get("date", "")

        # 计算整体项目进度
        total_tasks = sum(m["total_tasks"] for m in milestones.values())
        completed_tasks = sum(m["completed_tasks"] for m in milestones.values())
        overall_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        return {
            "title": project_data.get("title", ""),
            "description": project_data.get("shortDescription", ""),
            "url": project_data.get("url", ""),
            "overall_progress": round(overall_progress, 2),
            "milestones": list(milestones.values()),
            "tasks_by_milestone": tasks_by_milestone,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_report(self, data: Dict[str, Any], format: str = "json") -> str:
        """生成项目进度报告.

        Args:
            data: 结构化的路线图数据
            format: 输出格式 (json, markdown)

        Returns:
            格式化的报告
        """
        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)

        elif format == "markdown":
            report = "# VibeCopilot 路线图进度报告\n\n"
            report += f"**项目**: {data['title']}\n\n"
            report += f"**总体进度**: {data['overall_progress']}%\n\n"
            report += f"**生成时间**: {data['generated_at']}\n\n"

            report += "## 里程碑进度\n\n"
            report += "| 里程碑 | 完成任务 | 总任务数 | 完成率 |\n"
            report += "|--------|----------|---------|--------|\n"

            for milestone in data["milestones"]:
                progress = (
                    (milestone["completed_tasks"] / milestone["total_tasks"]) * 100
                    if milestone["total_tasks"] > 0
                    else 0
                )
                report += (
                    f"| {milestone['name']} | "
                    f"{milestone['completed_tasks']} | "
                    f"{milestone['total_tasks']} | "
                    f"{round(progress, 2)}% |\n"
                )

            report += "\n## 任务明细\n\n"

            for milestone, tasks in data["tasks_by_milestone"].items():
                report += f"### {milestone}\n\n"
                report += "| 任务 | 状态 | 优先级 | 负责人 |\n"
                report += "|------|------|--------|--------|\n"

                for task in tasks:
                    status = task.get("status", task.get("state", "未知"))
                    priority = task.get("priority", "")
                    assignees = ", ".join(task.get("assignees", []))
                    report += (
                        f"| [{task['title']}]({task['url']}) | "
                        f"{status} | {priority} | {assignees} |\n"
                    )

                report += "\n"

            return report

        return f"不支持的格式: {format}"


def main() -> None:
    """主函数."""
    parser = ArgumentParser(description="获取GitHub Projects路线图数据")
    parser.add_argument("-o", "--owner", default="jacobcy", help="仓库所有者")
    parser.add_argument("-r", "--repo", default="VibeCopilot", help="仓库名称")
    parser.add_argument("-p", "--project", type=int, default=1, help="项目编号")
    parser.add_argument(
        "-f", "--format", choices=["json", "markdown"], default="markdown", help="输出格式"
    )
    parser.add_argument("-t", "--token", help="GitHub个人访问令牌")
    parser.add_argument("-s", "--save", help="保存输出到文件")

    args = parser.parse_args()

    client = GitHubProjectsClient(args.token)
    data = client.get_project_v2(args.owner, args.repo, args.project)

    if not data:
        print("获取项目数据失败")
        return

    processed_data = client.process_roadmap_data(data)
    report = client.generate_report(processed_data, args.format)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.save}")
    else:
        print(report)


if __name__ == "__main__":
    main()

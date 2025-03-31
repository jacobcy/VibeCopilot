#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将现有GitHub Issues添加到GitHub Project脚本.

此脚本将仓库中的Issues添加到指定的GitHub Project中。

使用方法:
python scripts/add_issues_to_project.py --owner jacobcy --repo VibeCopilot --project-number 3
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("提示: 未安装dotenv库，将不会从.env文件加载环境变量")


def get_github_token() -> str:
    """获取GitHub令牌."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("错误: 未提供GitHub令牌，请设置GITHUB_TOKEN环境变量")
        sys.exit(1)
    return token


def get_issues(owner: str, repo: str, token: str) -> List[Dict[str, Any]]:
    """获取仓库中的所有Issue.

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        token: GitHub令牌

    Returns:
        Issue列表
    """
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"获取Issue失败: {response.status_code} - {response.text}")
        return []

    # 明确将response.json()的返回值转换为List[Dict[str, Any]]类型
    issues: List[Dict[str, Any]] = response.json()
    return issues


def get_project_id(owner: str, project_number: int, token: str) -> Optional[str]:
    """获取GitHub Project的ID.

    Args:
        owner: 项目所有者
        project_number: 项目编号
        token: GitHub令牌

    Returns:
        项目ID
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    # 使用GraphQL API获取项目ID
    query = """
    query($login: String!, $number: Int!) {
      user(login: $login) {
        projectV2(number: $number) {
          id
        }
      }
    }
    """

    variables = {"login": owner, "number": project_number}

    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": query, "variables": variables},
    )

    if response.status_code != 200 or "errors" in response.json():
        print(f"获取项目ID失败: {response.text}")
        return None

    # 明确返回类型为Optional[str]
    project_id: Optional[str] = (
        response.json().get("data", {}).get("user", {}).get("projectV2", {}).get("id")
    )

    return project_id


def add_issue_to_project(project_id: str, issue_node_id: str, token: str) -> bool:
    """将Issue添加到项目.

    Args:
        project_id: 项目ID
        issue_node_id: Issue节点ID
        token: GitHub令牌

    Returns:
        是否成功
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    # 使用GraphQL API添加Issue到项目
    query = """
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

    variables = {"projectId": project_id, "contentId": issue_node_id}

    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": query, "variables": variables},
    )

    if response.status_code != 200 or "errors" in response.json():
        print(f"添加Issue到项目失败: {response.text}")
        return False

    return True


def main() -> None:
    """主函数."""
    parser = argparse.ArgumentParser(description="将现有GitHub Issues添加到GitHub Project")
    parser.add_argument("--owner", required=True, help="仓库所有者")
    parser.add_argument("--repo", required=True, help="仓库名称")
    parser.add_argument("--project-number", required=True, type=int, help="项目编号")

    args = parser.parse_args()

    token = get_github_token()
    project_id = get_project_id(args.owner, args.project_number, token)

    if not project_id:
        print(f"无法获取项目ID，请确认项目编号 {args.project_number} 是否正确")
        sys.exit(1)

    print(f"已获取项目ID: {project_id}")

    issues = get_issues(args.owner, args.repo, token)
    print(f"找到 {len(issues)} 个Issue")

    success_count = 0
    for issue in issues:
        issue_node_id = issue.get("node_id")
        issue_number = issue.get("number")
        issue_title = issue.get("title")

        if not issue_node_id:
            print(f"跳过Issue #{issue_number}: 缺少节点ID")
            continue

        print(f"尝试添加Issue #{issue_number}: {issue_title}")

        if add_issue_to_project(project_id, issue_node_id, token):
            print(f"成功添加Issue #{issue_number}: {issue_title}")
            success_count += 1
        else:
            print(f"添加Issue #{issue_number} 失败")

    print(f"总共成功添加 {success_count}/{len(issues)} 个Issue到项目")


if __name__ == "__main__":
    main()

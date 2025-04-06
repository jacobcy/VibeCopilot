#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目分析API工具模块.

提供通用的API访问和数据处理功能。
"""

import logging
from typing import Any, Dict, List, Optional

from ....github.api import GitHubClient, GitHubIssuesClient, GitHubProjectsClient


def get_repo_data(github_client: GitHubClient, owner: str, repo: str) -> Dict[str, Any]:
    """获取仓库基本数据.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称

    Returns:
        Dict[str, Any]: 仓库数据，包含仓库信息和里程碑
    """
    logger = logging.getLogger(__name__)
    logger.info(f"获取仓库 {owner}/{repo} 数据")

    try:
        # 获取仓库
        repository = github_client.get(f"repos/{owner}/{repo}")

        # 获取里程碑
        milestones = github_client.get(f"repos/{owner}/{repo}/milestones", params={"state": "all"})
        if not isinstance(milestones, list):
            milestones = []

        return {"repository": repository, "milestones": milestones}
    except Exception as e:
        logger.error(f"获取仓库数据失败: {str(e)}")
        return {"repository": {}, "milestones": []}


def get_project_data(
    github_client: GitHubClient,
    projects_client: GitHubProjectsClient,
    issues_client: GitHubIssuesClient,
    owner: str,
    repo: str,
    project_number: int,
) -> Dict[str, Any]:
    """获取项目完整数据.

    Args:
        github_client: GitHub API客户端
        projects_client: GitHub Projects API客户端
        issues_client: GitHub Issues API客户端
        owner: 仓库所有者
        repo: 仓库名称
        project_number: 项目编号

    Returns:
        Dict[str, Any]: 项目数据
    """
    # 获取项目数据
    project_v2_data = projects_client.get_project_v2(owner, repo, project_number)

    # 获取仓库issue数据
    issues = issues_client.get_issues(owner, repo, state="all")

    # 获取仓库PR数据
    pull_requests = github_client.get(f"repos/{owner}/{repo}/pulls", params={"state": "all"})
    if not isinstance(pull_requests, list):
        pull_requests = []

    # 获取仓库里程碑数据
    milestones = github_client.get(f"repos/{owner}/{repo}/milestones", params={"state": "all"})
    if not isinstance(milestones, list):
        milestones = []

    return {
        "project_v2": project_v2_data,
        "issues": issues,
        "pull_requests": pull_requests,
        "milestones": milestones,
    }

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间线调整模块.

基于项目分析结果自动调整项目时间线。
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from ...github.api import GitHubClient, GitHubIssuesClient, GitHubProjectsClient
from .services import (
    apply_adjustments,
    apply_updates,
    apply_updates_from_file,
    calculate_adjustments,
    verify_updates,
)
from .utils import get_repo_data


class TimelineAdjuster:
    """项目时间线调整器."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        projects_client: Optional[GitHubProjectsClient] = None,
        issues_client: Optional[GitHubIssuesClient] = None,
    ):
        """初始化时间线调整器.

        Args:
            github_client: GitHub API客户端
            projects_client: GitHub Projects API客户端
            issues_client: GitHub Issues API客户端
        """
        self.github_client = github_client or GitHubClient()
        self.projects_client = projects_client or GitHubProjectsClient()
        self.issues_client = issues_client or GitHubIssuesClient()
        self.logger = logging.getLogger(__name__)

    def adjust_timeline(
        self,
        owner: str,
        repo: str,
        project_number: int,
        analysis: Dict[str, Any],
        update_milestones: bool = True,
        max_adjustment_days: int = 30,
    ) -> Dict[str, Any]:
        """调整项目时间线.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            analysis: 项目分析结果
            update_milestones: 是否更新里程碑
            max_adjustment_days: 最大调整天数限制

        Returns:
            Dict[str, Any]: 调整结果
        """
        # 获取仓库数据
        repo_data = get_repo_data(self.github_client, owner, repo)

        # 计算时间线调整
        adjustments = calculate_adjustments(analysis, repo_data, max_adjustment_days)

        # 应用调整
        applied_adjustments = apply_adjustments(
            self.github_client, owner, repo, adjustments, update_milestones
        )

        return {"date": datetime.datetime.now().isoformat(), "adjustments": applied_adjustments}

    def apply_updates_from_file(
        self, owner: str, repo: str, updates_file: str, dry_run: bool = True
    ) -> Dict[str, Any]:
        """从文件中应用更新.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates_file: 更新文件路径
            dry_run: 是否仅模拟执行

        Returns:
            Dict[str, Any]: 应用结果
        """
        return apply_updates_from_file(self.github_client, owner, repo, updates_file, dry_run)

    def apply_updates(
        self, owner: str, repo: str, updates: Dict[str, Any], dry_run: bool = True
    ) -> Dict[str, Any]:
        """应用更新.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates: 更新数据
            dry_run: 是否仅模拟执行

        Returns:
            Dict[str, Any]: 应用结果
        """
        return apply_updates(self.github_client, owner, repo, updates, dry_run)

    def verify_updates(
        self, owner: str, repo: str, updates_file: str, generate_diff: bool = True
    ) -> Dict[str, Any]:
        """验证更新结果.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates_file: 更新文件路径
            generate_diff: 是否生成差异报告

        Returns:
            Dict[str, Any]: 验证结果
        """
        return verify_updates(self.github_client, owner, repo, updates_file, generate_diff)

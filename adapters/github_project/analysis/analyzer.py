#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目分析模块.

分析GitHub项目的进度、质量和风险。
"""

from typing import Any, Dict, List, Optional

from ...github.api import GitHubClient, GitHubIssuesClient, GitHubProjectsClient
from .analyzers import analyze_progress, analyze_quality, analyze_risks, generate_report
from .utils import get_project_data


class ProjectAnalyzer:
    """项目分析器."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        projects_client: Optional[GitHubProjectsClient] = None,
        issues_client: Optional[GitHubIssuesClient] = None,
    ):
        """初始化项目分析器.

        Args:
            github_client: GitHub API客户端
            projects_client: GitHub Projects API客户端
            issues_client: GitHub Issues API客户端
        """
        self.github_client = github_client or GitHubClient()
        self.projects_client = projects_client or GitHubProjectsClient()
        self.issues_client = issues_client or GitHubIssuesClient()

    def analyze_project(
        self, owner: str, repo: str, project_number: int, metrics: List[str] = None
    ) -> Dict[str, Any]:
        """分析项目状态.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            metrics: 要分析的指标列表，默认全部分析

        Returns:
            Dict[str, Any]: 分析结果
        """
        # 默认分析所有指标
        if metrics is None:
            metrics = ["progress", "quality", "risks"]

        # 获取项目数据
        project_data = get_project_data(
            self.github_client,
            self.projects_client,
            self.issues_client,
            owner,
            repo,
            project_number,
        )

        # 分析结果
        analysis = {}

        if "progress" in metrics:
            analysis["progress"] = analyze_progress(project_data)

        if "quality" in metrics:
            analysis["quality"] = analyze_quality(project_data)

        if "risks" in metrics:
            analysis["risks"] = analyze_risks(project_data)

        return analysis

    def generate_report(self, analysis: Dict[str, Any], format_type: str = "markdown") -> str:
        """生成分析报告.

        Args:
            analysis: 分析结果
            format_type: 报告格式类型

        Returns:
            str: 格式化的报告
        """
        return generate_report(analysis, format_type)

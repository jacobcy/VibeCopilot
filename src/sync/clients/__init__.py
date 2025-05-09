#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub API客户端子模块包.

提供具体功能的API客户端类。
"""

# 导出基础客户端
from .github_client import GitHubClientBase

# 导出功能客户端
from .issues_client import GitHubIssuesClient
from .projects_client import GitHubProjectsClient
from .projects_fields import GitHubProjectFieldsClient
from .projects_items import GitHubProjectItemsClient

__all__ = [
    "GitHubClientBase",
    "GitHubIssuesClient",
    "GitHubProjectsClient",
    "GitHubProjectFieldsClient",
    "GitHubProjectItemsClient",
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目API客户端包.

此包包含与GitHub API交互的各种客户端实现，包括基础客户端、项目客户端和Issues客户端。
每个客户端都专注于特定API领域的功能。
"""

from .github_client import GitHubClientBase
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

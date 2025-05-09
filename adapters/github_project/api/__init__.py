#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub项目API包.

此包提供了与GitHub API交互的功能，包括项目、Issues和用户管理。
包含对REST API和GraphQL API的支持。

主要组件:
- GitHubClientBase - 基础API客户端
- GitHubProjectsClient - 项目管理客户端
- GitHubIssuesClient - Issue管理客户端

示例用法:
```python
from src.sync.clients import GitHubProjectsClient, GitHubIssuesClient

# 初始化项目客户端
projects_client = GitHubProjectsClient()
projects = projects_client.get_projects("octocat", "hello-world")

# 初始化Issues客户端
issues_client = GitHubIssuesClient()
issues = issues_client.get_issues("octocat", "hello-world", state="open")
```
"""

# 导出新的客户端类
from .clients import GitHubClientBase, GitHubIssuesClient, GitHubProjectFieldsClient, GitHubProjectItemsClient, GitHubProjectsClient

__all__ = [
    "GitHubClientBase",
    "GitHubIssuesClient",
    "GitHubProjectsClient",
    "GitHubProjectFieldsClient",
    "GitHubProjectItemsClient",
]

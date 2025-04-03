"""GitHub API 客户端包.

提供与GitHub API交互的客户端模块。
"""

from .github_client import GitHubClient
from .issues_client import GitHubIssuesClient
from .projects_client import GitHubProjectsClient

__all__ = ["GitHubClient", "GitHubIssuesClient", "GitHubProjectsClient"]

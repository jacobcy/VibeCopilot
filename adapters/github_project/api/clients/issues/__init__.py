#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues API子模块包.

此包包含与GitHub Issues API交互的各种专门功能模块，按功能细分。
"""

from .comments import GitHubIssueCommentsClient
from .core import GitHubIssuesCoreClient
from .labels import GitHubIssueLabelsClient
from .milestones import GitHubIssueMilestonesClient

__all__ = [
    "GitHubIssuesCoreClient",
    "GitHubIssueCommentsClient",
    "GitHubIssueLabelsClient",
    "GitHubIssueMilestonesClient",
]

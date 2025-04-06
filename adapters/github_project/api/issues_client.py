#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issues API客户端兼容层.

为保持向后兼容，此模块重定向到新的子模块。新代码应直接使用clients包。
"""

from typing import Any, Dict, List, Optional, Union

from .clients.issues_client import GitHubIssuesClient as BaseIssuesClient


class GitHubIssuesClient(BaseIssuesClient):
    """GitHub Issues API客户端兼容层.

    为保持向后兼容，此类调用专门的子客户端功能。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化客户端.

        Args:
            token: GitHub API令牌
            base_url: API基础URL
        """
        super().__init__(token, base_url)


# 对于需要支持的旧代码，可以保留这个仅用于说明的部分
if __name__ == "__main__":
    # 简单的使用示例
    client = GitHubIssuesClient()
    try:
        # 获取仓库issues列表
        owner = "octocat"
        repo = "hello-world"
        issues = client.get_issues(owner, repo, state="open")
        print(f"找到 {len(issues)} 个open状态的issues")

        # 如果有issues，获取第一个issue的评论
        if issues:
            issue_number = issues[0].get("number", 0)
            if issue_number > 0:
                comments = client.get_comments(owner, repo, issue_number)
                print(f"Issue #{issue_number} 有 {len(comments)} 条评论")
    except Exception as e:
        print(f"示例失败: {e}")

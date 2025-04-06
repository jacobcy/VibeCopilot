#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 基础API客户端兼容层.

为保持向后兼容，此模块重定向到新的子模块。新代码应直接使用clients包。
"""

import os
from typing import Any, Dict, Optional

from .clients.github_client import GitHubClientBase


class GitHubClient(GitHubClientBase):
    """GitHub API客户端兼容层.

    为保持向后兼容，此类调用专门的子客户端功能。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化GitHub客户端.

        Args:
            token: GitHub API令牌，如果为None则尝试从环境变量GITHUB_TOKEN获取
            base_url: GitHub API基础URL
        """
        # 如果未提供token，则尝试从环境变量获取
        if token is None:
            token = os.environ.get("GITHUB_TOKEN")

        super().__init__(token, base_url)


# 对于需要支持的旧代码，可以保留这个仅用于说明的部分
if __name__ == "__main__":
    # 简单的使用示例
    client = GitHubClient()
    try:
        # 获取当前用户信息
        user_info = client.get("user")
        if user_info:
            print(f"当前用户: {user_info.get('login')}")

        # 尝试一个GraphQL查询
        query = """
        query {
          viewer {
            login
            name
          }
        }
        """
        result = client.graphql(query)
        if result and "data" in result:
            viewer = result["data"]["viewer"]
            print(f"GraphQL查询结果: {viewer.get('name')} ({viewer.get('login')})")
    except Exception as e:
        print(f"示例失败: {e}")

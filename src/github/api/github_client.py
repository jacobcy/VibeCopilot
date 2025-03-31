#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub API客户端模块.

提供与GitHub API交互的基础功能，封装REST和GraphQL请求。
"""

import json
import os
from typing import Any, Dict, Optional

import requests


class GitHubClient:
    """GitHub API客户端基类."""

    def __init__(self, token: Optional[str] = None) -> None:
        """初始化GitHub API客户端.

        Args:
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("警告: 未提供GitHub令牌，API请求可能受到限制")

        self.headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.rest_url = "https://api.github.com"
        self.graphql_url = f"{self.rest_url}/graphql"

    def _make_rest_request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        """发送REST API请求.

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            endpoint: API端点，不包含基础URL
            **kwargs: 传递给requests的其他参数

        Returns:
            requests.Response: 响应对象
        """
        url = f"{self.rest_url}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)

        response = requests.request(method, url, headers=headers, **kwargs)
        return response

    def _make_graphql_request(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """发送GraphQL API请求.

        Args:
            query: GraphQL查询
            variables: 查询变量

        Returns:
            requests.Response: 响应对象
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json=payload,
        )
        return response

    def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """发送GET请求并返回JSON响应.

        Args:
            endpoint: API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应
        """
        response = self._make_rest_request("GET", endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """发送POST请求并返回JSON响应.

        Args:
            endpoint: API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应
        """
        response = self._make_rest_request("POST", endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GraphQL查询并返回JSON响应.

        Args:
            query: GraphQL查询
            variables: 查询变量

        Returns:
            Dict[str, Any]: JSON响应

        Raises:
            requests.HTTPError: 如果请求失败
            ValueError: 如果响应中包含错误
        """
        response = self._make_graphql_request(query, variables)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            error_msg = "; ".join(err.get("message", "未知错误") for err in data["errors"])
            raise ValueError(f"GraphQL查询错误: {error_msg}")

        return data


if __name__ == "__main__":
    # 简单的使用示例
    client = GitHubClient()
    try:
        # 获取GitHub用户信息
        user_data = client.get("user")
        print(f"当前用户: {user_data.get('login')}")

        # GraphQL示例查询
        query = """
        query {
          viewer {
            login
            name
          }
        }
        """
        graphql_data = client.graphql(query)
        viewer = graphql_data.get("data", {}).get("viewer", {})
        print(f"GraphQL查询结果: {viewer.get('name')} ({viewer.get('login')})")
    except Exception as e:
        print(f"示例失败: {e}")

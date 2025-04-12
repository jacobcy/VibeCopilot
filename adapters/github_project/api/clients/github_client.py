#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub API客户端基础模块.

提供GitHub API通用客户端功能，包括REST和GraphQL API调用。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import requests


class GitHubClientBase:
    """GitHub API基础客户端类.

    提供REST和GraphQL API的基础通信功能和身份验证。作为所有专用GitHub客户端的基类。
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化GitHub客户端.

        Args:
            token: GitHub个人访问令牌，如未提供则尝试从环境变量中读取
            base_url: GitHub API基础URL
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            logging.warning("未提供GitHub令牌，API访问将受到严格限制")

        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "VibeCopilot-GitHub-Client",
            }
        )

        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})

        self.logger = logging.getLogger(__name__)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """发送GET请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）
            params: 查询参数

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any]] = None) -> Any:
        """发送POST请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）
            json: JSON请求体
            payload: 表单数据请求体

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=json, data=payload)
        response.raise_for_status()
        return response.json() if response.content else None

    def patch(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """发送PATCH请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）
            json: JSON请求体

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.patch(url, json=json)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """发送PUT请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）
            json: JSON请求体

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.put(url, json=json)
        response.raise_for_status()
        return response.json() if response.content else None

    def delete(self, endpoint: str) -> Any:
        """发送DELETE请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        url = f"{self.base_url}/{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json() if response.content else None

    def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GraphQL查询到GitHub API.

        Args:
            query: GraphQL查询字符串
            variables: 查询变量

        Returns:
            Dict[str, Any]: GraphQL响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
            ValueError: 当响应包含错误时
        """
        graphql_url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(graphql_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            error_message = "; ".join([error.get("message", "未知错误") for error in result["errors"]])
            self.logger.error(f"GraphQL查询错误: {error_message}")
            raise ValueError(f"GraphQL查询错误: {error_message}")

        return result

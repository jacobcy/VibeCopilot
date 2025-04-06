#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub API基础客户端模块.

提供与GitHub API交互的基础功能，封装REST和GraphQL请求处理。
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

import requests

logger = logging.getLogger(__name__)


class GitHubClientBase:
    """GitHub API客户端基类，提供REST和GraphQL API交互功能."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化GitHub API客户端.

        Args:
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
            base_url: GitHub API的基础URL
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            logger.warning("未提供GitHub令牌，API请求可能受到限制")

        self.headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.rest_url = base_url
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

        logger.debug(f"发送 {method} 请求到 {url}")
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

        logger.debug(f"发送GraphQL请求到 {self.graphql_url}")

        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json=payload,
        )
        return response

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        """发送GET请求并返回JSON响应.

        Args:
            endpoint: API端点
            params: URL查询参数
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        try:
            response = self._make_rest_request("GET", endpoint, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"GET请求失败: {endpoint} - {str(e)}")
            raise

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        """发送POST请求并返回JSON响应.

        Args:
            endpoint: API端点
            json: 请求体JSON数据
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        try:
            response = self._make_rest_request("POST", endpoint, json=json, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"POST请求失败: {endpoint} - {str(e)}")
            raise

    def patch(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        """发送PATCH请求并返回JSON响应.

        Args:
            endpoint: API端点
            json: 请求体JSON数据
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        try:
            response = self._make_rest_request("PATCH", endpoint, json=json, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"PATCH请求失败: {endpoint} - {str(e)}")
            raise

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        """发送PUT请求并返回JSON响应.

        Args:
            endpoint: API端点
            json: 请求体JSON数据
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        try:
            response = self._make_rest_request("PUT", endpoint, json=json, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"PUT请求失败: {endpoint} - {str(e)}")
            raise

    def delete(self, endpoint: str, **kwargs: Any) -> Any:
        """发送DELETE请求并返回JSON响应.

        Args:
            endpoint: API端点
            **kwargs: 传递给requests的其他参数

        Returns:
            Dict[str, Any]: JSON响应，如果响应为空则返回None

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        try:
            response = self._make_rest_request("DELETE", endpoint, **kwargs)
            response.raise_for_status()
            # DELETE请求可能返回空响应
            return response.json() if response.content else None
        except requests.HTTPError as e:
            logger.error(f"DELETE请求失败: {endpoint} - {str(e)}")
            raise

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
        try:
            response = self._make_graphql_request(query, variables)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                error_msg = "; ".join(err.get("message", "未知错误") for err in data["errors"])
                logger.error(f"GraphQL查询错误: {error_msg}")
                raise ValueError(f"GraphQL查询错误: {error_msg}")

            return data
        except (requests.HTTPError, ValueError) as e:
            logger.error(f"GraphQL请求失败: {str(e)}")
            raise


class GitHubClient(GitHubClientBase):
    """GitHub API客户端，继承基类功能，可扩展特定功能."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        """初始化GitHub API客户端.

        Args:
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
            base_url: GitHub API的基础URL
        """
        super().__init__(token, base_url)
        self.logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)

    # 简单的使用示例
    client = GitHubClient()
    try:
        # 获取当前用户信息
        user_info = client.get("user")
        if user_info:
            logger.info(f"当前用户: {user_info.get('login')}")

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
            logger.info(f"GraphQL查询结果: {viewer.get('name')} ({viewer.get('login')})")
    except Exception as e:
        logger.error(f"示例失败: {e}")

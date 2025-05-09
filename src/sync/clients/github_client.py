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

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

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
        return self._request("get", endpoint, params=params)

    def post(self, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        """发送POST请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）
            payload: 表单数据请求体

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self._request("post", endpoint, json=payload)

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
        return self._request("patch", endpoint, json=json)

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
        return self._request("put", endpoint, json=json)

    def delete(self, endpoint: str) -> Any:
        """发送DELETE请求到GitHub REST API.

        Args:
            endpoint: API端点路径（不含基础URL）

        Returns:
            Any: API响应数据

        Raises:
            requests.HTTPError: 当API请求失败时
        """
        return self._request("delete", endpoint)

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

        # 打印请求详情，省略查询正文以避免日志过长
        self.logger.debug(f"发送GraphQL请求到 {graphql_url}")
        self.logger.debug(f"GraphQL请求变量: {variables}")
        self.logger.debug(f"GraphQL请求头(Authorization已隐藏): {{'Content-Type': {headers.get('Content-Type')}}}")

        try:
            response = requests.post(graphql_url, json=payload, headers=headers)

            # 记录HTTP状态
            self.logger.debug(f"GraphQL响应状态码: {response.status_code}")

            # 如果出现HTTP错误，记录详细信息
            if response.status_code >= 400:
                self.logger.error(f"GraphQL HTTP错误: 状态码 {response.status_code}, 响应: {response.text}")
                response.raise_for_status()

            result = response.json()

            # 检查并处理GraphQL错误
            if "errors" in result:
                errors = result.get("errors", [])
                error_messages = []
                error_types = []

                # 提取错误详情
                for error in errors:
                    message = error.get("message", "未知错误")
                    error_type = error.get("type", "未知类型")
                    locations = error.get("locations", [])
                    path = error.get("path", [])

                    error_messages.append(message)
                    error_types.append(error_type)

                    # 记录详细错误信息
                    self.logger.error(f"GraphQL错误: {message}, 类型: {error_type}, 位置: {locations}, 路径: {path}")

                # 合并错误消息
                error_message = "; ".join(error_messages)

                # 记录总结错误
                self.logger.error(f"GraphQL查询错误: {error_message}")

                # 包含更多错误细节在异常中
                full_error = {"message": error_message, "types": error_types, "variables": variables}
                raise ValueError(f"GraphQL查询错误: {error_message}", full_error)

            return result

        except requests.RequestException as e:
            self.logger.error(f"GraphQL请求异常: {e}")
            raise
        except ValueError as e:
            # 已经记录了GraphQL错误，直接抛出
            raise
        except Exception as e:
            self.logger.error(f"GraphQL请求未预期的异常: {e}")
            raise

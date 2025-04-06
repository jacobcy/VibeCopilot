"""
HTTP客户端模块

提供与n8n API通信的基础HTTP请求封装
"""

import logging
import os
from typing import Any, Dict, Optional

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class N8nHttpClient:
    """n8n HTTP客户端类"""

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30
    ):
        """初始化HTTP客户端

        Args:
            base_url: n8n API基础URL，如果未提供则从环境变量获取
            api_key: n8n API密钥，如果未提供则从环境变量获取
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or os.environ.get("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.environ.get("N8N_API_KEY", "")
        self.timeout = timeout

        # 移除URL末尾的斜杠
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        # 验证配置
        if not self.base_url:
            logger.warning("n8n基础URL未配置，将使用默认值http://localhost:5678")
        if not self.api_key:
            logger.warning("n8n API密钥未配置，可能导致认证失败")

    def get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    def make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求

        Args:
            method: HTTP方法（GET, POST, PUT, DELETE）
            endpoint: API端点
            data: 请求数据

        Returns:
            响应数据

        Raises:
            RequestException: 请求失败
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self.get_headers()
        response_data = {}

        try:
            logger.debug(f"发送{method}请求至{url}")
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            if response.content:
                response_data = response.json()
            logger.debug(f"请求成功，状态码: {response.status_code}")
            return response_data
        except RequestException as e:
            logger.error(f"n8n API请求失败: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"解析响应失败: {str(e)}")
            raise RequestException(f"解析响应失败: {str(e)}")

    def webhook_request(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送Webhook请求

        Args:
            webhook_url: Webhook URL
            payload: 请求数据

        Returns:
            响应数据

        Raises:
            RequestException: 请求失败
        """
        headers = {"Content-Type": "application/json"}
        try:
            logger.debug(f"发送Webhook请求至{webhook_url}")
            response = requests.post(
                webhook_url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json() if response.content else {}
            logger.debug("Webhook请求成功")
            return result
        except RequestException as e:
            logger.error(f"Webhook请求失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """测试连接

        Returns:
            连接是否可用
        """
        try:
            self.make_request("GET", "api/v1/workflows", {})
            return True
        except Exception:
            return False

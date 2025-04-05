"""
n8n适配器模块

封装与n8n API的交互，提供工作流触发、状态查询等功能。
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class N8nAdapter:
    """n8n适配器类"""

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30
    ):
        """初始化n8n适配器

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

    def _get_headers(self) -> Dict[str, str]:
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

    def _make_request(
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
        headers = self._get_headers()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=headers, json=data, timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=headers, json=data, timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}
        except RequestException as e:
            logger.error(f"n8n API请求失败: {str(e)}")
            raise

    def get_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流

        Returns:
            工作流列表
        """
        try:
            return self._make_request("GET", "api/v1/workflows")
        except RequestException:
            logger.exception("获取工作流列表失败")
            return []

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取指定工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流信息或None
        """
        try:
            return self._make_request("GET", f"api/v1/workflows/{workflow_id}")
        except RequestException:
            logger.exception(f"获取工作流失败: {workflow_id}")
            return None

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建工作流

        Args:
            workflow_data: 工作流数据

        Returns:
            创建的工作流信息或None
        """
        try:
            return self._make_request("POST", "api/v1/workflows", workflow_data)
        except RequestException:
            logger.exception("创建工作流失败")
            return None

    def update_workflow(
        self, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新工作流

        Args:
            workflow_id: 工作流ID
            workflow_data: 工作流数据

        Returns:
            更新后的工作流信息或None
        """
        try:
            return self._make_request(
                "PUT", f"api/v1/workflows/{workflow_id}", workflow_data
            )
        except RequestException:
            logger.exception(f"更新工作流失败: {workflow_id}")
            return None

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            是否删除成功
        """
        try:
            self._make_request("DELETE", f"api/v1/workflows/{workflow_id}")
            return True
        except RequestException:
            logger.exception(f"删除工作流失败: {workflow_id}")
            return False

    def activate_workflow(self, workflow_id: str) -> bool:
        """激活工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            是否激活成功
        """
        try:
            self._make_request("POST", f"api/v1/workflows/{workflow_id}/activate")
            return True
        except RequestException:
            logger.exception(f"激活工作流失败: {workflow_id}")
            return False

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """停用工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            是否停用成功
        """
        try:
            self._make_request("POST", f"api/v1/workflows/{workflow_id}/deactivate")
            return True
        except RequestException:
            logger.exception(f"停用工作流失败: {workflow_id}")
            return False

    def trigger_workflow(
        self, workflow_id: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """触发工作流执行

        Args:
            workflow_id: 工作流ID
            payload: 触发数据

        Returns:
            执行信息或None
        """
        try:
            return self._make_request(
                "POST", f"api/v1/workflows/{workflow_id}/execute", payload
            )
        except RequestException:
            logger.exception(f"触发工作流失败: {workflow_id}")
            return None

    def trigger_workflow_by_webhook(
        self, webhook_url: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """通过Webhook触发工作流

        Args:
            webhook_url: Webhook URL
            payload: 触发数据

        Returns:
            响应数据或None
        """
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                webhook_url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except RequestException:
            logger.exception(f"通过Webhook触发工作流失败: {webhook_url}")
            return None

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行信息

        Args:
            execution_id: 执行ID

        Returns:
            执行信息或None
        """
        try:
            return self._make_request("GET", f"api/v1/executions/{execution_id}")
        except RequestException:
            logger.exception(f"获取执行信息失败: {execution_id}")
            return None

    def get_workflow_executions(
        self, workflow_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取工作流执行历史

        Args:
            workflow_id: 工作流ID
            limit: 返回记录数量限制

        Returns:
            执行历史列表
        """
        try:
            return self._make_request(
                "GET", f"api/v1/workflows/{workflow_id}/executions?limit={limit}"
            )
        except RequestException:
            logger.exception(f"获取工作流执行历史失败: {workflow_id}")
            return []

    def stop_execution(self, execution_id: str) -> bool:
        """停止执行

        Args:
            execution_id: 执行ID

        Returns:
            是否停止成功
        """
        try:
            self._make_request("POST", f"api/v1/executions/{execution_id}/stop")
            return True
        except RequestException:
            logger.exception(f"停止执行失败: {execution_id}")
            return False

    def get_credentials(self) -> List[Dict[str, Any]]:
        """获取所有凭证

        Returns:
            凭证列表
        """
        try:
            return self._make_request("GET", "api/v1/credentials")
        except RequestException:
            logger.exception("获取凭证列表失败")
            return []

    def get_credential_types(self) -> List[Dict[str, Any]]:
        """获取所有凭证类型

        Returns:
            凭证类型列表
        """
        try:
            return self._make_request("GET", "api/v1/credential-types")
        except RequestException:
            logger.exception("获取凭证类型列表失败")
            return []

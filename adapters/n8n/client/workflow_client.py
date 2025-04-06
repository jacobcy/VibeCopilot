"""
工作流管理模块

提供n8n工作流和执行的管理功能
"""

import logging
from typing import Any, Dict, List, Optional

from requests.exceptions import RequestException

from adapters.n8n.client.http_client import N8nHttpClient

logger = logging.getLogger(__name__)


class N8nWorkflowClient:
    """n8n工作流客户端类"""

    def __init__(self, http_client: N8nHttpClient):
        """初始化工作流客户端

        Args:
            http_client: HTTP客户端
        """
        self.http_client = http_client

    def get_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流

        Returns:
            工作流列表
        """
        try:
            return self.http_client.make_request("GET", "api/v1/workflows")
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
            return self.http_client.make_request("GET", f"api/v1/workflows/{workflow_id}")
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
            return self.http_client.make_request("POST", "api/v1/workflows", workflow_data)
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
            return self.http_client.make_request(
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
            self.http_client.make_request("DELETE", f"api/v1/workflows/{workflow_id}")
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
            self.http_client.make_request("POST", f"api/v1/workflows/{workflow_id}/activate")
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
            self.http_client.make_request("POST", f"api/v1/workflows/{workflow_id}/deactivate")
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
            return self.http_client.make_request(
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
            return self.http_client.webhook_request(webhook_url, payload)
        except RequestException:
            logger.exception(f"通过Webhook触发工作流失败: {webhook_url}")
            return None

    def get_workflow_executions(self, workflow_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取工作流执行历史

        Args:
            workflow_id: 工作流ID
            limit: 返回记录数量限制

        Returns:
            执行历史列表
        """
        try:
            return self.http_client.make_request(
                "GET", f"api/v1/workflows/{workflow_id}/executions?limit={limit}"
            )
        except RequestException:
            logger.exception(f"获取工作流执行历史失败: {workflow_id}")
            return []

"""
n8n适配器模块 (兼容层)

提供与n8n API交互的适配器。此模块为兼容层，新代码应直接使用client包中的模块。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from adapters.n8n.client import (
    N8nCredentialClient,
    N8nExecutionClient,
    N8nHttpClient,
    N8nVariableClient,
    N8nWorkflowClient,
)

logger = logging.getLogger(__name__)


class N8nAdapter:
    """n8n适配器类，提供与n8n API交互的能力"""

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30
    ):
        """初始化n8n适配器

        Args:
            base_url: n8n API基础URL，如果未提供则从环境变量获取
            api_key: n8n API密钥，如果未提供则从环境变量获取
            timeout: 请求超时时间（秒）
        """
        # 初始化HTTP客户端
        self.http_client = N8nHttpClient(base_url, api_key, timeout)

        # 初始化各功能客户端
        self.workflow_client = N8nWorkflowClient(self.http_client)
        self.execution_client = N8nExecutionClient(self.http_client)
        self.credential_client = N8nCredentialClient(self.http_client)
        self.variable_client = N8nVariableClient(self.http_client)

        logger.info("n8n适配器初始化完成")

    # 向后兼容的工作流管理方法

    def get_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流"""
        return self.workflow_client.get_workflows()

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取指定工作流"""
        return self.workflow_client.get_workflow(workflow_id)

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建工作流"""
        return self.workflow_client.create_workflow(workflow_data)

    def update_workflow(
        self, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新工作流"""
        return self.workflow_client.update_workflow(workflow_id, workflow_data)

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        return self.workflow_client.delete_workflow(workflow_id)

    def activate_workflow(self, workflow_id: str) -> bool:
        """激活工作流"""
        return self.workflow_client.activate_workflow(workflow_id)

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """停用工作流"""
        return self.workflow_client.deactivate_workflow(workflow_id)

    def trigger_workflow(
        self, workflow_id: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """触发工作流执行"""
        return self.workflow_client.trigger_workflow(workflow_id, payload)

    def trigger_workflow_by_webhook(
        self, webhook_url: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """通过Webhook触发工作流"""
        return self.workflow_client.trigger_workflow_by_webhook(webhook_url, payload)

    def get_workflow_executions(self, workflow_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取工作流执行历史"""
        return self.workflow_client.get_workflow_executions(workflow_id, limit)

    # 向后兼容的执行管理方法

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行详情"""
        return self.execution_client.get_execution(execution_id)

    def stop_execution(self, execution_id: str) -> bool:
        """停止执行"""
        return self.execution_client.stop_execution(execution_id)

    def delete_execution(self, execution_id: str) -> bool:
        """删除执行记录"""
        return self.execution_client.delete_execution(execution_id)

    def get_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取所有执行记录"""
        return self.execution_client.get_executions(limit)

    # 向后兼容的凭证管理方法

    def get_credentials(self) -> List[Dict[str, Any]]:
        """获取所有凭证"""
        return self.credential_client.get_credentials()

    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """获取指定凭证"""
        return self.credential_client.get_credential(credential_id)

    def create_credential(
        self, credential_type_name: str, credential_data: Dict[str, Any], name: str
    ) -> Optional[Dict[str, Any]]:
        """创建凭证"""
        return self.credential_client.create_credential(credential_type_name, credential_data, name)

    def update_credential(
        self, credential_id: str, credential_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新凭证"""
        return self.credential_client.update_credential(credential_id, credential_data)

    def delete_credential(self, credential_id: str) -> bool:
        """删除凭证"""
        return self.credential_client.delete_credential(credential_id)

    def get_credential_types(self) -> List[Dict[str, Any]]:
        """获取凭证类型"""
        return self.credential_client.get_credential_types()

    # 向后兼容的变量管理方法

    def get_variables(self) -> List[Dict[str, Any]]:
        """获取所有变量"""
        return self.variable_client.get_variables()

    def get_variable(self, variable_id: str) -> Optional[Dict[str, Any]]:
        """获取指定变量"""
        return self.variable_client.get_variable(variable_id)

    def create_variable(
        self, key: str, value: str, description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """创建变量"""
        return self.variable_client.create_variable(key, value, description)

    def update_variable(self, variable_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新变量"""
        return self.variable_client.update_variable(variable_id, data)

    def delete_variable(self, variable_id: str) -> bool:
        """删除变量"""
        return self.variable_client.delete_variable(variable_id)

    # 基础方法兼容

    def make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        return self.http_client.make_request(method, endpoint, data)

    def webhook_request(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送Webhook请求"""
        return self.http_client.webhook_request(webhook_url, payload)

    def test_connection(self) -> bool:
        """测试连接"""
        return self.http_client.test_connection()

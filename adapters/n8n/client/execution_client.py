"""
执行管理模块

提供n8n执行的管理功能
"""

import logging
from typing import Any, Dict, List, Optional

from requests.exceptions import RequestException

from adapters.n8n.client.http_client import N8nHttpClient

logger = logging.getLogger(__name__)


class N8nExecutionClient:
    """n8n执行客户端类"""

    def __init__(self, http_client: N8nHttpClient):
        """初始化执行客户端

        Args:
            http_client: HTTP客户端
        """
        self.http_client = http_client

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行详情

        Args:
            execution_id: 执行ID

        Returns:
            执行详情或None
        """
        try:
            return self.http_client.make_request("GET", f"api/v1/executions/{execution_id}")
        except RequestException:
            logger.exception(f"获取执行详情失败: {execution_id}")
            return None

    def stop_execution(self, execution_id: str) -> bool:
        """停止执行

        Args:
            execution_id: 执行ID

        Returns:
            是否停止成功
        """
        try:
            self.http_client.make_request("POST", f"api/v1/executions/{execution_id}/stop")
            return True
        except RequestException:
            logger.exception(f"停止执行失败: {execution_id}")
            return False

    def delete_execution(self, execution_id: str) -> bool:
        """删除执行记录

        Args:
            execution_id: 执行ID

        Returns:
            是否删除成功
        """
        try:
            self.http_client.make_request("DELETE", f"api/v1/executions/{execution_id}")
            return True
        except RequestException:
            logger.exception(f"删除执行记录失败: {execution_id}")
            return False

    def get_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取所有执行记录

        Args:
            limit: 返回记录数量限制

        Returns:
            执行记录列表
        """
        try:
            return self.http_client.make_request("GET", f"api/v1/executions?limit={limit}")
        except RequestException:
            logger.exception("获取执行记录列表失败")
            return []

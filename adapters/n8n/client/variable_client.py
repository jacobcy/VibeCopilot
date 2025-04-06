"""
变量管理模块

提供n8n变量的管理功能
"""

import logging
from typing import Any, Dict, List, Optional

from requests.exceptions import RequestException

from adapters.n8n.client.http_client import N8nHttpClient

logger = logging.getLogger(__name__)


class N8nVariableClient:
    """n8n变量客户端类"""

    def __init__(self, http_client: N8nHttpClient):
        """初始化变量客户端

        Args:
            http_client: HTTP客户端
        """
        self.http_client = http_client

    def get_variables(self) -> List[Dict[str, Any]]:
        """获取所有变量

        Returns:
            变量列表
        """
        try:
            return self.http_client.make_request("GET", "api/v1/variables")
        except RequestException:
            logger.exception("获取变量列表失败")
            return []

    def get_variable(self, variable_id: str) -> Optional[Dict[str, Any]]:
        """获取指定变量

        Args:
            variable_id: 变量ID

        Returns:
            变量信息或None
        """
        try:
            return self.http_client.make_request("GET", f"api/v1/variables/{variable_id}")
        except RequestException:
            logger.exception(f"获取变量失败: {variable_id}")
            return None

    def create_variable(
        self, key: str, value: str, description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """创建变量

        Args:
            key: 变量键名
            value: 变量值
            description: 变量描述

        Returns:
            创建的变量信息或None
        """
        data = {
            "key": key,
            "value": value,
            "description": description,
        }
        try:
            return self.http_client.make_request("POST", "api/v1/variables", data)
        except RequestException:
            logger.exception(f"创建变量失败: {key}")
            return None

    def update_variable(self, variable_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新变量

        Args:
            variable_id: 变量ID
            data: 变量数据

        Returns:
            更新后的变量信息或None
        """
        try:
            return self.http_client.make_request("PATCH", f"api/v1/variables/{variable_id}", data)
        except RequestException:
            logger.exception(f"更新变量失败: {variable_id}")
            return None

    def delete_variable(self, variable_id: str) -> bool:
        """删除变量

        Args:
            variable_id: 变量ID

        Returns:
            是否删除成功
        """
        try:
            self.http_client.make_request("DELETE", f"api/v1/variables/{variable_id}")
            return True
        except RequestException:
            logger.exception(f"删除变量失败: {variable_id}")
            return False

"""
凭证管理模块

提供n8n凭证的管理功能
"""

import logging
from typing import Any, Dict, List, Optional

from requests.exceptions import RequestException

from adapters.n8n.client.http_client import N8nHttpClient

logger = logging.getLogger(__name__)


class N8nCredentialClient:
    """n8n凭证客户端类"""

    def __init__(self, http_client: N8nHttpClient):
        """初始化凭证客户端

        Args:
            http_client: HTTP客户端
        """
        self.http_client = http_client

    def get_credentials(self) -> List[Dict[str, Any]]:
        """获取所有凭证

        Returns:
            凭证列表
        """
        try:
            return self.http_client.make_request("GET", "api/v1/credentials")
        except RequestException:
            logger.exception("获取凭证列表失败")
            return []

    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """获取指定凭证

        Args:
            credential_id: 凭证ID

        Returns:
            凭证信息或None
        """
        try:
            return self.http_client.make_request("GET", f"api/v1/credentials/{credential_id}")
        except RequestException:
            logger.exception(f"获取凭证失败: {credential_id}")
            return None

    def create_credential(
        self, credential_type_name: str, credential_data: Dict[str, Any], name: str
    ) -> Optional[Dict[str, Any]]:
        """创建凭证

        Args:
            credential_type_name: 凭证类型名称
            credential_data: 凭证数据
            name: 凭证名称

        Returns:
            创建的凭证信息或None
        """
        data = {
            "name": name,
            "type": credential_type_name,
            "data": credential_data,
        }
        try:
            return self.http_client.make_request("POST", "api/v1/credentials", data)
        except RequestException:
            logger.exception(f"创建凭证失败: {name}")
            return None

    def update_credential(
        self, credential_id: str, credential_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新凭证

        Args:
            credential_id: 凭证ID
            credential_data: 凭证数据

        Returns:
            更新后的凭证信息或None
        """
        try:
            return self.http_client.make_request(
                "PUT", f"api/v1/credentials/{credential_id}", credential_data
            )
        except RequestException:
            logger.exception(f"更新凭证失败: {credential_id}")
            return None

    def delete_credential(self, credential_id: str) -> bool:
        """删除凭证

        Args:
            credential_id: 凭证ID

        Returns:
            是否删除成功
        """
        try:
            self.http_client.make_request("DELETE", f"api/v1/credentials/{credential_id}")
            return True
        except RequestException:
            logger.exception(f"删除凭证失败: {credential_id}")
            return False

    def get_credential_types(self) -> List[Dict[str, Any]]:
        """获取凭证类型

        Returns:
            凭证类型列表
        """
        try:
            return self.http_client.make_request("GET", "api/v1/credential-types")
        except RequestException:
            logger.exception("获取凭证类型列表失败")
            return []

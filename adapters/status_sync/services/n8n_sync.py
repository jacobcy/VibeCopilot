"""
N8n同步服务

负责同步数据到n8n系统并管理变量与凭证
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from adapters.n8n.adapter import N8nAdapter

logger = logging.getLogger(__name__)


class N8nSync:
    """N8n同步服务类"""

    def __init__(
        self,
        db_session: Session,
        n8n_adapter: Optional[N8nAdapter] = None,
    ):
        """初始化N8n同步服务

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器实例
        """
        self.db_session = db_session
        self.n8n_adapter = n8n_adapter

    def sync_variable(self, key: str, value: Any) -> bool:
        """同步变量到n8n

        Args:
            key: 变量名
            value: 变量值

        Returns:
            是否同步成功
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return False

            # 检查变量是否存在
            existing = self.n8n_adapter.get_variable(key)

            if existing:
                # 更新变量
                result = self.n8n_adapter.update_variable(key, value)
                if result:
                    logger.info(f"更新n8n变量: {key}")
                    return True
                else:
                    logger.error(f"更新n8n变量失败: {key}")
                    return False
            else:
                # 创建变量
                result = self.n8n_adapter.create_variable(key, value)
                if result:
                    logger.info(f"创建n8n变量: {key}")
                    return True
                else:
                    logger.error(f"创建n8n变量失败: {key}")
                    return False

        except Exception as e:
            logger.exception(f"同步变量到n8n失败: {str(e)}")
            return False

    def sync_credentials(self, credential_type: str, credential_data: Dict[str, Any]) -> bool:
        """同步凭证到n8n

        Args:
            credential_type: 凭证类型
            credential_data: 凭证数据

        Returns:
            是否同步成功
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return False

            # 安全检查
            if "name" not in credential_data:
                logger.error("凭证数据缺少name字段")
                return False

            # 检查凭证是否存在
            existing = self.n8n_adapter.get_credential_by_name(credential_data["name"])

            if existing:
                # 更新凭证
                result = self.n8n_adapter.update_credential(
                    existing["id"], credential_type, credential_data
                )
                if result:
                    logger.info(f"更新n8n凭证: {credential_data['name']}")
                    return True
                else:
                    logger.error(f"更新n8n凭证失败: {credential_data['name']}")
                    return False
            else:
                # 创建凭证
                result = self.n8n_adapter.create_credential(credential_type, credential_data)
                if result:
                    logger.info(f"创建n8n凭证: {credential_data['name']}")
                    return True
                else:
                    logger.error(f"创建n8n凭证失败: {credential_data['name']}")
                    return False

        except Exception as e:
            logger.exception(f"同步凭证到n8n失败: {str(e)}")
            return False

    def get_all_variables(self) -> List[Dict[str, Any]]:
        """获取所有n8n变量

        Returns:
            变量列表
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return []

            return self.n8n_adapter.get_all_variables()
        except Exception as e:
            logger.exception(f"获取n8n变量失败: {str(e)}")
            return []

    def get_all_credentials(self) -> List[Dict[str, Any]]:
        """获取所有n8n凭证

        Returns:
            凭证列表
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return []

            return self.n8n_adapter.get_all_credentials()
        except Exception as e:
            logger.exception(f"获取n8n凭证失败: {str(e)}")
            return []

    def test_connection(self) -> bool:
        """测试n8n连接

        Returns:
            是否连接成功
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return False

            return self.n8n_adapter.test_connection()
        except Exception as e:
            logger.exception(f"测试n8n连接失败: {str(e)}")
            return False

    def update_system_variables(self, variables: Dict[str, Any]) -> Dict[str, bool]:
        """批量更新系统变量

        Args:
            variables: 变量字典

        Returns:
            各变量更新结果
        """
        results = {}

        for key, value in variables.items():
            results[key] = self.sync_variable(key, value)

        return results

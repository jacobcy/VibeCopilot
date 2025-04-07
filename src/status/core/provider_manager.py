"""
状态提供者管理器模块

管理状态提供者的注册和获取。
"""

import logging
from typing import Any, Dict, List, Optional, Set

from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """状态提供者管理器

    管理状态提供者的注册和获取。
    """

    def __init__(self):
        """初始化提供者管理器"""
        self._providers: Dict[str, IStatusProvider] = {}

    def register_provider(self, provider: IStatusProvider) -> None:
        """注册状态提供者

        Args:
            provider: 状态提供者
        """
        domain = provider.domain
        if domain in self._providers:
            logger.warning(f"重复注册状态提供者: {domain}")

        self._providers[domain] = provider
        logger.info(f"已注册状态提供者: {domain}")

    def get_provider(self, domain: str) -> Optional[IStatusProvider]:
        """获取指定领域的状态提供者

        Args:
            domain: 领域名称

        Returns:
            状态提供者或None（如果不存在）
        """
        return self._providers.get(domain)

    def get_domains(self) -> List[str]:
        """获取所有可用的领域名称

        Returns:
            领域名称列表
        """
        return list(self._providers.keys())

    def get_all_providers(self) -> Dict[str, IStatusProvider]:
        """获取所有状态提供者

        Returns:
            领域名称到状态提供者的映射
        """
        return self._providers

    def has_provider(self, domain: str) -> bool:
        """检查是否存在指定领域的状态提供者

        Args:
            domain: 领域名称

        Returns:
            是否存在
        """
        return domain in self._providers

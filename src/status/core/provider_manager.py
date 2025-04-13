"""
状态提供者管理器模块

管理状态提供者的注册和获取。
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union

from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class FunctionStatusProvider(IStatusProvider):
    """函数式状态提供者包装器

    优化版本：为简单函数提供状态提供者接口封装，
    提供合理的默认实现来避免冗余代码
    """

    def __init__(self, domain: str, provider_func: Callable[[], Any]):
        self._domain = domain
        self._provider_func = provider_func
        self._entities = {}

    @property
    def domain(self) -> str:
        return self._domain

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取状态信息

        简化为：如果提供了entity_id，返回该实体的状态 (如果存在)
        否则，调用提供者函数获取整体状态

        Args:
            entity_id: 可选，实体ID

        Returns:
            Dict[str, Any]: 状态信息
        """
        if entity_id is not None:
            return self._entities.get(entity_id, {"error": "实体不存在", "domain": self._domain})

        # 获取提供者函数返回的状态，并增加domain字段
        status = self._provider_func()
        if isinstance(status, dict) and "domain" not in status:
            status["domain"] = self._domain
        return status

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新状态

        函数式提供者简化实现：更新_entities中的状态，但不实际持久化
        """
        if entity_id not in self._entities:
            self._entities[entity_id] = {}

        self._entities[entity_id]["status"] = status
        self._entities[entity_id].update(kwargs)

        return {"updated": True, "entity_id": entity_id, "status": status, "domain": self._domain}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出实体

        函数式提供者简化实现：返回内存中跟踪的实体
        """
        entities = []
        for entity_id, entity_data in self._entities.items():
            entity_status = entity_data.get("status")
            if status is None or entity_status == status:
                entities.append(
                    {
                        "id": entity_id,
                        "status": entity_status,
                        "type": "generic",
                        "domain": self._domain,
                        **{k: v for k, v in entity_data.items() if k not in ["status"]},
                    }
                )
        return entities


class ProviderManager:
    """状态提供者管理器

    管理状态提供者的注册和获取。
    """

    def __init__(self):
        """初始化提供者管理器"""
        self._providers: Dict[str, IStatusProvider] = {}

    def register_provider(self, domain: str, provider: Union[IStatusProvider, Callable[[], Any]]) -> None:
        """注册状态提供者

        Args:
            domain: 领域名称
            provider: 状态提供者或提供者函数
        """
        if domain in self._providers:
            logger.warning(f"重复注册状态提供者: {domain}，这可能导致不一致的行为")
            # 返回而不覆盖现有提供者，避免重复注册问题
            return

        if isinstance(provider, IStatusProvider):
            self._providers[domain] = provider
        else:
            self._providers[domain] = FunctionStatusProvider(domain, provider)

        logger.info(f"已注册状态提供者: {domain}")

    def unregister_provider(self, domain: str) -> bool:
        """注销状态提供者

        Args:
            domain: 领域名称

        Returns:
            bool: 是否成功注销
        """
        if domain in self._providers:
            del self._providers[domain]
            logger.info(f"已注销状态提供者: {domain}")
            return True
        return False

    def has_provider(self, domain: str) -> bool:
        """检查是否存在指定领域的提供者

        Args:
            domain: 领域名称

        Returns:
            bool: 是否存在提供者
        """
        return domain in self._providers

    def get_status(self, domain: str) -> Optional[Any]:
        """获取指定领域的状态

        Args:
            domain: 领域名称

        Returns:
            状态数据或None（如果不存在）
        """
        provider = self._providers.get(domain)
        if provider:
            return provider.get_status()
        return None

    def get_all_status(self) -> Dict[str, Any]:
        """获取所有领域的状态

        Returns:
            领域名称到状态数据的映射
        """
        result = {}
        for domain, provider in self._providers.items():
            try:
                result[domain] = provider.get_status()
            except Exception as e:
                logger.error(f"获取领域 '{domain}' 状态时出错: {e}")
                result[domain] = {"error": str(e), "domain": domain}
        return result

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

    def get_provider(self, domain: str) -> Optional[IStatusProvider]:
        """获取指定域的状态提供者

        Args:
            domain: 状态域名称

        Returns:
            StatusProvider: 状态提供者实例或None
        """
        return self._providers.get(domain)

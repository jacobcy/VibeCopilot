"""
状态服务模块

提供统一的状态管理服务，聚合各个领域的状态提供者。
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.status.interfaces import IStatusProvider, IStatusSubscriber

logger = logging.getLogger(__name__)


class StatusService:
    """状态服务

    聚合各个领域的状态提供者，提供统一的状态查询和管理接口。
    """

    _instance = None

    @classmethod
    def get_instance(cls) -> "StatusService":
        """获取单例实例

        Returns:
            StatusService: 单例实例
        """
        if cls._instance is None:
            cls._instance = StatusService()
        return cls._instance

    def __init__(self):
        """初始化状态服务"""
        self._providers: Dict[str, IStatusProvider] = {}
        self._subscribers: List[IStatusSubscriber] = []
        self._initialized = False

    def initialize(self) -> None:
        """初始化服务

        注册默认的状态提供者。这个方法应该在应用启动时调用一次。
        """
        if self._initialized:
            return

        try:
            # 注册路线图状态提供者
            from src.roadmap import RoadmapService
            from src.status.providers.roadmap_provider import RoadmapStatusProvider

            roadmap_service = RoadmapService()
            self.register_provider(RoadmapStatusProvider(roadmap_service))

            # 注册工作流状态提供者
            from src.status.providers.workflow_provider import WorkflowStatusProvider

            self.register_provider(WorkflowStatusProvider())

            # 注册状态同步适配器作为订阅者
            try:
                from sqlalchemy.orm import Session

                from adapters.status_sync.services.status_subscriber import StatusSyncSubscriber
                from src.db.session import get_db_session

                session = get_db_session()
                self.register_subscriber(StatusSyncSubscriber(session))
            except ImportError:
                logger.info("状态同步适配器不可用，跳过注册")

            self._initialized = True
            logger.info("状态服务已初始化")
        except Exception as e:
            logger.error(f"初始化状态服务时出错: {e}")

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

    def register_subscriber(self, subscriber: IStatusSubscriber) -> None:
        """注册状态订阅者

        Args:
            subscriber: 状态订阅者
        """
        self._subscribers.append(subscriber)
        logger.info(f"已注册状态订阅者: {subscriber.__class__.__name__}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态

        返回所有领域的状态概览。

        Returns:
            Dict[str, Any]: 系统状态
        """
        if not self._initialized:
            self.initialize()

        status = {"domains": list(self._providers.keys()), "status": {}}

        for domain, provider in self._providers.items():
            try:
                status["status"][domain] = provider.get_status()
            except Exception as e:
                logger.error(f"获取领域 {domain} 状态时出错: {e}")
                status["status"][domain] = {"error": str(e)}

        return status

    def get_domain_status(self, domain: str, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取特定领域的状态

        Args:
            domain: 领域名称
            entity_id: 可选，实体ID

        Returns:
            Dict[str, Any]: 状态信息
        """
        if not self._initialized:
            self.initialize()

        if domain not in self._providers:
            return {"error": f"未知领域: {domain}"}

        try:
            return self._providers[domain].get_status(entity_id)
        except Exception as e:
            logger.error(f"获取领域 {domain} 状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, domain: str, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新状态

        Args:
            domain: 领域名称
            entity_id: 实体ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        if not self._initialized:
            self.initialize()

        if domain not in self._providers:
            return {"error": f"未知领域: {domain}", "updated": False}

        try:
            # 先获取当前状态
            current_status_info = self._providers[domain].get_status(entity_id)
            old_status = current_status_info.get("status")

            # 更新状态
            result = self._providers[domain].update_status(entity_id, status, **kwargs)

            # 如果更新成功，通知订阅者
            if result.get("updated", False):
                for subscriber in self._subscribers:
                    try:
                        subscriber.on_status_changed(domain, entity_id, old_status, status, result)
                    except Exception as e:
                        logger.error(f"通知订阅者状态变更时出错: {e}")

            return result
        except Exception as e:
            logger.error(f"更新领域 {domain} 状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, domain: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出领域中的实体

        Args:
            domain: 领域名称
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        if not self._initialized:
            self.initialize()

        if domain not in self._providers:
            return []

        try:
            return self._providers[domain].list_entities(status)
        except Exception as e:
            logger.error(f"列出领域 {domain} 实体时出错: {e}")
            return []

"""
状态订阅者管理器模块

管理状态订阅者的注册和通知。
"""

import logging
from typing import Any, Dict, List, Optional

from src.status.interfaces import IStatusSubscriber

logger = logging.getLogger(__name__)


class SubscriberManager:
    """状态订阅者管理器

    管理状态订阅者的注册和通知。
    """

    def __init__(self):
        """初始化订阅者管理器"""
        self._subscribers: List[IStatusSubscriber] = []

    def register_subscriber(self, subscriber: IStatusSubscriber) -> None:
        """注册状态订阅者

        Args:
            subscriber: 状态订阅者
        """
        self._subscribers.append(subscriber)
        logger.info(f"已注册状态订阅者: {subscriber.__class__.__name__}")

    def notify_status_changed(
        self, domain: str, entity_id: str, old_status: str, new_status: str, result: Dict[str, Any]
    ) -> None:
        """通知所有订阅者状态变更

        Args:
            domain: 领域名称
            entity_id: 实体ID
            old_status: 旧状态
            new_status: 新状态
            result: 操作结果
        """
        for subscriber in self._subscribers:
            try:
                subscriber.on_status_changed(domain, entity_id, old_status, new_status, result)
            except Exception as e:
                logger.error(f"通知订阅者 {subscriber.__class__.__name__} 状态变更时出错: {e}")

    def get_subscribers(self) -> List[IStatusSubscriber]:
        """获取所有订阅者

        Returns:
            订阅者列表
        """
        return self._subscribers

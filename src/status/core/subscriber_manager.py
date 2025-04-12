"""
状态订阅者管理器模块

管理状态订阅者的注册和通知。
"""

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.status.interfaces import IStatusSubscriber

logger = logging.getLogger(__name__)


class SubscriberManager:
    """状态订阅者管理器

    管理状态订阅者的注册和通知。
    """

    def __init__(self):
        """初始化订阅者管理器"""
        # 存储状态订阅者
        self._subscribers: List[IStatusSubscriber] = []
        # 存储函数式订阅者 {subscription_id: (status_type, callback)}
        self._function_subscribers: Dict[str, Tuple[str, Callable[[str, Any], None]]] = {}

    def register_subscriber(self, subscriber: IStatusSubscriber) -> None:
        """注册状态订阅者

        Args:
            subscriber: 状态订阅者
        """
        self._subscribers.append(subscriber)
        logger.info(f"已注册状态订阅者: {subscriber.__class__.__name__}")

    def subscribe(self, status_type: str, callback: Callable[[str, Any], None]) -> str:
        """订阅状态更新

        Args:
            status_type: 状态类型
            callback: 回调函数，接收status_type和status两个参数

        Returns:
            str: 订阅ID
        """
        subscription_id = str(uuid.uuid4())
        self._function_subscribers[subscription_id] = (status_type, callback)
        logger.debug(f"已订阅状态更新: {status_type}, ID: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅

        Args:
            subscription_id: 订阅ID

        Returns:
            bool: 是否成功取消
        """
        if subscription_id in self._function_subscribers:
            status_type, _ = self._function_subscribers.pop(subscription_id)
            logger.debug(f"已取消状态订阅: {status_type}, ID: {subscription_id}")
            return True
        return False

    def notify_subscribers(self, status_type: str, status: Any) -> None:
        """通知所有函数式订阅者状态更新

        Args:
            status_type: 状态类型
            status: 状态数据
        """
        # 通知函数式订阅者
        for subscription_id, (subscribed_type, callback) in list(self._function_subscribers.items()):
            if subscribed_type == status_type:
                try:
                    callback(status_type, status)
                except Exception as e:
                    logger.error(f"通知函数式订阅者时出错 (ID: {subscription_id}): {e}")

    def notify_status_changed(self, domain: str, entity_id: str, old_status: str, new_status: str, data: Dict[str, Any]) -> None:
        """通知所有订阅者状态变更

        Args:
            domain: 领域名称
            entity_id: 实体ID
            old_status: 旧状态
            new_status: 新状态
            data: 操作结果或附加数据
        """
        # 通知接口订阅者
        for subscriber in self._subscribers:
            try:
                subscriber.on_status_changed(domain, entity_id, old_status, new_status, data)
            except Exception as e:
                logger.error(f"通知订阅者 {subscriber.__class__.__name__} 状态变更时出错: {e}")

        # 通过通用机制通知函数式订阅者
        notify_data = {"domain": domain, "entity_id": entity_id, "old_status": old_status, "new_status": new_status, **data}
        self.notify_subscribers(domain, notify_data)
        # 同时通知通用状态变更频道
        self.notify_subscribers("status_changed", notify_data)

    def get_subscribers(self) -> List[IStatusSubscriber]:
        """获取所有订阅者

        Returns:
            List[IStatusSubscriber]: 订阅者列表
        """
        return self._subscribers

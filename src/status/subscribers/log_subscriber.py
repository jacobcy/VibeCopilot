"""
日志订阅者模块

提供基于日志的状态订阅者实现。
"""

import logging
from typing import Any, Dict

from src.status.interfaces import IStatusSubscriber

logger = logging.getLogger(__name__)


class LogSubscriber(IStatusSubscriber):
    """日志订阅者

    将状态变更记录到日志系统。
    可作为订阅者的基本示例实现。
    """

    def __init__(self, log_level=logging.INFO):
        """初始化日志订阅者

        Args:
            log_level: 日志级别，默认为INFO
        """
        self.log_level = log_level

    def on_status_changed(self, domain: str, entity_id: str, old_status: str, new_status: str, data: Dict[str, Any]) -> None:
        """状态变更处理

        将状态变更记录到日志中。

        Args:
            domain: 领域名称
            entity_id: 实体ID
            old_status: 旧状态
            new_status: 新状态
            data: 附加数据
        """
        logger.log(self.log_level, f"状态变更: {domain}/{entity_id}: {old_status} -> {new_status}")

        # 详细记录可能有用的数据
        if data and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"状态变更详情: {data}")

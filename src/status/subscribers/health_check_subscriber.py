"""健康检查结果订阅者模块

订阅health模块的检查结果，并更新状态管理器中的健康状态。
"""

import logging
from typing import Any, Dict

from src.status.core.health_calculator import HealthCalculator
from src.status.interfaces import IStatusSubscriber

logger = logging.getLogger(__name__)


class HealthCheckSubscriber(IStatusSubscriber):
    """健康检查结果订阅者

    订阅health模块的检查结果，并更新状态管理器中的健康状态
    """

    def __init__(self):
        """初始化健康检查订阅者"""
        self.health_calculator = HealthCalculator()

    def on_status_changed(self, domain: str, entity_id: str, old_status: str, new_status: str, data: Dict[str, Any]) -> None:
        """状态变更回调

        当health模块发布检查结果时被调用

        Args:
            domain: 领域名称（"health_check"）
            entity_id: 实体ID（检查模块名称）
            old_status: 旧状态
            new_status: 新状态（通过/警告/失败）
            data: 检查结果详情
        """
        if domain == "health_check":
            # 更新health_calculator中的组件健康状态
            components = data.get("components", {})
            for component, health_data in components.items():
                self.health_calculator.update_component_health(
                    component,
                    {
                        "health": health_data.get("health", 70),
                        "level": health_data.get("level", "good"),
                        "message": health_data.get("message", "健康检查完成"),
                    },
                )

            # 记录健康检查事件
            logger.info(f"健康检查结果已更新: {entity_id} 状态为 {new_status}")

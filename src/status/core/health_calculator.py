"""
健康度计算器模块

提供计算状态健康度的功能。
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class HealthCalculator:
    """健康度计算器

    提供计算状态健康度的功能。
    """

    def __init__(self):
        """初始化健康度计算器"""
        self._component_health = {}

    def update_component_health(self, component: str, status: Dict[str, Any]):
        """更新组件健康状态

        Args:
            component: 组件名称
            status: 状态信息，包含health_level和message
        """
        self._component_health[component] = status

    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态

        Returns:
            Dict[str, Any]: 包含整体健康状态和各组件状态的字典
        """
        # 计算整体健康度
        overall_health = self.calculate_overall_health(self._component_health)
        health_level = self.get_health_level(overall_health)

        return {
            "overall_health": overall_health,
            "health_level": health_level,
            "components": self._component_health,
            "timestamp": logging.Formatter().converter(),
        }

    @staticmethod
    def calculate_health(status_data: Dict[str, Any]) -> int:
        """计算健康度分数

        Args:
            status_data: 状态数据

        Returns:
            int: 健康度分数(0-100)
        """
        # 实现健康度计算逻辑
        # 这里是一个简单的实现，实际应根据具体状态内容进行评分
        health = 100

        # 检查是否有错误
        if "error" in status_data:
            health -= 50

        # 检查活动项是否过多
        active_count = status_data.get("active_items", 0)
        if isinstance(active_count, list):
            active_count = len(active_count)

        if active_count > 10:
            health -= 10

        # 其他健康度评判标准...

        # 确保健康度在0-100之间
        return max(0, min(100, health))

    @staticmethod
    def calculate_overall_health(domain_statuses: Dict[str, Dict[str, Any]]) -> int:
        """计算系统整体健康度

        Args:
            domain_statuses: 各领域状态的映射

        Returns:
            int: 健康度分数(0-100)
        """
        if not domain_statuses:
            return 100

        # 计算所有领域健康度的平均值
        total_health = 0
        count = 0

        for domain, status in domain_statuses.items():
            health = status.get("health", 0)
            if isinstance(health, (int, float)):
                total_health += health
                count += 1

        if count == 0:
            return 100

        return round(total_health / count)

    @staticmethod
    def get_health_level(health: int) -> str:
        """获取健康度级别

        Args:
            health: 健康度分数

        Returns:
            str: 健康度级别(critical, warning, good)
        """
        if health < 50:
            return "critical"
        elif health < 70:
            return "warning"
        else:
            return "good"

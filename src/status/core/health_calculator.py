"""
健康度计算器模块

提供计算状态健康度的功能。
与health模块集成使用，实现系统状态健康检查。
作为Status和Health模块集成的核心组件，负责处理健康检查数据并计算总体健康状态。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class HealthCalculator:
    """健康度计算器

    提供计算状态健康度的功能。
    可被StatusChecker使用，用于评估各状态提供者和系统整体的健康状态。
    作为Status和Health模块集成的核心组件，接收来自Health模块的检查结果。
    """

    def __init__(self):
        """初始化健康度计算器"""
        self._component_health = {}
        self._last_updated = datetime.now().isoformat()

    def update_component_health(self, component: str, status: Dict[str, Any]):
        """更新组件健康状态

        Args:
            component: 组件名称（通常是状态提供者的domain）
            status: 状态信息，应包含health和level字段
        """
        # 记录上一个健康状态用于日志
        old_status = None
        if component in self._component_health:
            old_status = self._component_health[component].get("level")

        self._component_health[component] = status
        self._last_updated = datetime.now().isoformat()

        # 记录状态变化
        if old_status and old_status != status.get("level"):
            logger.info(f"组件[{component}]健康状态由[{old_status}]变为[{status.get('level')}]")

    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态

        此方法被StatusChecker调用以获取整体健康状态报告。
        也用于向Health模块提供状态信息。

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
            "timestamp": self._last_updated,
            "component_count": len(self._component_health),
        }

    def get_component_health(self, component: str) -> Dict[str, Any]:
        """获取指定组件的健康状态

        Args:
            component: 组件名称

        Returns:
            Dict[str, Any]: 组件健康状态，不存在则返回默认值
        """
        if component in self._component_health:
            return self._component_health[component]
        return {"health": 0, "level": "unknown", "message": f"未找到组件{component}的健康状态"}

    def process_health_check_result(self, checker_name: str, result: Dict[str, Any]):
        """处理健康检查结果

        将Health模块的检查结果转换为内部健康状态

        Args:
            checker_name: 检查器名称
            result: 检查结果
        """
        status = result.get("status", "unknown")
        components = result.get("components", {})

        # 更新检查器自身健康状态
        health_value = 100 if status == "passed" else (70 if status == "warning" else 40)
        self.update_component_health(
            checker_name, {"health": health_value, "level": status, "message": f"{checker_name}检查{status}", "timestamp": datetime.now().isoformat()}
        )

        # 更新检查结果中的各组件状态
        for comp_name, comp_data in components.items():
            if isinstance(comp_data, dict):
                self.update_component_health(
                    f"{checker_name}.{comp_name}",
                    {
                        "health": comp_data.get("health", health_value),
                        "level": comp_data.get("level", status),
                        "message": comp_data.get("message", f"{comp_name}状态为{status}"),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

    @staticmethod
    def calculate_health(status_data: Dict[str, Any]) -> int:
        """计算健康度分数

        基于状态数据计算健康度分数。
        StatusChecker使用此方法评估单个提供者的健康状态。
        增强了健康度计算，适配来自Health模块的数据格式。

        Args:
            status_data: 状态数据，通常来自状态提供者的get_status()方法

        Returns:
            int: 健康度分数(0-100)
        """
        # 状态数据中已有健康度则直接使用
        if "health" in status_data and isinstance(status_data["health"], (int, float)):
            return max(0, min(100, int(status_data["health"])))

        # 基于状态字符串推断健康度
        if "status" in status_data:
            status = status_data["status"]
            if status in ["passed", "ok", "good"]:
                return 100
            elif status == "warning":
                return 70
            elif status in ["failed", "error", "critical"]:
                return 40

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

        # 检查是否有警告
        warning_count = len(status_data.get("warnings", []))
        health -= warning_count * 5

        # 检查已完成项目比例
        total_items = status_data.get("total_items", 0)
        completed_items = status_data.get("completed_items", 0)

        if total_items > 0:
            completion_ratio = completed_items / total_items
            if completion_ratio < 0.3:
                health -= 10
            elif completion_ratio < 0.7:
                health -= 5

        # 确保健康度在0-100之间
        return max(0, min(100, health))

    @staticmethod
    def calculate_overall_health(domain_statuses: Dict[str, Dict[str, Any]]) -> int:
        """计算系统整体健康度

        基于所有领域状态计算系统整体健康度。
        被StatusChecker用于计算最终的系统健康状态。
        优化了计算逻辑，处理特殊的组件加权情况。

        Args:
            domain_statuses: 各领域状态的映射，键为domain，值为状态字典

        Returns:
            int: 健康度分数(0-100)
        """
        if not domain_statuses:
            return 100

        # 计算所有领域健康度的加权平均值
        total_health = 0
        weights = 0
        critical_count = 0

        # 关键组件列表及其权重
        critical_components = {"task": 2.0, "workflow": 2.0, "database": 3.0, "api": 1.5}

        for domain, status in domain_statuses.items():
            health = status.get("health", 0)
            if not isinstance(health, (int, float)):
                continue

            # 应用权重
            weight = 1.0
            if domain in critical_components:
                weight = critical_components[domain]

                # 关键组件健康度过低记录
                if health < 50:
                    critical_count += 1

            total_health += health * weight
            weights += weight

        if weights == 0:
            return 100

        # 如果有多个关键组件健康度过低，额外降低整体健康度
        health_score = round(total_health / weights)
        if critical_count >= 2:
            health_score = max(0, health_score - 20)

        return health_score

    @staticmethod
    def get_health_level(health: int) -> str:
        """获取健康度级别

        将数值健康度转换为文本级别。
        StatusChecker使用此方法确定检查结果的状态。

        Args:
            health: 健康度分数(0-100)

        Returns:
            str: 健康度级别(critical, warning, good)
        """
        if health < 50:
            return "critical"
        elif health < 70:
            return "warning"
        else:
            return "good"

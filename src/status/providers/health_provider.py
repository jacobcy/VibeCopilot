"""健康状态提供者模块

提供来自Health检查的结果
"""

import logging
from typing import Any, Dict, List, Optional

from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class HealthProvider(IStatusProvider):
    """健康状态提供者

    提供来自health模块的健康检查状态
    """

    def __init__(self):
        """初始化健康状态提供者"""
        # 存储最近的健康检查结果
        self._results: Dict[str, Dict[str, Any]] = {}
        self._last_updated = ""
        self._overall_status = "unknown"

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "health"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取健康状态

        Args:
            entity_id: 可选，检查器名称。不提供则获取整体健康状态。

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            if entity_id:
                # 返回特定检查器的状态
                if entity_id in self._results:
                    return {
                        "domain": self.domain,
                        "entity_id": entity_id,
                        "status": self._results[entity_id].get("status", "unknown"),
                        "last_check": self._results[entity_id].get("timestamp", ""),
                        "details": self._results[entity_id].get("details", []),
                        "suggestions": self._results[entity_id].get("suggestions", []),
                    }
                else:
                    return {
                        "domain": self.domain,
                        "entity_id": entity_id,
                        "status": "unknown",
                        "error": "未找到该检查器的结果",
                    }
            else:
                # 返回聚合的健康状态
                return {
                    "domain": self.domain,
                    "overall_status": self._overall_status,
                    "checkers": list(self._results.keys()),
                    "last_updated": self._last_updated,
                    "summary": self._get_summary(),
                }
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {"domain": self.domain, "status": "error", "error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新健康状态

        Args:
            entity_id: 检查器名称
            status: 新状态
            **kwargs: 附加参数，包括检查结果详情

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 更新检查器结果
            data = kwargs.get("data", {})

            self._results[entity_id] = {
                "status": status,
                "timestamp": kwargs.get("timestamp", ""),
                "details": data.get("details", []),
                "suggestions": data.get("suggestions", []),
                "components": data.get("components", {}),
            }

            # 更新最后更新时间
            self._last_updated = kwargs.get("timestamp", "")

            # 更新整体状态
            statuses = [r.get("status", "unknown") for r in self._results.values()]
            if "failed" in statuses:
                self._overall_status = "failed"
            elif "warning" in statuses:
                self._overall_status = "warning"
            elif "passed" in statuses:
                self._overall_status = "passed"
            else:
                self._overall_status = "unknown"

            return {
                "updated": True,
                "entity_id": entity_id,
                "status": status,
            }
        except Exception as e:
            logger.error(f"更新健康状态失败: {e}")
            return {"updated": False, "error": str(e)}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出健康检查器

        Args:
            status: 可选，筛选特定状态的检查器

        Returns:
            List[Dict[str, Any]]: 检查器列表
        """
        try:
            result = []
            for entity_id, data in self._results.items():
                if status is None or data.get("status") == status:
                    result.append(
                        {
                            "id": entity_id,
                            "status": data.get("status", "unknown"),
                            "last_check": data.get("timestamp", ""),
                        }
                    )
            return result
        except Exception as e:
            logger.error(f"列出健康检查器失败: {e}")
            return []

    def _get_summary(self) -> Dict[str, Any]:
        """获取健康检查结果摘要

        Returns:
            Dict[str, Any]: 结果摘要
        """
        statuses = [r.get("status", "unknown") for r in self._results.values()]
        return {
            "total": len(self._results),
            "passed": statuses.count("passed"),
            "warning": statuses.count("warning"),
            "failed": statuses.count("failed"),
            "unknown": statuses.count("unknown"),
        }

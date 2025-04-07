"""
状态服务模块

提供获取和管理系统状态的功能，包括订阅者管理、状态提供者管理和健康状态计算。
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.providers.task_provider import get_task_status_summary

logger = logging.getLogger(__name__)

# --- Add Singleton Pattern --- (Recommended for service classes)
_instance = None


class StatusService:
    """状态服务，负责系统状态管理和分发"""

    @classmethod
    def get_instance(cls):
        """获取 StatusService 的单例实例"""
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    # -----------------------------

    def __init__(self):
        """初始化状态服务 (设为私有防止直接实例化)"""
        if _instance is not None:
            raise Exception("This class is a singleton! Use get_instance()")
        else:
            _instance = self  # Assign instance here

        logger.info("Initializing Status Service...")
        self.provider_manager = ProviderManager()
        self.subscriber_manager = SubscriberManager()
        self.health_calculator = HealthCalculator()
        self.project_state = ProjectState()
        self._register_default_providers()
        logger.info("Status Service Initialized.")

    def _register_default_providers(self):
        """注册默认的状态提供者

        包括系统健康状态和项目状态
        """
        # 注册健康状态提供者
        self.register_provider("health", self.health_calculator.get_health_status)

        # 注册项目状态提供者
        self.register_provider("project_state", self.project_state.get_project_state)

        # --- Register Task Provider ---
        self.register_provider("task", get_task_status_summary)
        # -----------------------------

    def register_provider(self, status_type: str, provider_func: Callable[[], Any]):
        """注册状态提供者

        Args:
            status_type: 状态类型
            provider_func: 提供者函数，返回状态数据
        """
        self.provider_manager.register_provider(status_type, provider_func)
        logger.info(f"状态提供者注册成功: {status_type}")

    def unregister_provider(self, status_type: str) -> bool:
        """注销状态提供者

        Args:
            status_type: 状态类型

        Returns:
            是否成功注销
        """
        return self.provider_manager.unregister_provider(status_type)

    def get_status(self, status_type: Optional[str] = None) -> Dict[str, Any]:
        """获取指定类型或所有状态

        Args:
            status_type: 状态类型，如果为None则获取所有状态

        Returns:
            状态数据字典
        """
        try:
            if status_type:
                # 获取指定类型状态
                return {status_type: self.provider_manager.get_status(status_type)}
            else:
                # 获取所有状态
                return self.provider_manager.get_all_status()
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {"error": str(e)}

    def subscribe(self, status_type: str, callback: Callable[[str, Any], None]) -> str:
        """订阅状态更新

        Args:
            status_type: 状态类型
            callback: 回调函数，接收status_type和status两个参数

        Returns:
            订阅ID
        """
        return self.subscriber_manager.subscribe(status_type, callback)

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅

        Args:
            subscription_id: 订阅ID

        Returns:
            是否成功取消
        """
        return self.subscriber_manager.unsubscribe(subscription_id)

    def notify_subscribers(self, status_type: str, status: Any):
        """通知订阅者状态更新

        Args:
            status_type: 状态类型
            status: 状态数据
        """
        self.subscriber_manager.notify_subscribers(status_type, status)

    def update_health(self, component: str, status: Dict[str, Any]):
        """更新组件健康状态

        Args:
            component: 组件名称
            status: 状态信息，包含health_level和message
        """
        self.health_calculator.update_component_health(component, status)

        # 获取更新后的健康状态
        health_status = self.health_calculator.get_health_status()

        # 通知订阅者
        self.notify_subscribers("health", health_status)

    def get_health(self) -> Dict[str, Any]:
        """获取系统健康状态

        Returns:
            健康状态数据
        """
        return self.health_calculator.get_health_status()

    def update_project_state(self, state_key: str, state_value: Any):
        """更新项目状态

        Args:
            state_key: 状态键
            state_value: 状态值
        """
        self.project_state.update_state(state_key, state_value)

        # 获取更新后的项目状态
        project_state = self.project_state.get_project_state()

        # 通知订阅者
        self.notify_subscribers("project_state", project_state)

    def get_project_state(self) -> Dict[str, Any]:
        """获取项目状态

        Returns:
            项目状态数据
        """
        return self.project_state.get_project_state()

    # --- Added get_domain_status ---
    def get_domain_status(self, domain: str) -> Dict[str, Any]:
        """获取指定领域的状态信息"""
        logger.debug(f"获取领域状态: {domain}")
        try:
            # Assuming the provider returns the necessary structure
            status_data = self.provider_manager.get_status(domain)
            if status_data is None:  # Provider might not be registered or failed internally
                return {"error": f"未找到或无法获取领域 '{domain}' 的状态。"}
            # Add domain key for clarity in the command layer?
            # status_data["domain"] = domain # Maybe not needed if command knows domain
            return status_data
        except Exception as e:
            logger.error(f"获取领域 '{domain}' 状态时出错: {e}", exc_info=True)
            return {"error": f"获取领域 '{domain}' 状态失败: {e}"}

    # ---------------------------

    # --- Added get_system_status ---
    def get_system_status(self, detailed: bool = False) -> Dict[str, Any]:
        """获取整体系统状态 (聚合所有 Provider)"""
        logger.debug(f"获取系统状态 (detailed={detailed})...")
        system_status = {}
        try:
            all_statuses = self.provider_manager.get_all_status()

            # Basic structure - can be enhanced
            # project_state might be None if provider failed
            project_state = all_statuses.get("project_state", {})
            if isinstance(project_state, dict):
                system_status["project_phase"] = project_state.get("current_phase", "未知")
                system_status["project_name"] = project_state.get("name", "未命名项目")
                system_status["project_version"] = project_state.get("version", "N/A")
            else:
                system_status["project_phase"] = "错误"
                system_status["project_name"] = "错误"
                system_status["project_version"] = "错误"

            # Placeholder for active workflow - needs a proper provider
            system_status["active_workflow"] = all_statuses.get("active_workflow_summary", {}).get("name", "无")

            # Include task summary directly (already fetched by get_all_status)
            system_status["task_summary"] = all_statuses.get("task", {"error": "Task provider 未运行或出错"})

            # Include health status
            system_status["health"] = all_statuses.get("health", {"error": "Health provider 未运行或出错"})

            if detailed:
                # Include all fetched statuses if detailed=True
                system_status["all_domain_details"] = all_statuses

            return system_status
        except Exception as e:
            logger.error(f"获取系统状态时出错: {e}", exc_info=True)
            return {"error": f"获取系统状态失败: {e}"}

    # -----------------------------

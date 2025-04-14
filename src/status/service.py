"""
状态服务模块

提供获取和管理系统状态的功能，包括订阅者管理、状态提供者管理和健康状态计算。
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union

from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.interfaces import IStatusProvider, IStatusSubscriber
from src.status.service_initialization import initialize_components, register_default_providers, register_default_subscribers
from src.status.status_operations import get_domain_status, get_system_status, initialize_project_status, update_project_phase, update_status

logger = logging.getLogger(__name__)


class StatusService:
    """状态服务，负责系统状态管理和分发"""

    _instance = None

    @classmethod
    def get_instance(cls):
        """获取 StatusService 的单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """初始化状态服务 (设为私有防止直接实例化)"""
        if StatusService._instance is not None:
            raise Exception("This class is a singleton! Use get_instance()")

        logger.info("初始化状态服务...")

        # 初始化核心组件
        components = initialize_components()
        self.provider_manager = components[0]
        self.subscriber_manager = components[1]
        self.health_calculator = components[2]
        self.project_state = components[3]

        # 注册默认提供者和订阅者
        register_default_providers(self.provider_manager, self.health_calculator, self.project_state)
        register_default_subscribers(self.subscriber_manager)

        logger.info("状态服务初始化完成。")

    def register_provider(self, domain: str, provider: Union[IStatusProvider, Callable[[], Any]]):
        """注册状态提供者

        Args:
            domain: 状态类型
            provider: 提供者函数或对象，返回状态数据
        """
        self.provider_manager.register_provider(domain, provider)
        logger.info(f"状态提供者注册成功: {domain}")

    def unregister_provider(self, domain: str) -> bool:
        """注销状态提供者

        Args:
            domain: 状态类型

        Returns:
            是否成功注销
        """
        return self.provider_manager.unregister_provider(domain)

    def register_subscriber(self, subscriber: IStatusSubscriber) -> None:
        """注册状态订阅者

        Args:
            subscriber: 状态订阅者实例
        """
        self.subscriber_manager.register_subscriber(subscriber)

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

    def update_status(self, domain: str, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新实体状态

        统一更新各领域实体状态的入口，并通知订阅者

        Args:
            domain: 领域名称
            entity_id: 实体ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        return update_status(self.provider_manager, self.subscriber_manager, domain, entity_id, status, **kwargs)

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

    def get_domain_status(self, domain: str, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取指定领域的状态信息

        Args:
            domain: 领域名称
            entity_id: 可选的实体ID

        Returns:
            Dict[str, Any]: 状态信息
        """
        return get_domain_status(self.provider_manager, domain, entity_id)

    def get_system_status(self, detailed: bool = False) -> Dict[str, Any]:
        """获取整体系统状态 (聚合所有 Provider)

        Args:
            detailed: 是否包含详细信息

        Returns:
            Dict[str, Any]: 系统状态
        """
        return get_system_status(self.provider_manager, detailed)

    def list_providers(self) -> List[str]:
        """列出所有已注册的提供者

        Returns:
            List[str]: 提供者域名列表
        """
        return self.provider_manager.get_domains()

    def update_project_phase(self, phase: str) -> Dict[str, Any]:
        """更新项目阶段

        Args:
            phase: 新的项目阶段

        Returns:
            Dict[str, Any]: 操作结果
        """
        return update_project_phase(self.project_state, self.subscriber_manager, phase)

    def initialize_project_status(self, project_name: str = None) -> Dict[str, Any]:
        """初始化项目状态

        Args:
            project_name: 项目名称，如果为None则使用默认名称

        Returns:
            Dict[str, Any]: 操作结果
        """
        return initialize_project_status(self.project_state, self.subscriber_manager, project_name)

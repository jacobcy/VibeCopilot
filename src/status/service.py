"""
状态服务模块

提供获取和管理系统状态的功能，包括订阅者管理、状态提供者管理和健康状态计算。
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from src.core.config import get_config
from src.core.config.settings import SettingsConfig
from src.roadmap.service.service_connector import force_connect, set_status_service
from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.interfaces import IStatusProvider, IStatusSubscriber
from src.status.models import StatusSource
from src.status.service_initialization import initialize_components, register_default_providers, register_default_subscribers
from src.status.status_operations import get_domain_status, get_system_status, update_project_phase, update_status

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
            # Allow re-initialization for scripts like fix_project_state.py, but log it.
            logger.warning(
                "StatusService is a singleton but is being re-initialized. This should only happen in controlled scenarios (e.g., tests, fix scripts)."
            )
            # raise Exception("This class is a singleton! Use get_instance()") # Soften for fixing script

        logger.info("初始化状态服务 (StatusService __init__)...")

        components = initialize_components()
        self.provider_manager = components[0]
        self.subscriber_manager = components[1]
        self.health_calculator = components[2]
        self.project_state = components[3]

        # 使用 SettingsConfig 管理配置
        self.settings_manager = SettingsConfig()

        # 然后将 settings_manager (SettingsConfig instance) 设置到 project_state
        # ProjectState 需要能够处理 SettingsConfig 实例，或需要调整
        self.project_state.settings_config = self.settings_manager

        # 现在注册默认提供者
        register_default_providers(self.provider_manager, self.health_calculator, self.project_state)
        register_default_subscribers(self.subscriber_manager)

        set_status_service(self)  # Register self with the connector
        logger.info("StatusService已注册到服务连接器")

        # Explicitly try to connect services now that StatusService is fully set up
        try:
            logger.info("StatusService __init__: 尝试强制连接所有服务...")
            if force_connect():
                logger.info("StatusService __init__: 服务连接成功 (via force_connect)。")
            else:
                logger.warning("StatusService __init__: force_connect() 未能完全连接服务。RoadmapService可能尚未实例化。")
        except ImportError:
            logger.error("StatusService __init__: 无法导入 service_connector.force_connect。")
        except Exception as e:
            logger.error(f"StatusService __init__: 调用 force_connect 时出错: {e}", exc_info=True)

        self.providers = []

        StatusService._instance = self  # Set instance at the very end
        logger.info("状态服务初始化完成 (StatusService __init__ done)。")

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

    def initialize_project_status(self, project_name: str, github_project_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """初始化项目状态

        Args:
            project_name: 项目名称
            github_project_info: GitHub项目信息，包含project_id, project_title, project_number

        Returns:
            Dict: 初始化结果
        """
        try:
            # 调用ProjectState的initialize_project方法
            result = self.project_state.initialize_project(project_name, github_project_info)

            # 通知订阅者项目状态变更
            updated_state = self.project_state.get_project_state()
            self.subscriber_manager.notify_status_changed(
                domain="project_state",
                entity_id=None,
                old_status="unknown",
                new_status=updated_state.get("current_phase", "planning"),
                data=updated_state,
            )

            # 返回成功结果
            if github_project_info:
                logger.info(
                    f"项目状态已初始化: {project_name}，关联GitHub项目: {github_project_info.get('project_title')} (#{github_project_info.get('project_number')})"
                )
            else:
                logger.info(f"项目状态已初始化: {project_name}")

            return {
                "status": "success",
                "message": f"项目 {project_name} 已初始化",
                "project_name": project_name,
                "current_phase": updated_state.get("current_phase", "planning"),
                "github_project_linked": bool(github_project_info),
            }
        except Exception as e:
            logger.error(f"初始化项目状态时出错: {e}")
            return {"status": "error", "error": f"初始化项目状态失败: {str(e)}"}

    def connect_roadmap_service(self):
        """连接RoadmapService与RoadmapStatusProvider

        尝试建立RoadmapService和RoadmapStatusProvider之间的连接
        """
        try:
            # 尝试从连接器获取RoadmapService
            from src.roadmap.service.service_connector import connect_services, get_roadmap_service

            # 触发连接
            connect_services()

            # 检查是否连接成功
            roadmap_provider = self.provider_manager.get_provider("roadmap")
            if roadmap_provider and hasattr(roadmap_provider, "roadmap_service") and roadmap_provider.roadmap_service:
                logger.info("RoadmapService和RoadmapStatusProvider已成功连接")
                return True
            else:
                logger.warning("RoadmapService和RoadmapStatusProvider未成功连接")
                return False
        except ImportError:
            logger.warning("无法导入service_connector模块，无法连接RoadmapService")
            return False
        except Exception as e:
            logger.error(f"连接RoadmapService时出错: {e}")
            return False

    def update_settings(self, path: str, value: Any) -> bool:
        """更新settings.json中的特定配置

        Args:
            path: 配置路径，使用点符号，如 'github.owner'
            value: 配置值

        Returns:
            bool: 是否更新成功
        """
        if self.settings_manager.set(path, value):
            return self.settings_manager.save()
        return False

    def get_settings_value(self, path: str, default: Any = None) -> Any:
        """获取settings.json中的配置值

        Args:
            path: 配置路径，使用点符号，如 'github.owner'
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        return self.settings_manager.get(path, default)

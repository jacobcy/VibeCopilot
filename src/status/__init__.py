"""
状态服务包

提供系统状态管理和监控功能
"""

import logging

logger = logging.getLogger(__name__)

from src.status.init_service import InitService

# 导入服务模块
from src.status.service import StatusService
from src.status.service_initialization import initialize_components, register_default_providers, register_default_subscribers
from src.status.status_operations import get_domain_status, get_system_status, update_project_phase, update_status

# 全局状态服务实例
status_service = None


def initialize():
    """初始化状态模块

    注册默认的提供者和订阅者
    """
    global status_service

    # 延迟初始化状态服务实例
    if status_service is None:
        status_service = StatusService.get_instance()

    from src.status.subscribers.health_check_subscriber import HealthCheckSubscriber

    # 获取状态服务单例
    service = StatusService.get_instance()

    # 注册健康检查订阅者
    try:
        service.register_subscriber(HealthCheckSubscriber())
        logger.info("健康检查订阅者注册成功")
    except Exception as e:
        logger.error(f"注册健康检查订阅者失败: {e}")

    # 检查是否已经注册了健康状态提供者
    if not service.provider_manager.has_provider("health"):
        try:
            from src.status.providers.health_provider import HealthProvider

            health_provider = HealthProvider()
            service.register_provider("health", health_provider)
            logger.info("健康状态提供者注册成功")
        except Exception as e:
            logger.error(f"注册健康状态提供者失败: {e}")

    logger.info("状态模块初始化完成。")


__all__ = [
    "StatusService",
    "InitService",
    "initialize_components",
    "register_default_providers",
    "register_default_subscribers",
    "get_domain_status",
    "get_system_status",
    "update_project_phase",
    "update_status",
]

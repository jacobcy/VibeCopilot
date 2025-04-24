"""
状态服务初始化模块

处理StatusService的初始化逻辑，包括默认提供者和订阅者注册
"""

import logging
from typing import Optional

from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.interfaces import IStatusProvider
from src.status.providers.task_provider import TaskStatusProvider
from src.status.providers.workflow_provider import WorkflowStatusProvider
from src.status.subscribers.log_subscriber import LogSubscriber

logger = logging.getLogger(__name__)


# 定义模拟类，避免导入错误
class MockRoadmapStatusProvider(IStatusProvider):
    """路线图状态提供者模拟实现"""

    def __init__(self, roadmap_service=None):
        """初始化模拟路线图状态提供者"""
        self._domain = "roadmap"

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return self._domain

    def get_status(self, entity_id=None):
        """获取模拟状态数据"""
        return {"status": "warning", "message": "使用模拟路线图数据，真实路线图服务未正确初始化", "health": 50, "domain": self._domain, "mock": True}

    def update_status(self, entity_id, status, **kwargs):
        """模拟更新状态"""
        return {"updated": False, "error": "模拟路线图提供者不支持更新操作", "mock": True}

    def list_entities(self, status=None):
        """返回模拟实体列表"""
        return [{"id": "mock:roadmap", "name": "模拟路线图数据", "type": "mock", "status": "warning"}]


def initialize_components():
    """初始化状态服务的核心组件

    Returns:
        tuple: 包含(provider_manager, subscriber_manager, health_calculator, project_state)的元组
    """
    logger.info("初始化状态服务核心组件...")
    provider_manager = ProviderManager()
    subscriber_manager = SubscriberManager()
    health_calculator = HealthCalculator()
    project_state = ProjectState()

    return provider_manager, subscriber_manager, health_calculator, project_state


def register_default_providers(provider_manager, health_calculator, project_state):
    """注册默认的状态提供者

    包括系统健康状态和项目状态

    Args:
        provider_manager: 提供者管理器实例
        health_calculator: 健康计算器实例
        project_state: 项目状态实例
    """
    # 尝试获取数据库会话，但不强制依赖
    session = None
    try:
        from src.db import get_session_factory

        # 直接使用已初始化的会话，减少数据库操作
        session_factory = get_session_factory()
        if session_factory is not None:
            session = session_factory()
    except Exception as e:
        logger.warning(f"获取数据库会话失败: {e}")
        # 将错误降级为警告，不影响状态模块初始化

    # 注册健康状态提供者
    provider_manager.register_provider("health", health_calculator.get_health_status)
    logger.info("健康状态提供者注册成功")

    # 注册项目状态提供者
    provider_manager.register_provider("project_state", project_state.get_project_state)
    logger.info("项目状态提供者注册成功")

    # 注册任务状态提供者
    try:
        task_provider = TaskStatusProvider()
        provider_manager.register_provider("task", task_provider)
        logger.info("任务状态提供者注册成功")
    except Exception as e:
        logger.error(f"注册任务状态提供者失败: {e}")
        provider_manager.register_provider(
            "task",
            lambda: {
                "status": "error",
                "error": f"任务状态提供者初始化失败: {e}",
                "code": "PROVIDER_INIT_ERROR",
            },
        )

    # 注册路线图状态提供者
    register_roadmap_provider(provider_manager)

    # 注册工作流状态提供者
    register_workflow_provider(provider_manager, session)


def register_roadmap_provider(provider_manager):
    """注册路线图状态提供者

    Args:
        provider_manager: 提供者管理器实例
    """
    try:
        # 使用模拟提供者替代临时禁用的真实提供者
        logger.info("路线图状态提供者已临时禁用，使用模拟提供者")
        roadmap_provider = MockRoadmapStatusProvider()
        provider_manager.register_provider("roadmap", roadmap_provider)
        logger.info("模拟路线图状态提供者注册成功")
    except ImportError as e:
        logger.error(f"注册路线图状态提供者失败 (导入错误): {e}")
        provider_manager.register_provider(
            "roadmap",
            lambda: {
                "status": "error",
                "error": f"路线图状态提供者导入失败: {e}",
                "code": "IMPORT_ERROR",
                "health": 0,
                "suggestions": ["检查导入路径是否正确", "确保所有必要的模块已安装", "检查代码中是否存在导入冲突"],
            },
        )
    except Exception as e:
        logger.error(f"注册路线图状态提供者失败: {e}")
        # 使用模拟数据作为临时解决方案
        provider_manager.register_provider(
            "roadmap",
            lambda: {
                "status": "error",
                "error": f"路线图状态提供者初始化失败: {e}",
                "code": "PROVIDER_INIT_ERROR",
                "health": 0,
                "suggestions": ["检查数据库连接", "确保所有必要的表都已创建", "验证 RoadmapService 配置"],
            },
        )


def register_workflow_provider(provider_manager, session=None):
    """注册工作流状态提供者

    Args:
        provider_manager: 提供者管理器实例
        session: 可选的数据库会话
    """
    try:
        # 使用已初始化的session，避免重复初始化数据库
        if session:
            workflow_provider = WorkflowStatusProvider()
            # 注入现有session到provider
            workflow_provider._db_session = session
            provider_manager.register_provider("workflow", workflow_provider)
            logger.info("工作流状态提供者注册成功")
        else:
            raise Exception("数据库会话不可用")
    except Exception as e:
        logger.error(f"注册工作流状态提供者失败: {e}")


def register_default_subscribers(subscriber_manager):
    """注册默认的状态订阅者

    添加基本的日志订阅者，用于记录状态变更

    Args:
        subscriber_manager: 订阅者管理器实例
    """
    try:
        # 注册日志订阅者
        log_subscriber = LogSubscriber()
        subscriber_manager.register_subscriber(log_subscriber)
        logger.info("日志状态订阅者注册成功")
    except Exception as e:
        logger.error(f"注册日志状态订阅者失败: {e}")

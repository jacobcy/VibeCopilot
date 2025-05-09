"""
状态服务初始化模块

处理StatusService的初始化逻辑，包括默认提供者和订阅者注册
"""

import logging
from typing import Optional, Tuple

from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.interfaces import IStatusProvider, IStatusSubscriber
from src.status.providers.flow_session_provider import FlowSessionStatusProvider
from src.status.providers.github_info_provider import GitHubInfoProvider
from src.status.providers.health_provider import HealthProvider
from src.status.providers.roadmap_provider import RoadmapStatusProvider
from src.status.providers.task_provider import TaskStatusProvider
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


def initialize_components() -> Tuple[ProviderManager, SubscriberManager, HealthCalculator, ProjectState]:
    """初始化状态模块的核心组件"""
    provider_manager = ProviderManager()
    subscriber_manager = SubscriberManager()
    health_calculator = HealthCalculator()

    # 使用新的构造方法初始化 ProjectState，不再传入文件路径
    project_state = ProjectState()

    logger.info("状态模块核心组件初始化完成。")
    return provider_manager, subscriber_manager, health_calculator, project_state


def register_default_providers(provider_manager: ProviderManager, health_calculator: HealthCalculator, project_state: ProjectState) -> None:
    """注册默认状态提供者"""
    logger.info("注册默认状态提供者 (in service_initialization)...")

    try:
        # 添加日志以帮助调试
        logger.info("开始注册默认提供者...")
        provider_manager.register_provider("health", HealthProvider())
        logger.info("健康状态提供者注册成功")

        # 添加调试日志
        logger.info("正在注册 GitHub 信息提供者...")
        github_provider = GitHubInfoProvider()
        provider_manager.register_provider("github_info", github_provider)
        logger.info("GitHub 信息提供者注册成功")

        # RoadmapStatusProvider is instantiated here, it needs RoadmapService later.
        roadmap_provider = RoadmapStatusProvider(project_state)  # Still pass project_state
        provider_manager.register_provider("roadmap", roadmap_provider)

        try:
            task_provider = TaskStatusProvider(project_state)
            provider_manager.register_provider("task", task_provider)
        except Exception as e:
            logger.error(f"注册TaskStatusProvider时出错: {e}")

        if not provider_manager.has_provider("project_state"):
            provider_manager.register_provider("project_state", project_state.get_project_state)

        # Removed explicit connect_services() or get_roadmap_service() calls here.
        # The connection will be attempted by StatusService.__init__ using force_connect,
        # or when RoadmapStatusProvider._ensure_service_set is called.
        logger.info("默认提供者已注册。服务连接将由 StatusService.__init__ 或按需处理。")

    except Exception as e:
        logger.error(f"注册默认提供者时出错: {e}", exc_info=True)
        # 添加更详细的错误处理
        import traceback

        logger.error(f"完整错误堆栈: {traceback.format_exc()}")


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

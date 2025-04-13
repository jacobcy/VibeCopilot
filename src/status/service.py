"""
状态服务模块

提供获取和管理系统状态的功能，包括订阅者管理、状态提供者管理和健康状态计算。
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.roadmap.service import RoadmapService
from src.status.core.health_calculator import HealthCalculator
from src.status.core.project_state import ProjectState
from src.status.core.provider_manager import ProviderManager
from src.status.core.subscriber_manager import SubscriberManager
from src.status.interfaces import IStatusProvider, IStatusSubscriber
from src.status.providers.roadmap_provider import RoadmapStatusProvider
from src.status.providers.task_provider import get_task_status_summary
from src.status.providers.workflow_provider import WorkflowStatusProvider
from src.status.subscribers.log_subscriber import LogSubscriber

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
        self.provider_manager = ProviderManager()
        self.subscriber_manager = SubscriberManager()
        self.health_calculator = HealthCalculator()
        self.project_state = ProjectState()
        self._register_default_providers()
        self._register_default_subscribers()
        logger.info("状态服务初始化完成。")

    def _register_default_providers(self):
        """注册默认的状态提供者

        包括系统健康状态和项目状态
        """
        # 预先初始化数据库，避免每个provider重复初始化
        try:
            from src.db import get_session_factory, init_db

            # 直接使用已初始化的会话，减少数据库操作
            # 不调用init_db()，因为这在主程序启动时已经完成
            session = get_session_factory()()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")
            session = None

        # 注册健康状态提供者
        self.register_provider("health", self.health_calculator.get_health_status)

        # 注册项目状态提供者
        self.register_provider("project_state", self.project_state.get_project_state)

        # 注册任务状态提供者
        self.register_provider("task", get_task_status_summary)

        # 注册路线图状态提供者
        try:
            if session:
                roadmap_service = RoadmapService(session=session)
                roadmap_provider = RoadmapStatusProvider(roadmap_service)
                self.register_provider("roadmap", roadmap_provider)
                logger.info("路线图状态提供者注册成功")
            else:
                raise Exception("数据库会话不可用")
        except ImportError as e:
            logger.error(f"注册路线图状态提供者失败 (导入错误): {e}")
            self.register_provider(
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
            self.register_provider(
                "roadmap",
                lambda: {
                    "status": "error",
                    "error": f"路线图状态提供者初始化失败: {e}",
                    "code": "PROVIDER_INIT_ERROR",
                    "health": 0,
                    "suggestions": ["检查数据库连接", "确保所有必要的表都已创建", "验证 RoadmapService 配置"],
                },
            )

        # 注册工作流状态提供者
        try:
            # 使用已初始化的session，避免重复初始化数据库
            if session:
                workflow_provider = WorkflowStatusProvider()
                # 注入现有session到provider
                workflow_provider._db_session = session
                self.register_provider("workflow", workflow_provider)
                logger.info("工作流状态提供者注册成功")
            else:
                raise Exception("数据库会话不可用")
        except Exception as e:
            logger.error(f"注册工作流状态提供者失败: {e}")

    def _register_default_subscribers(self):
        """注册默认的状态订阅者

        添加基本的日志订阅者，用于记录状态变更
        """
        try:
            # 注册日志订阅者
            log_subscriber = LogSubscriber()
            self.register_subscriber(log_subscriber)
            logger.info("日志状态订阅者注册成功")
        except Exception as e:
            logger.error(f"注册日志状态订阅者失败: {e}")

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
        logger.debug(f"更新状态: {domain}/{entity_id} -> {status}")
        try:
            provider = self.provider_manager.get_provider(domain)
            if not provider:
                return {"error": f"未找到领域 '{domain}' 的状态提供者", "updated": False}

            # 获取当前状态，用于记录变更
            try:
                current_status = provider.get_status(entity_id)
                old_status = current_status.get("status", "unknown")
            except Exception:
                old_status = "unknown"

            # 调用提供者更新状态
            result = provider.update_status(entity_id, status, **kwargs)

            # 如果更新成功，通知订阅者
            if result.get("updated", False):
                self.subscriber_manager.notify_status_changed(domain, entity_id, old_status, status, result)

            return result

        except Exception as e:
            logger.error(f"更新状态时出错: {e}", exc_info=True)
            return {"error": str(e), "updated": False}

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
        logger.debug(f"获取领域状态: {domain}, 实体ID: {entity_id}")
        try:
            provider = self.provider_manager.get_provider(domain)
            if provider is None:
                return {"error": f"未找到领域 '{domain}' 的状态提供者", "code": "PROVIDER_NOT_FOUND", "suggestions": ["检查提供者是否正确注册", "确认领域名称是否正确"]}

            # 调用提供者的 get_status 方法
            status_data = provider.get_status(entity_id) if entity_id else provider.get_status()

            if status_data is None:
                return {"error": f"无法获取领域 '{domain}' 的状态", "code": "STATUS_FETCH_FAILED", "suggestions": ["检查数据库连接", "验证实体ID是否存在"]}

            return status_data

        except Exception as e:
            logger.error(f"获取领域 '{domain}' 状态时出错: {e}", exc_info=True)
            return {"error": f"获取领域 '{domain}' 状态失败: {str(e)}", "code": "STATUS_ERROR", "suggestions": ["检查日志获取详细错误信息", "确认系统配置是否正确"]}

    def get_system_status(self, detailed: bool = False) -> Dict[str, Any]:
        """获取整体系统状态 (聚合所有 Provider)

        Args:
            detailed: 是否包含详细信息

        Returns:
            Dict[str, Any]: 系统状态
        """
        logger.debug(f"获取系统状态 (detailed={detailed})...")
        system_status = {}
        try:
            all_statuses = self.provider_manager.get_all_status()

            # 项目基本信息
            project_state = all_statuses.get("project_state", {})
            if isinstance(project_state, dict):
                system_status["project_phase"] = project_state.get("current_phase", "未知")
                system_status["project_name"] = project_state.get("name", "未命名项目")
                system_status["project_version"] = project_state.get("version", "N/A")
            else:
                system_status["project_phase"] = "错误"
                system_status["project_name"] = "错误"
                system_status["project_version"] = "错误"

            # 活动工作流状态
            workflow_status = all_statuses.get("workflow", {})
            if isinstance(workflow_status, dict):
                # 尝试提取活动工作流
                sessions = workflow_status.get("sessions", [])
                active_sessions = [s for s in sessions if s.get("status") == "IN_PROGRESS"]
                system_status["active_workflow"] = active_sessions[0]["name"] if active_sessions else "无"
                system_status["workflow_count"] = len(sessions)
            else:
                system_status["active_workflow"] = "无"
                system_status["workflow_count"] = 0

            # 包含任务状态摘要
            system_status["task_summary"] = all_statuses.get("task", {"error": "Task provider 未运行或出错"})

            # 路线图状态摘要
            roadmap_status = all_statuses.get("roadmap", {})
            if isinstance(roadmap_status, dict) and "error" not in roadmap_status:
                system_status["roadmap"] = {
                    "status": roadmap_status.get("status", "未知"),
                    "milestones": len(roadmap_status.get("milestone_status", {})),
                }
            else:
                system_status["roadmap"] = {"status": "错误", "error": roadmap_status.get("error", "未知错误")}

            # 健康状态
            system_status["health"] = all_statuses.get("health", {"error": "Health provider 未运行或出错"})

            if detailed:
                # 包含所有获取的状态
                system_status["all_domain_details"] = all_statuses

            return system_status
        except Exception as e:
            logger.error(f"获取系统状态时出错: {e}", exc_info=True)
            return {"error": f"获取系统状态失败: {e}"}

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
        if not phase:
            return {"status": "error", "error": "缺少项目阶段参数", "code": "MISSING_PHASE"}

        valid_phases = ["planning", "development", "testing", "release", "maintenance"]
        if phase.lower() not in valid_phases:
            return {"status": "error", "error": f"无效的项目阶段: {phase}", "code": "INVALID_PHASE", "suggestions": [f"有效的项目阶段: {', '.join(valid_phases)}"]}

        try:
            # 更新项目状态
            self.update_project_state("phase", phase.lower())

            # 设置适当的进度
            phase_progress = {"planning": 20, "development": 40, "testing": 60, "release": 80, "maintenance": 100}
            self.update_project_state("progress", phase_progress.get(phase.lower(), 0))

            return {"status": "success", "message": f"已将项目阶段更新为: {phase}", "phase": phase, "系统信息": "项目阶段已更新"}
        except Exception as e:
            logger.error(f"更新项目阶段时出错: {e}", exc_info=True)
            return {"status": "error", "error": f"更新项目阶段失败: {str(e)}", "code": "UPDATE_FAILED"}

    def initialize_project_status(self, project_name: str = None) -> Dict[str, Any]:
        """初始化项目状态

        Args:
            project_name: 项目名称，如果为None则使用默认名称

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 设置项目名称
            name = project_name if project_name else "VibeCopilot"
            self.update_project_state("name", name)

            # 设置默认阶段和进度
            self.update_project_state("phase", "planning")
            self.update_project_state("progress", 20)
            self.update_project_state("start_time", time.time())

            return {
                "status": "success",
                "message": f"项目 '{name}' 状态已初始化",
                "name": name,
                "phase": "planning",
                "progress": 20,
                "初始化成功": True,
                "系统信息": "项目已初始化",
            }
        except Exception as e:
            logger.error(f"初始化项目状态时出错: {e}", exc_info=True)
            return {"status": "error", "error": f"初始化项目状态失败: {str(e)}", "code": "INIT_FAILED"}

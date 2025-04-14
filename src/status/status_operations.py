"""
状态操作模块

提供状态查询和更新的功能实现
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_domain_status(provider_manager, domain: str, entity_id: Optional[str] = None) -> Dict[str, Any]:
    """获取指定领域的状态信息

    Args:
        provider_manager: 提供者管理器实例
        domain: 领域名称
        entity_id: 可选的实体ID

    Returns:
        Dict[str, Any]: 状态信息
    """
    logger.debug(f"获取领域状态: {domain}, 实体ID: {entity_id}")
    try:
        provider = provider_manager.get_provider(domain)
        if provider is None:
            logger.error(f"未找到领域 '{domain}' 的状态提供者")
            return {"error": f"未找到领域 '{domain}' 的状态提供者", "code": "PROVIDER_NOT_FOUND", "suggestions": ["检查提供者是否正确注册", "确认领域名称是否正确"]}

        # 打印详细日志
        logger.info(f"调用状态提供者: domain={domain}, entity_id={entity_id}, provider类型={type(provider).__name__}")

        # 调用提供者的 get_status 方法
        status_data = provider.get_status(entity_id) if entity_id else provider.get_status()

        # 记录返回的状态数据
        logger.info(f"提供者返回的状态数据: {status_data}")

        if status_data is None:
            logger.error(f"无法获取领域 '{domain}' 的状态")
            return {"error": f"无法获取领域 '{domain}' 的状态", "code": "STATUS_FETCH_FAILED", "suggestions": ["检查数据库连接", "验证实体ID是否存在"]}

        return status_data

    except Exception as e:
        logger.error(f"获取领域 '{domain}' 状态时出错: {e}", exc_info=True)
        return {"error": f"获取领域 '{domain}' 状态失败: {str(e)}", "code": "STATUS_ERROR", "suggestions": ["检查日志获取详细错误信息", "确认系统配置是否正确"]}


def get_system_status(provider_manager, detailed: bool = False) -> Dict[str, Any]:
    """获取整体系统状态 (聚合所有 Provider)

    Args:
        provider_manager: 提供者管理器实例
        detailed: 是否包含详细信息

    Returns:
        Dict[str, Any]: 系统状态
    """
    logger.debug(f"获取系统状态 (detailed={detailed})...")
    system_status = {}
    try:
        all_statuses = provider_manager.get_all_status()

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


def update_status(provider_manager, subscriber_manager, domain: str, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
    """更新实体状态

    统一更新各领域实体状态的入口，并通知订阅者

    Args:
        provider_manager: 提供者管理器实例
        subscriber_manager: 订阅者管理器实例
        domain: 领域名称
        entity_id: 实体ID
        status: 新状态
        **kwargs: 附加参数

    Returns:
        Dict[str, Any]: 更新结果
    """
    logger.debug(f"更新状态: {domain}/{entity_id} -> {status}")
    try:
        provider = provider_manager.get_provider(domain)
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
            subscriber_manager.notify_status_changed(domain, entity_id, old_status, status, result)

        return result

    except Exception as e:
        logger.error(f"更新状态时出错: {e}", exc_info=True)
        return {"error": str(e), "updated": False}


def update_project_phase(project_state, subscriber_manager, phase: str) -> Dict[str, Any]:
    """更新项目阶段

    Args:
        project_state: 项目状态实例
        subscriber_manager: 订阅者管理器实例
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
        project_state.update_state("phase", phase.lower())

        # 设置适当的进度
        phase_progress = {"planning": 20, "development": 40, "testing": 60, "release": 80, "maintenance": 100}
        project_state.update_state("progress", phase_progress.get(phase.lower(), 0))

        # 获取更新后的项目状态
        updated_state = project_state.get_project_state()

        # 通知订阅者
        subscriber_manager.notify_subscribers("project_state", updated_state)

        return {"status": "success", "message": f"已将项目阶段更新为: {phase}", "phase": phase, "系统信息": "项目阶段已更新"}
    except Exception as e:
        logger.error(f"更新项目阶段时出错: {e}", exc_info=True)
        return {"status": "error", "error": f"更新项目阶段失败: {str(e)}", "code": "UPDATE_FAILED"}


def initialize_project_status(project_state, subscriber_manager, project_name: str = None) -> Dict[str, Any]:
    """初始化项目状态

    Args:
        project_state: 项目状态实例
        subscriber_manager: 订阅者管理器实例
        project_name: 项目名称，如果为None则使用默认名称

    Returns:
        Dict[str, Any]: 操作结果
    """
    try:
        # 设置项目名称
        name = project_name if project_name else "VibeCopilot"
        project_state.update_state("name", name)

        # 设置默认阶段和进度
        project_state.update_state("phase", "planning")
        project_state.update_state("progress", 20)
        project_state.update_state("start_time", time.time())

        # 获取更新后的状态
        updated_state = project_state.get_project_state()

        # 通知订阅者
        subscriber_manager.notify_subscribers("project_state", updated_state)

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

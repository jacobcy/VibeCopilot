#!/usr/bin/env python3
"""
VibeCopilot - 任务工具函数模块

提供任务更新、阶段推进等任务管理功能
"""

import logging
import os
from typing import Optional

from src.core.state_manager import ProjectPhase, StateManager, TaskStatus

# 配置日志
logger = logging.getLogger(__name__)


def update_task(
    project_path: Optional[str] = None,
    phase: str = None,
    task_id: str = None,
    status: str = None,
    progress: int = None,
) -> bool:
    """
    更新任务状态

    Args:
        project_path: 项目路径
        phase: 阶段名称
        task_id: 任务ID
        status: 新状态
        progress: 新进度

    Returns:
        是否成功
    """
    if not phase or not task_id or not status:
        logger.error("缺少必要参数: phase, task_id, status")
        return False

    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, "data/temp")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 验证阶段和状态
    try:
        ProjectPhase(phase)  # 只验证值有效，不赋值给变量
    except ValueError:
        logger.error(f"无效的阶段: {phase}")
        logger.info(f"有效的阶段: {[p.value for p in ProjectPhase]}")
        return False

    try:
        status_enum = TaskStatus(status)
    except ValueError:
        logger.error(f"无效的状态: {status}")
        logger.info(f"有效的状态: {[s.value for s in TaskStatus]}")
        return False

    # 更新任务状态
    state_manager = StateManager(path)
    result = state_manager.set_task_status(phase, task_id, status_enum, progress)

    if result:
        logger.info(f"已更新任务 [{phase}] {task_id} 的状态为 {status}")
        if progress is not None:
            logger.info(f"已更新任务进度为 {progress}%")

    return result


def advance_phase(project_path: Optional[str] = None) -> bool:
    """
    推进到下一个项目阶段

    Args:
        project_path: 项目路径

    Returns:
        是否成功
    """
    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, "data/temp")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 推进阶段
    state_manager = StateManager(path)
    current_phase = state_manager.get_current_phase()

    result = state_manager.advance_phase()

    if result:
        new_phase = state_manager.get_current_phase()
        logger.info(f"已从阶段 {current_phase} 推进到 {new_phase}")
    else:
        logger.warning("无法推进到下一阶段")

    return result


def update_document(project_path: Optional[str] = None, doc_type: str = None, status: str = None) -> bool:
    """
    更新文档状态

    Args:
        project_path: 项目路径
        doc_type: 文档类型
        status: 新状态

    Returns:
        是否成功
    """
    if not doc_type or not status:
        logger.error("缺少必要参数: doc_type, status")
        return False

    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, "data/temp")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 验证状态
    valid_statuses = ["not_created", "in_progress", "created"]
    if status not in valid_statuses:
        logger.error(f"无效的文档状态: {status}")
        logger.info(f"有效的状态: {valid_statuses}")
        return False

    # 更新文档状态
    state_manager = StateManager(path)
    result = state_manager.set_document_status(doc_type, status)

    if result:
        logger.info(f"已更新文档 {doc_type} 的状态为 {status}")

    return result

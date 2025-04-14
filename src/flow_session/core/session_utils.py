#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话相关工具函数

提供会话管理相关的工具函数
"""

from typing import Any, Dict, Optional

from src.flow_session.core.utils import echo_error, echo_info, echo_success, format_time, get_db_session, get_error_code, output_json


def format_session_dict(session: Any, verbose: bool = False) -> Dict[str, Any]:
    """格式化会话对象为字典

    Args:
        session: 会话对象
        verbose: 是否包含详细信息

    Returns:
        格式化后的会话字典
    """
    try:
        if isinstance(session, dict):
            return session

        # 确保对象有to_dict方法
        if hasattr(session, "to_dict") and callable(getattr(session, "to_dict")):
            return session.to_dict()

        # 手动创建字典
        session_dict = {
            "id": getattr(session, "id", None),
            "name": getattr(session, "name", None),
            "workflow_id": getattr(session, "workflow_id", None),
            "status": getattr(session, "status", None),
            "current_stage_id": getattr(session, "current_stage_id", None),
            "created_at": format_time(getattr(session, "created_at", None)),
            "updated_at": format_time(getattr(session, "updated_at", None)),
            "completed_stages": getattr(session, "completed_stages", []),
            "context": getattr(session, "context", {}),
            "task_id": getattr(session, "task_id", None),
        }

        # 检查会话是否有当前阶段，如果没有则尝试设置
        if not session_dict["current_stage_id"]:
            try:
                # 导入必要的模块
                from src.flow_session.manager import FlowSessionManager

                # 获取数据库会话
                db_session = get_db_session()

                # 创建会话管理器
                manager = FlowSessionManager(db_session)

                # 获取第一个阶段并设置为当前阶段
                first_stage_id = manager.get_session_first_stage(session.id)

                if first_stage_id:
                    # 更新字典中的当前阶段ID
                    session_dict["current_stage_id"] = first_stage_id

                    if verbose:
                        echo_info(f"已自动设置会话 {session.id} 的当前阶段为 {first_stage_id}")
            except Exception as e:
                if verbose:
                    echo_error(f"自动设置会话阶段失败: {str(e)}")

        # 如果有关联任务，获取任务信息
        task_id = getattr(session, "task_id", None)
        if task_id:
            try:
                # 获取关联任务信息
                from src.db.repositories.task_repository import TaskRepository

                # 使用当前会话的数据库会话
                db_session = session.object_session if hasattr(session, "object_session") else None

                if db_session:
                    task_repo = TaskRepository(db_session)
                    task = task_repo.get_by_id(task_id)
                    if task:
                        session_dict["task_title"] = task.title
                    else:
                        session_dict["task_title"] = "任务未找到"
                else:
                    # 如果无法获取数据库会话，尝试从当前会话名称中提取任务信息
                    session_name = getattr(session, "name", "")
                    if task_id in session_name:
                        # 如果会话名称包含任务ID，可能是按约定命名的格式
                        session_dict["task_title"] = session_name
                    else:
                        session_dict["task_title"] = f"任务 {task_id}"
            except Exception as e:
                echo_error(f"获取任务信息时出错: {str(e)}")
                # 尝试从会话名称中获取信息作为备选
                session_name = getattr(session, "name", "")
                if session_name and len(session_name) > 0:
                    session_dict["task_title"] = session_name
                else:
                    session_dict["task_title"] = f"任务 {task_id}"
        else:
            session_dict["task_title"] = "-"

        # 添加详细信息如果需要
        if verbose and not isinstance(session, dict):
            # 可以在这里添加更多详细字段
            pass

        return session_dict
    except Exception as e:
        echo_error(f"转换会话对象时出错: {str(e)}")
        return {}


def format_session_list(sessions: list, verbose: bool = False) -> list:
    """格式化会话列表

    Args:
        sessions: 会话对象列表
        verbose: 是否包含详细信息

    Returns:
        格式化后的会话字典列表
    """
    session_dicts = []
    for session in sessions:
        session_dict = format_session_dict(session, verbose)
        if session_dict:
            session_dicts.append(session_dict)
    return session_dicts

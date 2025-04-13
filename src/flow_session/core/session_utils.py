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
        }

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流会话处理函数

提供工作流会话管理的核心功能实现
"""

import datetime
import json
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union

import click
from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.flow_session.status.status import SessionStatus


@contextmanager
def get_db_session() -> Session:
    """获取数据库会话的上下文管理器"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def format_time(timestamp: Optional[datetime.datetime], iso_format: bool = False) -> str:
    """格式化时间戳

    Args:
        timestamp: 时间戳
        iso_format: 是否使用ISO格式

    Returns:
        格式化后的时间字符串
    """
    if not timestamp:
        timestamp = datetime.datetime.now()

    if iso_format:
        return timestamp.isoformat()

    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_progress(completed: int, total: int) -> str:
    """格式化进度百分比

    Args:
        completed: 已完成数量
        total: 总数量

    Returns:
        格式化后的进度百分比
    """
    if total <= 0:
        return "0%"

    percentage = (completed / total) * 100
    return f"{percentage:.1f}%"


def echo_success(message: str) -> None:
    """打印成功消息

    Args:
        message: 消息内容
    """
    click.echo(click.style(message, fg="green"))


def echo_error(message: str) -> None:
    """打印错误消息

    Args:
        message: 消息内容
    """
    click.echo(click.style(f"错误: {message}", fg="red"), err=True)


def echo_info(message: str) -> None:
    """打印信息消息

    Args:
        message: 消息内容
    """
    click.echo(message)


def echo_warning(message: str) -> None:
    """打印警告消息

    Args:
        message: 消息内容
    """
    click.echo(click.style(f"警告: {message}", fg="yellow"))


def confirm_action(message: str) -> bool:
    """确认操作

    Args:
        message: 确认消息

    Returns:
        是否确认
    """
    return click.confirm(message)


def output_json(data: Dict[str, Any]) -> None:
    """以JSON格式输出数据

    Args:
        data: 要输出的数据
    """
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def output_text(data: Union[str, Dict[str, Any]], is_success: bool = True) -> None:
    """以文本格式输出数据

    Args:
        data: 要输出的数据
        is_success: 是否成功消息
    """
    if isinstance(data, dict):
        message = data.get("message", str(data))
    else:
        message = data

    if is_success:
        echo_success(message)
    else:
        echo_error(message)


def get_error_code(error_type: str) -> str:
    """获取标准化的错误代码

    Args:
        error_type: 错误类型

    Returns:
        错误代码
    """
    error_codes = {
        # 会话管理错误
        "SESSION_NOT_FOUND": "FS-001",
        "CREATE_SESSION_ERROR": "FS-002",
        "PAUSE_SESSION_ERROR": "FS-003",
        "RESUME_SESSION_ERROR": "FS-004",
        "ABORT_SESSION_ERROR": "FS-005",
        "DELETE_SESSION_ERROR": "FS-006",
        "LIST_SESSIONS_ERROR": "FS-007",
        "SHOW_SESSION_ERROR": "FS-008",
        # 阶段管理错误
        "STAGE_NOT_FOUND": "FS-101",
        "START_STAGE_ERROR": "FS-102",
        "COMPLETE_STAGE_ERROR": "FS-103",
        "FAIL_STAGE_ERROR": "FS-104",
        # 工作流管理错误
        "WORKFLOW_NOT_FOUND": "FS-201",
        # 通用错误
        "DATABASE_ERROR": "FS-901",
        "VALIDATION_ERROR": "FS-902",
        "OPERATION_CANCELED": "FS-903",
        "UNAUTHORIZED": "FS-904",
        "SYSTEM_ERROR": "FS-999",
    }

    return error_codes.get(error_type, "FS-000")


def get_error_message(error_code: str) -> str:
    """获取错误代码对应的标准错误消息

    Args:
        error_code: 错误代码

    Returns:
        错误消息
    """
    error_messages = {
        "FS-001": "会话不存在",
        "FS-002": "创建会话失败",
        "FS-003": "暂停会话失败",
        "FS-004": "恢复会话失败",
        "FS-005": "终止会话失败",
        "FS-006": "删除会话失败",
        "FS-007": "列出会话失败",
        "FS-008": "显示会话详情失败",
        "FS-101": "阶段不存在",
        "FS-102": "启动阶段失败",
        "FS-103": "完成阶段失败",
        "FS-104": "阶段执行失败",
        "FS-201": "工作流不存在",
        "FS-901": "数据库错误",
        "FS-902": "数据验证错误",
        "FS-903": "操作已取消",
        "FS-904": "未授权操作",
        "FS-999": "系统错误",
    }

    return error_messages.get(error_code, "未知错误")


def format_output(data: Dict[str, Any], format_type: str, is_success: bool = True) -> None:
    """根据指定格式输出数据

    Args:
        data: 要输出的数据
        format_type: 输出格式类型 (json或text)
        is_success: 是否成功消息
    """
    if format_type.lower() == "json":
        output_json(data)
    else:
        output_text(data, is_success)


def handle_session_list():
    """列出所有会话"""
    sessions = FlowSessionManager.list_sessions()
    if not sessions:
        print("当前没有活动的会话")
        return

    for session in sessions:
        print(f"会话ID: {session.id}")
        print(f"工作流: {session.workflow_id}")
        print(f"状态: {session.status}")
        print("---")


def handle_session_stop(session_id: str):
    """停止会话"""
    session = FlowSessionManager.get_session(session_id)
    if not session:
        print(f"会话 {session_id} 不存在")
        return

    session.stop()
    print(f"已停止会话: {session_id}")


def handle_session_resume(session_id: str):
    """恢复会话"""
    session = FlowSessionManager.get_session(session_id)
    if not session:
        print(f"会话 {session_id} 不存在")
        return

    session.resume()
    print(f"已恢复会话: {session_id}")


def handle_session_status(session_id: str):
    """查看会话状态"""
    session = FlowSessionManager.get_session(session_id)
    if not session:
        print(f"会话 {session_id} 不存在")
        return

    print(f"会话ID: {session.id}")
    print(f"工作流: {session.workflow_id}")
    print(f"状态: {session.status}")
    print(f"开始时间: {session.start_time}")
    if session.end_time:
        print(f"结束时间: {session.end_time}")
    print(f"当前步骤: {session.current_step}")
    print("---")

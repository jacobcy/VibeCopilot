#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话相关工具函数模块

提供工作流会话操作的辅助函数，简化命令实现
"""

import logging
from typing import Any, Dict, Optional, Tuple, Union

from rich.console import Console

from src.flow_session.manager import get_current_session, get_session, get_session_first_stage, set_current_stage

console = Console()
logger = logging.getLogger(__name__)


def get_active_session(
    session_id: Optional[str] = None, verbose: bool = False, require_stage: bool = False
) -> Tuple[Union[Dict[str, Any], Any], str, str, Optional[str]]:
    """
    获取活动会话信息

    如果提供了session_id，则尝试获取该ID的会话；
    否则，获取当前活动会话。

    Args:
        session_id: 会话ID (可选)
        verbose: 是否显示详细信息
        require_stage: 是否强制要求返回阶段信息

    Returns:
        Tuple[会话对象, 会话ID, 会话名称, 当前阶段ID]

    Raises:
        SystemExit: 如果无法获取指定会话或当前没有活动会话时，返回适当的错误信息
    """
    target_session = None
    if session_id:
        # 如果指定了会话ID或名称，获取该会话
        target_session = get_session(session_id)
        if not target_session:
            console.print(f"[red]错误: 找不到ID或名称为 '{session_id}' 的会话[/red]")
            return None, "", "", None
    else:
        # 否则使用当前活动会话
        target_session = get_current_session()
        if not target_session:
            console.print("[red]错误: 没有活动会话。请先创建会话或指定会话ID。[/red]")
            console.print("[blue]提示: 使用 'vc flow create session --workflow <工作流ID>' 创建新会话[/blue]")
            return None, "", "", None

    # 处理target_session可能是对象或字典的情况
    if isinstance(target_session, dict):
        session_id = target_session.get("id")
        session_name = target_session.get("name", "unknown")
        current_stage_id = target_session.get("current_stage_id")
    else:
        session_id = target_session.id
        session_name = target_session.name
        current_stage_id = target_session.current_stage_id

    if not session_id:
        console.print("[red]错误: 无法获取当前会话ID[/red]")
        return None, "", "", None

    # 如果当前阶段为空，尝试使用第一个阶段作为当前阶段
    if not current_stage_id:
        try:
            # 尝试获取第一个阶段ID
            first_stage_id = get_session_first_stage(session_id)
            if first_stage_id:
                if verbose:
                    console.print(f"[yellow]会话没有当前阶段，尝试设置第一个阶段: {first_stage_id}[/yellow]")

                # 设置为当前阶段
                set_current_stage(session_id, first_stage_id)
                current_stage_id = first_stage_id

                # 更新target_session的current_stage_id
                if isinstance(target_session, dict):
                    target_session["current_stage_id"] = current_stage_id
                else:
                    target_session.current_stage_id = current_stage_id

                if verbose:
                    console.print(f"[green]已自动设置当前阶段为: {current_stage_id}[/green]")
        except Exception as e:
            logger.warning(f"尝试设置第一个阶段失败: {str(e)}")
            if require_stage:
                console.print("[red]错误: 会话没有当前阶段，且无法找到可用的阶段。请指定阶段ID。[/red]")
                return None, "", "", None
            else:
                if verbose:
                    console.print("[yellow]警告: 会话没有当前阶段，将只显示会话信息[/yellow]")

    if verbose:
        console.print(f"使用会话: {session_name} ({session_id})")
        if current_stage_id:
            console.print(f"当前阶段: {current_stage_id}")

    return target_session, session_id, session_name, current_stage_id

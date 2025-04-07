#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流会话命令处理函数

提供工作流会话命令的处理函数
"""

import io
import logging
import sys
from contextlib import redirect_stdout
from typing import Any, Dict, List, Optional, Tuple

from src.db import get_session_factory, init_db
from src.flow_session.cli import (
    abort_session,
    create_session,
    delete_session,
    list_sessions,
    pause_session,
    resume_session,
    show_session,
)

logger = logging.getLogger(__name__)


def handle_session_command(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理session子命令，直接调用flow_session的CLI函数

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not hasattr(args, "action") or not args.action:
        return False, "未指定会话操作，可用操作: list, show, create, pause, resume, abort, delete", None

    # 捕获标准输出
    captured_output = io.StringIO()

    try:
        with redirect_stdout(captured_output):
            # 获取数据库会话
            engine = init_db()
            SessionFactory = get_session_factory(engine)

            # 根据操作调用相应的函数
            if args.action == "list":
                status = getattr(args, "status", None)
                workflow = getattr(args, "workflow", None)
                list_sessions(status, workflow)

            elif args.action == "show":
                if not hasattr(args, "id") or not args.id:
                    return False, "❌ show操作需要会话ID参数", None
                show_session(args.id)

            elif args.action == "create":
                if not hasattr(args, "workflow") or not args.workflow:
                    return False, "❌ create操作需要工作流ID参数", None
                name = getattr(args, "name", None)
                create_session(args.workflow, name)

            elif args.action == "pause":
                if not hasattr(args, "id") or not args.id:
                    return False, "❌ pause操作需要会话ID参数", None
                pause_session(args.id)

            elif args.action == "resume":
                if not hasattr(args, "id") or not args.id:
                    return False, "❌ resume操作需要会话ID参数", None
                resume_session(args.id)

            elif args.action == "abort":
                if not hasattr(args, "id") or not args.id:
                    return False, "❌ abort操作需要会话ID参数", None
                abort_session(args.id)

            elif args.action == "delete":
                if not hasattr(args, "id") or not args.id:
                    return False, "❌ delete操作需要会话ID参数", None
                force = getattr(args, "force", False)
                delete_session(args.id, force)

            else:
                return False, f"❌ 未知的会话操作: {args.action}", None

        # 获取捕获的输出
        output = captured_output.getvalue()
        return True, output, None

    except Exception as e:
        logger.exception(f"执行会话命令失败: {str(e)}")
        return False, f"❌ 会话命令执行失败: {str(e)}", None

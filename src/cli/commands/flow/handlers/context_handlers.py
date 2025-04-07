#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流上下文处理模块

提供获取工作流上下文的功能
"""

import argparse
import logging
import sys
from io import StringIO
from typing import Any, Dict, Optional, Tuple

from src.cli.commands.flow.handlers.base_handlers import format_stage_summary
from src.workflow.workflow_operations import get_workflow_context, view_workflow

logger = logging.getLogger(__name__)


def handle_get_workflow_context(workflow_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理获取工作流上下文命令

    Args:
        workflow_id: 工作流ID

    Returns:
        包含状态、消息和上下文数据的元组
    """
    try:
        # 先查看工作流详情
        args = argparse.Namespace()
        args.id = workflow_id
        args.verbose = False

        # 收集输出
        original_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # 执行函数
        view_workflow(args)

        # 恢复标准输出
        sys.stdout = original_stdout
        output = captured_output.getvalue()

        if "工作流不存在" in output:
            return False, f"找不到ID为 '{workflow_id}' 的工作流", None

        # 解析工作流信息
        workflow = {
            "id": workflow_id,
            "name": output.split("(ID:")[0].strip().split(" ", 1)[1].strip(),
            "stages": [],
        }

        # 创建一个空的进度数据对象，因为get_workflow_context需要这个参数
        progress_data = {}
        context = get_workflow_context(workflow_id, progress_data)

        if not context:
            return True, "工作流尚未有上下文数据", {}

        current_stage = context.get("current_stage")
        completed_checks = context.get("completed_checks", [])

        # 找到当前阶段
        stage_data = None
        for stage in workflow.get("stages", []):
            if stage.get("name") == current_stage:
                stage_data = stage
                break

        stage_summary = ""
        if stage_data:
            stage_summary = format_stage_summary(stage_data, completed_checks)

        message = f"工作流: {workflow.get('name')}\n"
        message += f"当前阶段: {current_stage or '未开始'}\n"
        message += f"进度: {len(completed_checks)} 项已完成\n\n"

        if stage_summary:
            message += "当前阶段详情:\n\n" + stage_summary

        return True, message, context

    except Exception as e:
        logger.exception("获取工作流上下文时出错")
        return False, f"获取工作流上下文时出错: {str(e)}", None

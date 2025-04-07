#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流列表处理模块

提供列出工作流的功能
"""

import argparse
import logging
import sys
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from src.cli.commands.flow.handlers.base_handlers import format_workflow_summary
from src.workflow.workflow_operations import list_workflows

logger = logging.getLogger(__name__)


def handle_list_workflows() -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """
    处理列出工作流命令

    Returns:
        包含状态、消息和工作流列表的元组
    """
    try:
        # 创建参数对象
        args = argparse.Namespace()
        args.verbose = False

        # 收集输出以便返回结构化数据
        original_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # 执行函数
        list_workflows(args)

        # 恢复标准输出
        sys.stdout = original_stdout
        output = captured_output.getvalue()

        # 提取工作流数据
        if "没有找到工作流" in output:
            return True, "没有找到工作流。", []

        # 从输出中解析工作流信息
        workflows = []
        lines = output.strip().split("\n")

        # 跳过第一行（标题行）
        for line in lines[1:]:
            if line.strip():
                # 简单解析，可能需要根据实际输出格式调整
                parts = line.strip().split(": ", 1)
                if len(parts) > 1:
                    id_name = parts[1].split(" (")[0]
                    id_parts = parts[0].split(" ")
                    workflow_id = id_parts[-1]
                    status = "active" if "🟢" in line else "inactive"
                    workflows.append({"id": workflow_id, "name": id_name, "status": status})

        summaries = []
        for workflow in workflows:
            summaries.append(format_workflow_summary(workflow))

        message = f"找到 {len(workflows)} 个工作流\n\n" + "\n\n".join(summaries)
        return True, message, workflows

    except Exception as e:
        logger.exception("列出工作流时出错")
        return False, f"列出工作流时出错: {str(e)}", None

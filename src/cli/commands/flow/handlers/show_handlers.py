#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流查看处理模块

提供查看工作流详情的功能
"""

import argparse
import json
import logging
import sys
from io import StringIO
from typing import Any, Dict, Optional, Tuple

from src.cli.commands.flow.handlers.base_handlers import (
    format_stage_summary,
    format_workflow_summary,
)
from src.workflow.workflow_operations import view_workflow

logger = logging.getLogger(__name__)


def handle_show_workflow(
    workflow_id: str, format_type: str = "text", verbose: bool = False
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理查看工作流命令

    Args:
        workflow_id: 工作流ID
        format_type: 输出格式 ("json" 或 "text")
        verbose: 是否显示详细信息

    Returns:
        包含状态、消息和工作流数据的元组
    """
    try:
        # 创建参数对象
        args = argparse.Namespace()
        args.id = workflow_id
        args.verbose = verbose

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
            "name": output.split("(ID:")[0].strip().split(" ", 1)[1].strip()
            if "(ID:" in output
            else "未知",
            "stages": [],
        }

        # 提取步骤信息
        if "步骤:" in output:
            steps_section = output.split("步骤:")[1].split("\n\n")[0]
            steps_lines = steps_section.strip().split("\n")
            for line in steps_lines:
                if line.strip() and line.strip().startswith("  "):
                    step_info = line.strip()
                    step_num = step_info.split(".")[0].strip()
                    step_name = step_info.split(".")[1].split("(")[0].strip()
                    workflow["stages"].append(
                        {"id": f"stage_{step_num}", "name": step_name, "order": int(step_num) - 1}
                    )

        # 根据格式返回结果
        if format_type == "json":
            return True, json.dumps(workflow, ensure_ascii=False, indent=2), workflow
        else:
            workflow_summary = format_workflow_summary(workflow)

            stage_summaries = []
            for stage in workflow.get("stages", []):
                stage_summaries.append(format_stage_summary(stage))

            message = f"{workflow_summary}\n\n"
            if stage_summaries:
                message += "阶段详情:\n\n"
                message += "\n\n".join(stage_summaries)
            else:
                message += output

            return True, message, workflow

    except Exception as e:
        logger.exception("查看工作流时出错")
        return False, f"查看工作流时出错: {str(e)}", None

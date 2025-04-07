#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流导出处理模块

提供导出工作流为不同格式的功能
"""

import argparse
import json
import logging
import sys
from io import StringIO
from typing import Any, Dict, Optional, Tuple, Union

from src.cli.commands.flow.exporters import JsonExporter, MermaidExporter
from src.workflow.workflow_operations import view_workflow

logger = logging.getLogger(__name__)


def handle_export_workflow(
    workflow_id: str, format_type: str
) -> Tuple[bool, str, Optional[Union[str, Dict[str, Any]]]]:
    """
    处理导出工作流命令

    Args:
        workflow_id: 工作流ID
        format_type: 导出格式类型，支持json、mermaid

    Returns:
        包含状态、消息和导出数据的元组
    """
    try:
        # 先查看工作流
        args = argparse.Namespace()
        args.id = workflow_id
        args.verbose = True

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

        if format_type.lower() == "json":
            exporter = JsonExporter()
            result = exporter.export(workflow)
            return True, f"成功导出工作流为JSON格式", json.loads(result)

        elif format_type.lower() == "mermaid":
            exporter = MermaidExporter()
            result = exporter.export(workflow)
            return True, f"成功导出工作流为Mermaid格式", result

        else:
            return False, f"不支持的导出格式: {format_type}", None

    except Exception as e:
        logger.exception("导出工作流时出错")
        return False, f"导出工作流时出错: {str(e)}", None

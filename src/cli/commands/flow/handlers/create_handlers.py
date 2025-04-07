#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流创建处理模块

提供从规则或模板创建工作流的功能
"""

import argparse
import logging
import sys
from io import StringIO
from typing import Any, Dict, Optional, Tuple

from src.cli.commands.flow.handlers.base_handlers import format_workflow_summary
from src.parsing.processors import RuleProcessor
from src.workflow.interpreter.flow_converter import FlowConverter
from src.workflow.workflow_operations import create_workflow

logger = logging.getLogger(__name__)


def handle_create_workflow(rule_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理创建工作流命令

    Args:
        rule_path: 规则文件路径

    Returns:
        包含状态、消息和工作流数据的元组
    """
    try:
        # 使用新的RuleProcessor处理规则文件
        rule_processor = RuleProcessor()
        rule_data = rule_processor.process_rule_file(rule_path)

        if not rule_data:
            return False, f"无法解析规则文件: {rule_path}", None

        # 使用flow_converter转换规则到工作流
        converter = FlowConverter()
        workflow = converter.convert_rule_to_workflow(rule_data)

        if not workflow:
            return False, "无法从规则创建工作流", None

        # 使用新的工作流管理函数保存工作流
        args = argparse.Namespace()
        args.name = workflow.get("name")
        args.description = workflow.get("description", "")
        args.active = True
        args.n8n_id = None

        # 收集输出
        original_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # 执行创建
        create_workflow(args, workflow)

        # 恢复标准输出
        sys.stdout = original_stdout
        output = captured_output.getvalue()

        saved = "成功" in output
        if not saved:
            return False, "保存工作流失败", None

        summary = format_workflow_summary(workflow)
        return True, f"成功创建工作流:\n\n{summary}", workflow

    except Exception as e:
        logger.exception("创建工作流时出错")
        return False, f"创建工作流时出错: {str(e)}", None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理函数模块

提供列出、创建、查看和获取工作流上下文的功能
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from src.cli.commands.flow.exporters import JsonExporter, MermaidExporter
from src.cli.commands.flow.handlers.base_handlers import (
    format_stage_summary,
    format_workflow_summary,
)
from src.core.parsing import RuleParser
from src.flows.converters import FlowConverter
from src.flows.workflow import WorkflowManager
from src.flows.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


def handle_list_workflows() -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """
    处理列出工作流命令

    Returns:
        包含状态、消息和工作流列表的元组
    """
    try:
        workflow_manager = WorkflowManager()
        workflows = workflow_manager.list_workflows()

        if not workflows:
            return True, "没有找到工作流。", []

        summaries = []
        for workflow in workflows:
            summaries.append(format_workflow_summary(workflow))

        message = f"找到 {len(workflows)} 个工作流\n\n" + "\n\n".join(summaries)
        return True, message, workflows

    except Exception as e:
        logger.exception("列出工作流时出错")
        return False, f"列出工作流时出错: {str(e)}", None


def handle_create_workflow(rule_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理创建工作流命令

    Args:
        rule_path: 规则文件路径

    Returns:
        包含状态、消息和工作流数据的元组
    """
    try:
        rule_parser = RuleParser()
        rule_data = rule_parser.parse_rule_file(rule_path)

        if not rule_data:
            return False, f"无法解析规则文件: {rule_path}", None

        converter = FlowConverter()
        workflow = converter.convert_rule_to_workflow(rule_data)

        if not workflow:
            return False, "无法从规则创建工作流", None

        workflow_manager = WorkflowManager()
        saved = workflow_manager.save_workflow(workflow)

        if not saved:
            return False, "保存工作流失败", None

        summary = format_workflow_summary(workflow)
        return True, f"成功创建工作流:\n\n{summary}", workflow

    except Exception as e:
        logger.exception("创建工作流时出错")
        return False, f"创建工作流时出错: {str(e)}", None


def handle_view_workflow(workflow_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理查看工作流命令

    Args:
        workflow_id: 工作流ID

    Returns:
        包含状态、消息和工作流数据的元组
    """
    try:
        workflow_manager = WorkflowManager()
        workflow = workflow_manager.get_workflow(workflow_id)

        if not workflow:
            return False, f"找不到ID为 '{workflow_id}' 的工作流", None

        workflow_summary = format_workflow_summary(workflow)

        stage_summaries = []
        for stage in workflow.get("stages", []):
            stage_summaries.append(format_stage_summary(stage))

        message = f"{workflow_summary}\n\n"
        message += "阶段详情:\n\n"
        message += "\n\n".join(stage_summaries)

        return True, message, workflow

    except Exception as e:
        logger.exception("查看工作流时出错")
        return False, f"查看工作流时出错: {str(e)}", None


def handle_get_workflow_context(workflow_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理获取工作流上下文命令

    Args:
        workflow_id: 工作流ID

    Returns:
        包含状态、消息和上下文数据的元组
    """
    try:
        workflow_manager = WorkflowManager()
        workflow = workflow_manager.get_workflow(workflow_id)

        if not workflow:
            return False, f"找不到ID为 '{workflow_id}' 的工作流", None

        workflow_engine = WorkflowEngine()
        context = workflow_engine.get_context(workflow_id)

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
        workflow_manager = WorkflowManager()
        workflow = workflow_manager.get_workflow(workflow_id)

        if not workflow:
            return False, f"找不到ID为 '{workflow_id}' 的工作流", None

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

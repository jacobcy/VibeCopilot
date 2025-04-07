#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程类型处理函数模块

提供特定类型流程的处理和管理功能
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.cli.commands.flow.handlers.workflow_handlers import handle_create_workflow
from src.core.config import get_project_root
from src.workflow.config import list_templates
from src.workflow.template_loader import create_workflow_from_template, load_flow_template

logger = logging.getLogger(__name__)


def handle_flow_type(flow_type: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理特定类型的流程命令

    根据请求的流程类型，检查是否存在相应的工作流，
    如果不存在则从对应的规则模板创建。

    Args:
        flow_type: 流程类型，例如 coding, spec, review

    Returns:
        包含状态、消息和工作流数据的元组
    """
    # 将类型转换为规范格式
    flow_type = flow_type.lower().strip()

    # 添加后缀，匹配规则命名约定
    if not flow_type.endswith("-flow"):
        flow_type_id = f"{flow_type}-flow"
    else:
        flow_type_id = flow_type

    try:
        # 首先检查是否有对应的模板
        template_data = load_flow_template(flow_type_id)
        if template_data:
            logger.info(f"找到 {flow_type_id} 模板")

            # 从模板创建工作流
            workflow = create_workflow_from_template(flow_type_id)
            if workflow:
                return True, f"成功从模板创建 {flow_type_id} 工作流", workflow
            else:
                return False, f"从模板创建 {flow_type_id} 工作流失败", None

        # 如果没有找到模板，尝试从规则创建
        logger.info(f"未找到 {flow_type_id} 模板，尝试从规则创建")

        # 查找对应的规则文件
        rule_paths = _find_flow_rule_paths(flow_type_id)

        if not rule_paths:
            available_templates = list_templates()
            if available_templates:
                template_list = "\n".join([f"- {t}" for t in available_templates])
                return False, f"找不到与 {flow_type_id} 对应的规则或模板。\n\n可用的模板有:\n{template_list}", None
            else:
                return False, f"找不到与 {flow_type_id} 对应的规则或模板", None

        # 创建工作流
        success = False
        message = f"尝试从以下路径创建 {flow_type_id} 工作流:\n"

        for rule_path in rule_paths:
            logger.info(f"尝试从规则创建工作流: {rule_path}")
            success, create_message, workflow = handle_create_workflow(rule_path)
            message += f"\n- {rule_path}: {'成功' if success else '失败'}"

            if success:
                logger.info(f"成功从规则 {rule_path} 创建 {flow_type_id} 工作流")
                return True, f"已创建 {flow_type_id} 工作流", workflow

        return False, f"无法创建 {flow_type_id} 工作流: {message}", None

    except Exception as e:
        logger.exception(f"处理流程类型 {flow_type} 时出错")
        return False, f"处理流程类型 {flow_type} 时出错: {str(e)}", None


def _find_flow_rule_paths(flow_type_id: str) -> list:
    """
    查找与特定流程类型相关的规则文件路径

    Args:
        flow_type_id: 流程类型标识符

    Returns:
        包含匹配规则文件路径的列表
    """
    rule_paths = []

    # 获取项目根目录
    project_root = get_project_root()

    # 在flow-rules目录中查找
    flow_rules_dir = os.path.join(project_root, ".cursor", "rules", "flow-rules")
    if os.path.exists(flow_rules_dir):
        for filename in os.listdir(flow_rules_dir):
            if (
                filename.lower() == f"{flow_type_id}.md"
                or filename.lower() == f"{flow_type_id}.mdc"
            ):
                rule_paths.append(os.path.join(flow_rules_dir, filename))

    # 在.cursor/rules/flow-rules目录中查找
    cursor_rules_dir = os.path.join(project_root, ".cursor", "rules", "flow-rules")
    if os.path.exists(cursor_rules_dir):
        for filename in os.listdir(cursor_rules_dir):
            if (
                filename.lower() == f"{flow_type_id}.md"
                or filename.lower() == f"{flow_type_id}.mdc"
            ):
                rule_paths.append(os.path.join(cursor_rules_dir, filename))

    return rule_paths

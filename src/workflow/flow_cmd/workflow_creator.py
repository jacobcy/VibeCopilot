"""
工作流创建器模块

处理从规则或模板创建工作流的功能
"""

import logging
import os
from typing import Any, Dict, Optional

from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.interpreter.flow_converter import FlowConverter
from src.workflow.interpreter.rule_parser import RuleParser
from src.workflow.template_loader import create_workflow_from_template, load_flow_template

logger = logging.getLogger(__name__)


def create_workflow_from_rule(rule_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从规则文件创建工作流

    Args:
        rule_path: 规则文件路径
        output_path: 输出文件路径，不提供则自动生成

    Returns:
        工作流定义
    """
    # 解析规则
    rule_parser = RuleParser()
    rule_data = rule_parser.parse_rule_file(rule_path)

    if not rule_data:
        logger.error(f"解析规则文件失败: {rule_path}")
        return {}

    # 转换为工作流
    converter = FlowConverter()
    workflow = converter.convert_rule_to_workflow(rule_data)

    # 保存工作流定义
    if workflow:
        exporter = JsonExporter()
        exporter.export_workflow(workflow, output_path)

        logger.info(f"已从规则创建工作流: {workflow.get('id')}")

        # 输出Mermaid图
        mermaid_exporter = MermaidExporter()
        mermaid_code = mermaid_exporter.export_workflow(workflow)
        logger.info(f"工作流Mermaid图:\n{mermaid_code}")

    return workflow


def create_workflow_from_template_with_vars(
    template_name: str, variables: Dict[str, Any], output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    从模板创建工作流，并应用变量

    Args:
        template_name: 模板名称
        variables: 模板变量
        output_path: 输出文件路径，不提供则自动生成

    Returns:
        工作流定义
    """
    # 加载模板
    template = load_flow_template(template_name)

    if not template:
        logger.error(f"加载模板失败: {template_name}")
        return {}

    # 创建工作流
    workflow = create_workflow_from_template(template, variables)

    # 保存工作流定义
    if workflow and output_path:
        exporter = JsonExporter()
        exporter.export_workflow(workflow, output_path)
        logger.info(f"已从模板创建工作流: {workflow.get('id')}")

    return workflow

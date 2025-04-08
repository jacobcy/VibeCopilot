#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流创建器

提供从规则或模板创建工作流的功能
"""

import logging
import os
from typing import Any, Dict, Optional

from src.rule_engine.parser import parse_rule_content
from src.utils.file_utils import read_json_file, read_text_file, write_json_file
from src.workflow.workflow_operations import create_workflow

logger = logging.getLogger(__name__)


def create_workflow_from_rule(rule_path: str, output_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    从规则文件创建工作流

    Args:
        rule_path: 规则文件路径
        output_path: 输出文件路径（可选）

    Returns:
        Optional[Dict[str, Any]]: 创建的工作流数据或None
    """
    try:
        # 读取规则文件
        rule_content = read_text_file(rule_path)

        # 解析规则内容
        rule_data = parse_rule_content(rule_content)

        if not rule_data:
            logger.error(f"解析规则文件失败: {rule_path}")
            return None

        # 提取规则元数据
        meta = rule_data.get("meta", {})

        # 创建工作流数据
        workflow_data = {
            "name": meta.get("title", os.path.basename(rule_path).split(".")[0]),
            "description": meta.get("description", "从规则创建的工作流"),
            "type": meta.get("type", "workflow"),
            "tags": meta.get("tags", []),
            "steps": [],
        }

        # 如果规则中有流程定义，则添加步骤
        if "process" in rule_data:
            process = rule_data["process"]
            for i, step in enumerate(process):
                workflow_data["steps"].append(
                    {
                        "id": f"step_{i+1}",
                        "name": step.get("name", f"步骤 {i+1}"),
                        "description": step.get("description", ""),
                        "type": "script",  # 默认为脚本类型
                        "order": i + 1,
                        "config": {"script": step.get("action", "")},
                    }
                )

        # 创建工作流
        workflow = create_workflow(workflow_data)

        # 如果提供了输出路径，则写入文件
        if output_path:
            write_json_file(output_path, workflow)
            logger.info(f"工作流已保存到: {output_path}")

        return workflow

    except Exception as e:
        logger.error(f"从规则创建工作流时出错: {str(e)}", exc_info=True)
        return None


def create_workflow_from_template_with_vars(
    template_name: str, variables: Dict[str, Any] = None, output_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    从模板创建工作流，支持变量替换

    Args:
        template_name: 模板名称
        variables: 模板变量（可选）
        output_path: 输出文件路径（可选）

    Returns:
        Optional[Dict[str, Any]]: 创建的工作流数据或None
    """
    from src.core.config import get_config

    try:
        # 获取模板目录
        config = get_config()
        templates_dir = os.path.join(config.get("paths.templates_dir", ""), "workflows")

        # 查找模板文件
        template_path = os.path.join(templates_dir, f"{template_name}.json")
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            return None

        # 读取模板
        template = read_json_file(template_path)

        # 替换变量
        if variables:
            template = _replace_variables(template, variables)

        # 创建工作流
        workflow = create_workflow(template)

        # 如果提供了输出路径，则写入文件
        if output_path:
            write_json_file(output_path, workflow)
            logger.info(f"工作流已保存到: {output_path}")

        return workflow

    except Exception as e:
        logger.error(f"从模板创建工作流时出错: {str(e)}", exc_info=True)
        return None


def _replace_variables(data: Any, variables: Dict[str, Any]) -> Any:
    """递归替换数据中的变量"""
    if isinstance(data, str):
        # 替换字符串中的变量，格式为 {{variable_name}}
        for key, value in variables.items():
            data = data.replace(f"{{{{{key}}}}}", str(value))
        return data

    elif isinstance(data, dict):
        # 替换字典中的值
        return {key: _replace_variables(value, variables) for key, value in data.items()}

    elif isinstance(data, list):
        # 替换列表中的值
        return [_replace_variables(item, variables) for item in data]

    else:
        # 其他类型不处理
        return data

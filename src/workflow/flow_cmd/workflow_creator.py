#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流创建器

提供从规则或模板创建工作流的功能
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from rich import print_json
from rich.console import Console
from rich.panel import Panel

from src.parsing.processors.workflow_processor import WorkflowProcessor
from src.utils.file_utils import read_json_file, read_text_file, write_json_file
from src.workflow.operations import create_workflow

logger = logging.getLogger(__name__)
console = Console()


async def create_workflow_from_rule(rule_path: str) -> Optional[Dict[str, Any]]:
    """
    从规则文件创建工作流

    Args:
        rule_path: 规则文件路径

    Returns:
        Optional[Dict[str, Any]]: 工作流数据，如果创建失败则返回None
    """
    try:
        # 读取规则文件
        with open(rule_path, "r", encoding="utf-8") as f:
            rule_content = f.read()

        # 使用WorkflowProcessor解析工作流结构
        processor = WorkflowProcessor()
        workflow_structure = await processor.parse_workflow_rule(rule_content)

        if not workflow_structure:
            error_msg = "规则解析失败: 无法从规则内容中提取工作流结构"
            logger.error(error_msg)
            console.print(f"\n[bold red]✗[/bold red] {error_msg}")
            return None

        # 生成工作流ID
        workflow_structure["id"] = str(uuid.uuid4())

        # 确保工作流结构包含必要字段
        if "name" not in workflow_structure:
            workflow_structure["name"] = os.path.splitext(os.path.basename(rule_path))[0]
        if "description" not in workflow_structure:
            workflow_structure["description"] = f"从规则文件 {rule_path} 创建的工作流"

        # 打印解析结果
        console.print("\n[bold green]规则解析成功！[/bold green]")
        console.print(Panel(json.dumps(workflow_structure, ensure_ascii=False, indent=2), title="工作流结构", border_style="green"))

        return workflow_structure

    except FileNotFoundError:
        error_msg = f"规则文件不存在: {rule_path}"
        logger.error(error_msg)
        console.print(f"\n[bold red]✗[/bold red] {error_msg}")
        return None
    except Exception as e:
        error_msg = f"从规则创建工作流时出错: {str(e)}"
        logger.error(error_msg)
        console.print(f"\n[bold red]✗[/bold red] {error_msg}")
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

        # 确保工作流结构包含必要字段
        if "id" not in template:
            template["id"] = str(uuid.uuid4())
        if "name" not in template:
            template["name"] = template_name
        if "description" not in template:
            template["description"] = f"从模板 {template_name} 创建的工作流"

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

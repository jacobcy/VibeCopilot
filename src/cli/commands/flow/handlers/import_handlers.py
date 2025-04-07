#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流导入处理模块

提供导入工作流定义的功能
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

from src.workflow.config import WORKFLOW_DIR
from src.workflow.exporters.json_exporter import JsonExporter

logger = logging.getLogger(__name__)


def handle_import_workflow(
    file_path: str, overwrite: bool = False, verbose: bool = False
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理导入工作流命令

    Args:
        file_path: 工作流定义文件路径
        overwrite: 是否覆盖同名工作流
        verbose: 是否显示详细信息

    Returns:
        包含状态、消息和导入的工作流数据的元组
    """
    try:
        # 验证文件存在
        if not os.path.exists(file_path):
            return False, f"找不到文件: '{file_path}'", None

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                workflow = json.load(file)
            except json.JSONDecodeError:
                return False, f"无效的JSON文件: '{file_path}'", None

        # 验证工作流结构
        if not isinstance(workflow, dict) or "id" not in workflow:
            return False, f"无效的工作流定义: 缺少'id'字段", None

        # 检查工作流是否已存在
        exporter = JsonExporter()
        workflow_id = workflow.get("id")
        existing_workflow = exporter.load_workflow(workflow_id)

        if existing_workflow and not overwrite:
            return False, f"工作流 '{workflow_id}' 已存在。使用 --overwrite 参数覆盖现有工作流。", None

        # 导入工作流
        output_path = os.path.join(WORKFLOW_DIR, f"{workflow_id}.json")
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump(workflow, out_file, ensure_ascii=False, indent=2)

        # 准备响应消息
        action = "更新" if existing_workflow else "导入"
        message = f"✅ 已{action}工作流: '{workflow_id}'\n"
        message += f"- 名称: {workflow.get('name', '未命名')}\n"
        message += f"- 文件: {output_path}\n"

        # 显示阶段信息
        stages = workflow.get("stages", [])
        if stages:
            message += f"- 包含 {len(stages)} 个阶段\n"
            if verbose:
                message += "\n阶段列表:\n"
                for i, stage in enumerate(stages, 1):
                    message += f"  {i}. {stage.get('name', f'阶段{i}')}\n"

        return True, message, workflow

    except Exception as e:
        logger.exception(f"导入工作流时出错: {file_path}")
        return False, f"导入工作流时出错: {str(e)}", None

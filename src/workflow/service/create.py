#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流创建操作

提供工作流的创建功能。
"""

import datetime
import logging
import os
import uuid
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel

from src.utils.file_utils import ensure_directory_exists, write_json_file
from src.validation.core.workflow_validator import WorkflowValidator
from src.workflow.service.base import get_workflows_directory
from src.workflow.service.get import get_workflow_by_name

logger = logging.getLogger(__name__)
console = Console()


def create_workflow(workflow_data: Dict[str, Any], save_dir: str = None) -> Dict[str, Any]:
    """
    创建工作流

    Args:
        workflow_data: 工作流数据
        save_dir: 保存目录（可选）

    Returns:
        Dict[str, Any]: 创建的工作流数据

    Raises:
        ValueError: 工作流数据无效
        OSError: 保存工作流文件失败
    """
    # 检查是否存在同名工作流
    existing_workflow = get_workflow_by_name(workflow_data.get("name"))

    # 如果存在同名工作流，生成新的ID
    if existing_workflow:
        # 生成8个字符的短ID
        short_id = str(uuid.uuid4())[:8]
        workflow_data["id"] = short_id
        logger.info(f"发现同名工作流，生成新ID: {workflow_data['id']}")
    elif "id" not in workflow_data:
        # 如果不存在同名工作流且未提供ID，生成新ID
        short_id = str(uuid.uuid4())[:8]
        workflow_data["id"] = short_id
        logger.info(f"生成新工作流ID: {workflow_data['id']}")

    # 添加或更新时间戳
    current_time = datetime.datetime.now().isoformat()
    if "metadata" not in workflow_data:
        workflow_data["metadata"] = {}

    # 保留原始创建时间，更新修改时间
    if existing_workflow and "metadata" in existing_workflow:
        workflow_data["metadata"]["created_at"] = existing_workflow["metadata"].get("created_at", current_time)
    else:
        workflow_data["metadata"]["created_at"] = current_time
    workflow_data["metadata"]["updated_at"] = current_time

    # 验证工作流数据
    validator = WorkflowValidator()
    validation_result = validator.validate(workflow_data)
    if not validation_result.is_valid:
        error_msg = "工作流数据验证失败:\n" + "\n".join(f"  - {error}" for error in validation_result.errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    # 确定保存目录
    workflows_dir = save_dir if save_dir else get_workflows_directory()
    ensure_directory_exists(workflows_dir)

    # 构建工作流文件路径
    workflow_path = os.path.join(workflows_dir, f"{workflow_data['id']}.json")

    try:
        # 保存工作流文件
        write_json_file(workflow_path, workflow_data)
        logger.info(f"工作流已保存: {workflow_path}")

        # 在控制台显示创建成功信息
        console.print(
            Panel.fit(
                f"[bold green]✓ 工作流创建成功[/bold green]\n\n"
                f"[cyan]基本信息[/cyan]\n"
                f"ID: {workflow_data['id']}\n"
                f"名称: {workflow_data.get('name', 'Unnamed')}\n"
                f"描述: {workflow_data.get('description', '无描述')}\n"
                f"版本: {workflow_data.get('version', '1.0.0')}\n\n"
                f"[cyan]统计信息[/cyan]\n"
                f"阶段数: {len(workflow_data.get('stages', []))}\n"
                f"转换数: {len(workflow_data.get('transitions', []))}\n\n"
                f"[cyan]存储信息[/cyan]\n"
                f"保存位置: {workflow_path}\n"
                f"创建时间: {workflow_data['metadata']['created_at']}\n"
                f"更新时间: {workflow_data['metadata']['updated_at']}",
                title="工作流创建结果",
                border_style="green",
            )
        )

        return workflow_data
    except OSError as e:
        error_msg = f"保存工作流文件失败: {str(e)}"
        logger.error(error_msg)
        raise OSError(error_msg) from e

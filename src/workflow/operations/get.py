#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流获取操作

提供工作流的获取功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.utils.file_utils import file_exists, read_json_file
from src.workflow.operations.base import get_workflow_file_path, get_workflows_directory
from src.workflow.operations.list import list_workflows
from src.workflow.operations.sync import sync_workflow_to_db

logger = logging.getLogger(__name__)


def get_workflow(workflow_id: str, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    通过ID获取工作流

    Args:
        workflow_id: 工作流ID
        verbose: 是否显示详细日志

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    workflows_dir = get_workflows_directory()

    # 尝试直接通过ID查找
    workflow_path = os.path.join(workflows_dir, f"{workflow_id}.json")
    if file_exists(workflow_path):
        workflow_data = read_json_file(workflow_path)
        # 同步到数据库
        sync_workflow_to_db(workflow_data, verbose)
        return workflow_data

    # 如果直接查找失败，则遍历所有工作流查找
    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            try:
                workflow_path = os.path.join(workflows_dir, filename)
                workflow_data = read_json_file(workflow_path)
                if workflow_data.get("id") == workflow_id:
                    # 同步到数据库
                    sync_workflow_to_db(workflow_data, verbose)
                    return workflow_data
            except Exception as e:
                if verbose:
                    logger.error(f"读取工作流文件失败 {filename}: {str(e)}")

    return None


def get_workflow_by_id(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    通过ID获取工作流（与get_workflow功能相同的别名函数）

    Args:
        workflow_id: 工作流ID

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    return get_workflow(workflow_id)


def get_workflow_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    通过名称获取工作流

    Args:
        name: 工作流名称

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    workflows = list_workflows()

    for workflow in workflows:
        if workflow.get("name") == name:
            # 同步到数据库
            sync_workflow_to_db(workflow)
            return workflow

    return None


def get_workflow_by_type(workflow_type: str) -> List[Dict[str, Any]]:
    """
    通过类型获取工作流列表

    Args:
        workflow_type: 工作流类型

    Returns:
        List[Dict[str, Any]]: 符合指定类型的工作流列表
    """
    workflows = list_workflows()
    return [workflow for workflow in workflows if workflow.get("type") == workflow_type]


def view_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    查看工作流（别名方法）

    Args:
        workflow_id: 工作流ID

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    return get_workflow(workflow_id)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流基础操作

提供工作流的基本管理功能，包括增删改查。
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Union

from src.core.config import get_config
from src.models.workflow import Workflow
from src.utils.file_utils import ensure_directory_exists, file_exists, read_json_file, write_json_file


def get_workflows_directory() -> str:
    """获取工作流目录路径"""
    config = get_config()
    return os.path.join(config.get("paths.data_dir", "."), "workflows")


def get_workflow_file_path(workflow_id: str) -> str:
    """
    获取工作流文件的完整路径

    Args:
        workflow_id: 工作流ID

    Returns:
        str: 工作流文件的完整路径
    """
    workflows_dir = get_workflows_directory()
    return os.path.join(workflows_dir, f"{workflow_id}.json")


def list_workflows() -> List[Dict[str, Any]]:
    """
    列出所有工作流

    Returns:
        List[Dict[str, Any]]: 工作流列表（字典形式）
    """
    workflows_dir = get_workflows_directory()
    ensure_directory_exists(workflows_dir)

    workflows = []

    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            workflow_path = os.path.join(workflows_dir, filename)
            try:
                workflow_data = read_json_file(workflow_path)
                workflows.append(workflow_data)
            except Exception as e:
                print(f"Error reading workflow file {filename}: {str(e)}")

    return workflows


def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    通过ID获取工作流

    Args:
        workflow_id: 工作流ID

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    workflows_dir = get_workflows_directory()

    # 尝试直接通过ID查找
    workflow_path = os.path.join(workflows_dir, f"{workflow_id}.json")
    if file_exists(workflow_path):
        return read_json_file(workflow_path)

    # 如果直接查找失败，则遍历所有工作流查找
    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            try:
                workflow_path = os.path.join(workflows_dir, filename)
                workflow_data = read_json_file(workflow_path)
                if workflow_data.get("id") == workflow_id:
                    return workflow_data
            except Exception as e:
                print(f"Error reading workflow file {filename}: {str(e)}")

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


def create_workflow(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建新工作流

    Args:
        workflow_data: 工作流数据

    Returns:
        Dict[str, Any]: 创建的工作流数据
    """
    workflows_dir = get_workflows_directory()
    ensure_directory_exists(workflows_dir)

    # 确保有ID
    if "id" not in workflow_data:
        workflow_data["id"] = str(uuid.uuid4())

    # 保存工作流文件
    workflow_path = os.path.join(workflows_dir, f"{workflow_data['id']}.json")
    write_json_file(workflow_path, workflow_data)

    return workflow_data


def update_workflow(workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    更新现有工作流

    Args:
        workflow_id: 工作流ID
        workflow_data: 更新的工作流数据

    Returns:
        Optional[Dict[str, Any]]: 更新后的工作流数据
    """
    # 确保工作流存在
    existing_workflow = get_workflow(workflow_id)
    if not existing_workflow:
        return None

    # 更新数据
    workflow_data["id"] = workflow_id  # 确保ID一致

    # 保存更新后的工作流
    workflows_dir = get_workflows_directory()
    workflow_path = os.path.join(workflows_dir, f"{workflow_id}.json")
    write_json_file(workflow_path, workflow_data)

    return workflow_data


def delete_workflow(workflow_id: str) -> bool:
    """
    删除工作流

    Args:
        workflow_id: 工作流ID

    Returns:
        bool: 是否成功删除
    """
    workflows_dir = get_workflows_directory()
    workflow_path = os.path.join(workflows_dir, f"{workflow_id}.json")

    if file_exists(workflow_path):
        try:
            os.remove(workflow_path)
            return True
        except Exception as e:
            print(f"Error deleting workflow {workflow_id}: {str(e)}")
            return False

    # 如果直接路径没找到，尝试遍历查找
    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            try:
                path = os.path.join(workflows_dir, filename)
                data = read_json_file(path)
                if data.get("id") == workflow_id:
                    os.remove(path)
                    return True
            except Exception as e:
                print(f"Error processing workflow file {filename}: {str(e)}")

    return False

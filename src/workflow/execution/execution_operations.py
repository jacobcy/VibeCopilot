#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行操作

提供工作流执行相关的功能，包括执行历史获取、保存等。
"""

import datetime
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file

logger = logging.getLogger(__name__)


def save_execution(execution_data: Dict[str, Any]) -> bool:
    """
    保存工作流执行数据到持久化存储

    Args:
        execution_data: 执行数据

    Returns:
        bool: 是否保存成功
    """
    execution_id = execution_data.get("execution_id")
    workflow_id = execution_data.get("workflow_id")

    logger.info(f"保存工作流执行数据: 执行ID:{execution_id}, 工作流ID:{workflow_id}")

    try:
        # 获取存储目录
        config = get_config()
        data_dir = config.get("paths.data_dir", "data")
        if not os.path.isabs(data_dir):
            # 如果是相对路径，转换为绝对路径
            data_dir = os.path.abspath(data_dir)

        executions_dir = os.path.join(data_dir, "workflow_executions")
        ensure_directory_exists(executions_dir)

        # 生成文件名
        filename = f"{execution_id}.json"
        file_path = os.path.join(executions_dir, filename)

        # 保存数据到文件
        write_json_file(file_path, execution_data)

        logger.info(f"已保存执行数据到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存执行数据失败: {str(e)}")
        return False


def get_workflow_executions(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的执行历史记录

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 执行历史记录列表
    """
    config = get_config()
    # 获取data_dir路径，确保配置正确访问
    data_dir = config.get("paths.data_dir", ".")
    executions_dir = os.path.join(data_dir, "workflow_executions")

    if not os.path.exists(executions_dir):
        return []

    executions = []

    # 查找匹配工作流ID的执行记录
    for filename in os.listdir(executions_dir):
        if filename.startswith(f"{workflow_id}_") and filename.endswith(".json"):
            execution_path = os.path.join(executions_dir, filename)
            try:
                execution_data = read_json_file(execution_path)
                executions.append(execution_data)
            except Exception as e:
                logger.error(f"读取执行文件 {filename} 出错: {str(e)}")

    # 按执行时间排序（从新到旧）
    executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return executions


def get_executions_for_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的所有执行记录

    这是更推荐使用的新API，相比get_workflow_executions函数增加了日志记录

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 执行记录列表
    """
    logger.info(f"获取工作流执行历史: 工作流ID:{workflow_id}")
    return get_workflow_executions(workflow_id)


def get_execution_by_id(execution_id: str) -> Optional[Dict[str, Any]]:
    """
    通过执行ID获取执行记录

    Args:
        execution_id: 执行ID

    Returns:
        Optional[Dict[str, Any]]: 执行记录或None
    """
    config = get_config()
    data_dir = config.get("paths.data_dir", ".")
    executions_dir = os.path.join(data_dir, "workflow_executions")

    if not os.path.exists(executions_dir):
        return None

    # 遍历所有执行记录文件
    for filename in os.listdir(executions_dir):
        if filename.endswith(".json"):
            execution_path = os.path.join(executions_dir, filename)
            try:
                execution_data = read_json_file(execution_path)
                if execution_data.get("execution_id") == execution_id:
                    return execution_data
            except Exception as e:
                logger.error(f"读取执行文件 {filename} 出错: {str(e)}")

    return None


def update_execution_status(execution_id: str, status: str, messages: List[str] = None) -> bool:
    """
    更新执行状态

    Args:
        execution_id: 执行ID
        status: 新状态
        messages: 要添加的消息列表

    Returns:
        bool: 更新是否成功
    """
    execution = get_execution_by_id(execution_id)
    if not execution:
        logger.error(f"找不到执行记录: {execution_id}")
        return False

    execution["status"] = status
    if messages:
        if "messages" not in execution:
            execution["messages"] = []
        execution["messages"].extend(messages)

    # 更新结束时间（如果是终态）
    if status in ["completed", "failed", "aborted"]:
        execution["end_time"] = datetime.datetime.now().isoformat()

    return save_execution(execution)

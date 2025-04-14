#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流搜索模块

提供工作流的搜索和模糊匹配功能。
"""

import logging
from typing import Any, Dict, Optional

from src.workflow.service import get_workflow, get_workflow_by_id, get_workflow_by_name, list_workflows

logger = logging.getLogger(__name__)


def get_workflow_fuzzy(identifier: str) -> Optional[Dict[str, Any]]:
    """
    通过模糊匹配查找工作流，支持ID、名称或部分匹配

    Args:
        identifier: 工作流ID、名称或部分匹配字符串

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）或None
    """
    logger.debug(f"开始查找工作流: '{identifier}'")

    # 尝试精确匹配ID
    workflow = get_workflow(identifier)
    if workflow:
        logger.info(f"通过ID精确匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
        return workflow

    # 尝试精确匹配名称
    workflow = get_workflow_by_name(identifier)
    if workflow:
        logger.info(f"通过名称精确匹配找到工作流: {workflow.get('name')} (ID: {workflow.get('id')})")
        return workflow

    # 开始模糊匹配
    logger.debug(f"未找到精确匹配，开始进行模糊匹配: '{identifier}'")
    workflows = list_workflows()

    if not workflows:
        logger.warning("数据库中没有找到任何工作流定义")
        return None

    # 先尝试ID部分匹配
    for workflow in workflows:
        if identifier.lower() in workflow.get("id", "").lower():
            logger.info(f"通过ID部分匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
            return workflow

    # 然后尝试名称部分匹配
    for workflow in workflows:
        workflow_name = workflow.get("name", "").lower()
        if workflow_name and identifier.lower() in workflow_name:
            logger.info(f"通过名称部分匹配找到工作流: {workflow.get('name')} (ID: {workflow.get('id')})")
            return workflow

    # 最后尝试描述匹配
    for workflow in workflows:
        description = workflow.get("description", "").lower()
        if description and identifier.lower() in description:
            logger.info(f"通过描述匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
            return workflow

    # 查找类型匹配
    for workflow in workflows:
        workflow_type = workflow.get("type", "").lower()
        if workflow_type and identifier.lower() == workflow_type:
            logger.info(f"通过类型匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
            return workflow

    logger.warning(f"未找到匹配的工作流: '{identifier}'")

    # 打印所有可用的工作流，帮助用户排查
    logger.debug("可用的工作流列表:")
    for wf in workflows:
        logger.debug(f"- {wf.get('name', '未命名')} (ID: {wf.get('id')}, 类型: {wf.get('type', '未知')})")

    return None

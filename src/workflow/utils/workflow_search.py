#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流搜索模块

提供工作流的搜索和模糊匹配功能。
"""

import logging
import re
from typing import Any, Dict, Optional

from src.workflow.service import get_workflow, get_workflow_by_id, get_workflow_by_name, list_workflows

logger = logging.getLogger(__name__)


def is_likely_id(identifier: str) -> bool:
    """
    判断标识符是否可能是一个ID（而非名称）

    Args:
        identifier: 标识符字符串

    Returns:
        bool: 如果标识符可能是ID则返回True
    """
    # 如果完全由数字和字母组成，且长度为8个字符，很可能是ID
    if re.match(r"^[0-9a-f]{8}$", identifier.lower()):
        return True
    return False


def get_workflow_fuzzy(identifier: str) -> Optional[Dict[str, Any]]:
    """
    通过模糊匹配查找工作流，支持ID、名称或部分匹配

    Args:
        identifier: 工作流ID、名称或部分匹配字符串

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）或None
    """
    logger.debug(f"开始查找工作流: '{identifier}'")

    if not identifier:
        logger.error("工作流标识符不能为空")
        return None

    # 先判断是否可能是ID格式
    is_id = is_likely_id(identifier)

    # 如果看起来像ID，优先使用ID查找
    if is_id:
        logger.debug(f"'{identifier}'符合ID格式，优先使用ID查找")
        # 尝试精确匹配ID
        workflow = get_workflow_by_id(identifier)
        if workflow:
            logger.info(f"通过ID精确匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
            return workflow

    # 尝试精确匹配名称
    workflow = get_workflow_by_name(identifier)
    if workflow:
        logger.info(f"通过名称精确匹配找到工作流: {workflow.get('name')} (ID: {workflow.get('id')})")
        return workflow

    # 如果直接匹配失败，继续模糊匹配
    logger.debug(f"未找到精确匹配，开始进行模糊匹配: '{identifier}'")
    workflows = list_workflows()

    if not workflows:
        logger.warning("数据库中没有找到任何工作流定义")
        return None

    # 先尝试ID部分匹配
    for workflow in workflows:
        workflow_id = workflow.get("id", "").lower()
        if workflow_id and identifier.lower() in workflow_id:
            logger.info(f"通过ID部分匹配找到工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id')})")
            return workflow

    # 然后尝试名称部分匹配
    matching_workflows = []
    for workflow in workflows:
        workflow_name = workflow.get("name", "").lower()
        if workflow_name and identifier.lower() in workflow_name:
            matching_workflows.append(workflow)

    # 如果有多个匹配的工作流，选择名称最相似的一个
    if matching_workflows:
        if len(matching_workflows) == 1:
            logger.info(f"通过名称部分匹配找到工作流: {matching_workflows[0].get('name')} (ID: {matching_workflows[0].get('id')})")
            return matching_workflows[0]
        else:
            # 如果有多个匹配，选择名称完全相等的，或者最短的那个（最精确的匹配）
            for wf in matching_workflows:
                if wf.get("name", "").lower() == identifier.lower():
                    logger.info(f"多个匹配中找到名称完全匹配的工作流: {wf.get('name')} (ID: {wf.get('id')})")
                    return wf

            # 没有完全匹配，选择第一个
            logger.warning(f"找到多个匹配的工作流，选择第一个: {matching_workflows[0].get('name')} (ID: {matching_workflows[0].get('id')})")
            return matching_workflows[0]

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

    # 输出详细错误信息
    logger.warning(f"未找到匹配的工作流: '{identifier}'")
    logger.debug("可用的工作流列表:")
    for wf in workflows:
        logger.debug(f"- {wf.get('name', '未命名')} (ID: {wf.get('id')}, 类型: {wf.get('type', '未知')})")

    workflow_names = [wf.get("name", "未命名") for wf in workflows]
    workflow_ids = [wf.get("id", "") for wf in workflows]

    error_message = f"找不到ID或名称为 '{identifier}' 的工作流，请检查拼写是否正确。"
    error_message += f"\n可用的工作流: {', '.join(workflow_names)}"
    error_message += f"\n可用的工作流ID: {', '.join(workflow_ids)}"

    logger.error(error_message)
    return None

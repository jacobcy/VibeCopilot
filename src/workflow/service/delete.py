#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流删除操作

提供工作流的删除功能。
"""

import logging
import os

from src.workflow.service.base import get_workflows_directory

logger = logging.getLogger(__name__)


def delete_workflow(workflow_id: str, workflow_dir: str = None) -> bool:
    """
    删除工作流

    Args:
        workflow_id: 工作流ID
        workflow_dir: 工作流目录（可选，默认使用配置的工作流目录）

    Returns:
        删除是否成功
    """
    try:
        logger.info(f"开始删除工作流 '{workflow_id}'...")

        # 确定工作流目录
        if workflow_dir is None:
            workflow_dir = get_workflows_directory()

        # 构建工作流文件路径
        workflow_file = os.path.join(workflow_dir, f"{workflow_id}.json")

        # 检查工作流文件是否存在
        if not os.path.exists(workflow_file):
            # 文件不存在视为删除成功（幂等性）
            logger.info(f"工作流文件已不存在: {workflow_file}，视为删除成功")
            return True

        # 删除工作流文件
        os.remove(workflow_file)
        logger.info(f"工作流 '{workflow_id}' 删除成功")
        return True

    except Exception as e:
        logger.error(f"删除工作流失败: {str(e)}")
        return False

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流更新操作

提供工作流的更新功能。
"""

import logging
import os
from typing import Any, Dict

from src.utils.file_utils import write_json_file
from src.validation.core.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


def update_workflow(workflow_id: str, workflow_data: Dict[str, Any], workflow_dir: str) -> bool:
    """
    更新现有工作流

    Args:
        workflow_id: 工作流ID
        workflow_data: 更新的工作流数据
        workflow_dir: 工作流目录

    Returns:
        更新是否成功
    """
    try:
        logger.info(f"开始更新工作流 '{workflow_id}'...")

        # 确保工作流数据中的ID与传入的workflow_id一致
        data_id = workflow_data.get("id")
        if data_id and data_id != workflow_id:
            logger.warning(f"工作流数据中的ID ({data_id}) 与目标ID ({workflow_id}) 不匹配，自动修正为 {workflow_id}")
            # 修正ID，使其与文件名一致
            workflow_data["id"] = workflow_id

        # 如果数据中没有ID，则添加
        if "id" not in workflow_data:
            logger.warning(f"工作流数据中缺少ID，自动添加ID: {workflow_id}")
            workflow_data["id"] = workflow_id

        # 验证工作流数据
        validator = WorkflowValidator()
        is_valid, errors = validator.validate_workflow(workflow_data)
        if not is_valid:
            logger.error("更新的工作流数据验证失败:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        # 检查工作流文件是否存在
        workflow_file = os.path.join(workflow_dir, f"{workflow_id}.json")
        if not os.path.exists(workflow_file):
            logger.error(f"工作流文件不存在: {workflow_file}")
            return False

        # 保存更新后的工作流
        if write_json_file(workflow_file, workflow_data):
            logger.info(f"工作流 '{workflow_id}' 更新成功")
            return True
        else:
            logger.error(f"保存更新后的工作流失败: {workflow_file}")
            return False

    except Exception as e:
        logger.error(f"更新工作流失败: {str(e)}")
        return False

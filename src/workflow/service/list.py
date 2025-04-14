#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流列表操作

提供工作流的列表查询功能。
"""

import logging
import os
from typing import Any, Dict, List

from src.utils.file_utils import ensure_directory_exists, read_json_file
from src.workflow.service.base import get_workflows_directory

logger = logging.getLogger(__name__)


def list_workflows() -> List[Dict[str, Any]]:
    """
    列出所有工作流

    Returns:
        List[Dict[str, Any]]: 工作流列表（字典形式）
    """
    workflows_dir = get_workflows_directory()
    ensure_directory_exists(workflows_dir)

    workflows = []
    processed_ids = set()  # 用于跟踪已处理的ID

    for filename in os.listdir(workflows_dir):
        if filename.endswith(".json"):
            workflow_path = os.path.join(workflows_dir, filename)
            try:
                workflow_data = read_json_file(workflow_path)
                workflow_id = workflow_data.get("id")

                # 跳过没有ID的工作流
                if not workflow_id:
                    logger.warning(f"工作流文件缺少ID: {filename}")
                    continue

                # 检查ID是否已经处理过（避免重复）
                if workflow_id in processed_ids:
                    logger.warning(f"发现重复的工作流ID: {workflow_id}，在文件 {filename}")
                    continue

                # 检查文件名是否与ID一致（排除后缀）
                expected_filename = f"{workflow_id}.json"
                if filename != expected_filename:
                    # 对于不一致的情况，添加警告日志
                    logger.warning(f"工作流文件名与ID不匹配: {filename} 包含ID {workflow_id}")

                    # 如果我们能找到与ID匹配的文件，则跳过当前文件
                    if os.path.exists(os.path.join(workflows_dir, expected_filename)):
                        logger.info(f"已存在匹配ID的文件 {expected_filename}，跳过 {filename}")
                        continue
                    else:
                        # 如果文件名与ID不匹配，且没有匹配ID的文件，也跳过
                        # 这可能是由于删除操作后的遗留文件
                        logger.warning(f"文件名 {filename} 与其ID {workflow_id} 不匹配，且没有找到匹配的文件，可能需要修复")
                        continue

                # 将ID添加到已处理集合中
                processed_ids.add(workflow_id)
                workflows.append(workflow_data)
            except Exception as e:
                logger.error(f"读取工作流文件失败 {filename}: {str(e)}")

    return workflows

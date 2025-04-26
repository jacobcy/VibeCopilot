#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流列表操作

提供工作流的列表查询功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Add database imports
from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

# Remove file system imports
# from src.utils.file_utils import ensure_directory_exists, read_json_file
# from src.workflow.service.base import get_workflows_directory


logger = logging.getLogger(__name__)


def list_workflows(session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    列出所有工作流 (从数据库读取)

    Args:
        session: 可选的 SQLAlchemy 会话对象。如果未提供，将创建临时会话。

    Returns:
        List[Dict[str, Any]]: 工作流列表（字典形式）
    """
    logger.info("从数据库列出所有工作流定义...")
    workflows_data = []

    # Determine if we need to manage the session locally
    manage_session_locally = session is None
    db_session = session if session else None

    try:
        # Create a session if one wasn't provided
        if manage_session_locally:
            logger.debug("No session provided to list_workflows, creating temporary one.")
            db_session = get_session_factory()()

        repo = WorkflowDefinitionRepository()
        # Get list of WorkflowDefinition objects using the determined session
        workflow_objects = repo.get_all(db_session)

        logger.debug(f"从数据库获取到 {len(workflow_objects)} 个工作流对象")

        for workflow_obj in workflow_objects:
            try:
                if hasattr(workflow_obj, "to_dict") and callable(workflow_obj.to_dict):
                    workflow_dict = workflow_obj.to_dict()
                else:
                    # Fallback: Manually create dict from attributes if no to_dict
                    workflow_dict = {
                        "id": workflow_obj.id,
                        "name": workflow_obj.name,
                        "description": workflow_obj.description,
                        "type": workflow_obj.type,
                        # "version": workflow_obj.version, # Model doesn't have version anymore
                        # "metadata": workflow_obj.metadata, # Model doesn't have metadata
                        "stages_data": workflow_obj.stages_data if hasattr(workflow_obj, "stages_data") else [],
                        # "transitions_data": workflow_obj.transitions_data if hasattr(workflow_obj, 'transitions_data') else [] # Model doesn't have transitions
                    }
                workflows_data.append(workflow_dict)
            except Exception as conversion_e:
                logger.error(f"转换工作流对象 (ID: {getattr(workflow_obj, 'id', 'N/A')}) 为字典失败: {conversion_e}", exc_info=True)

    except Exception as e:
        logger.error(f"从数据库列出工作流失败: {e}", exc_info=True)
        return []
    finally:
        # Close the session only if it was created locally
        if manage_session_locally and db_session:
            logger.debug("Closing temporary session in list_workflows.")
            db_session.close()

    logger.info(f"成功从数据库获取 {len(workflows_data)} 个工作流定义")
    return workflows_data


# Remove old file-based implementation
# def list_workflows_file_based() -> List[Dict[str, Any]]:
#     workflows_dir = get_workflows_directory()
#     ensure_directory_exists(workflows_dir)
#
#     workflows = []
#     processed_ids = set()  # 用于跟踪已处理的ID
#
#     for filename in os.listdir(workflows_dir):
#         if filename.endswith(".json"):
#             workflow_path = os.path.join(workflows_dir, filename)
#             try:
#                 workflow_data = read_json_file(workflow_path)
#                 workflow_id = workflow_data.get("id")
#
#                 # 跳过没有ID的工作流
#                 if not workflow_id:
#                     logger.warning(f"工作流文件缺少ID: {filename}")
#                     continue
#
#                 # 检查ID是否已经处理过（避免重复）
#                 if workflow_id in processed_ids:
#                     logger.warning(f"发现重复的工作流ID: {workflow_id}，在文件 {filename}")
#                     continue
#
#                 # 检查文件名是否与ID一致（排除后缀）
#                 expected_filename = f"{workflow_id}.json"
#                 if filename != expected_filename:
#                     # 对于不一致的情况，添加警告日志
#                     logger.warning(f"工作流文件名与ID不匹配: {filename} 包含ID {workflow_id}")
#
#                     # 如果我们能找到与ID匹配的文件，则跳过当前文件
#                     if os.path.exists(os.path.join(workflows_dir, expected_filename)):
#                         logger.info(f"已存在匹配ID的文件 {expected_filename}，跳过 {filename}")
#                         continue
#                     else:
#                         # 如果文件名与ID不匹配，且没有匹配ID的文件，也跳过
#                         # 这可能是由于删除操作后的遗留文件
#                         logger.warning(f"文件名 {filename} 与其ID {workflow_id} 不匹配，且没有找到匹配的文件，可能需要修复")
#                         continue
#
#                 # 将ID添加到已处理集合中
#                 processed_ids.add(workflow_id)
#                 workflows.append(workflow_data)
#             except Exception as e:
#                 logger.error(f"读取工作流文件失败 {filename}: {str(e)}")
#
#     return workflows

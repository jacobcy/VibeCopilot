#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流获取操作

提供工作流的获取功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Add database imports
from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.utils.file_utils import file_exists, read_json_file
from src.workflow.service.base import get_workflow_file_path, get_workflows_directory
from src.workflow.service.list import list_workflows
from src.workflow.service.sync import sync_workflow_to_db

logger = logging.getLogger(__name__)


def get_workflow(workflow_id: str, verbose: bool = False, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    通过ID获取工作流 (文件系统查找，如果找到则同步数据库)
    不再直接操作数据库查找，只处理文件和调用同步

    Args:
        workflow_id: 工作流ID
        verbose: 是否显示详细日志
        session: (未使用) 保持签名兼容，但此函数不直接用 session

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    # This function primarily deals with the file system representation
    # and triggers a sync if found. Database lookups are handled elsewhere.
    logger.debug(f"[File Service] Attempting to get workflow by ID from file system: {workflow_id}")
    workflows_dir = get_workflows_directory()

    workflow_path = os.path.join(workflows_dir, f"{workflow_id}.json")
    if file_exists(workflow_path):
        try:
            workflow_data = read_json_file(workflow_path)
            if workflow_data and workflow_data.get("id") == workflow_id:
                logger.debug(f"[File Service] Found workflow file: {workflow_path}. Triggering DB sync.")
                # 同步到数据库 (sync_workflow_to_db will handle its own session)
                sync_workflow_to_db(workflow_data, verbose)
                return workflow_data
            else:
                logger.warning(f"[File Service] File {workflow_path} exists but content ID does not match {workflow_id}.")
        except Exception as e:
            logger.error(f"[File Service] Error reading workflow file {workflow_path}: {e}")

    # If not found directly by ID file, maybe log and return None?
    # The previous logic iterating all files seems inefficient here if DB is primary.
    # If the expectation is that DB is the source of truth, file system check is just for sync.
    logger.debug(f"[File Service] Workflow file for ID {workflow_id} not found or content mismatch.")
    return None


def get_workflow_by_id(workflow_id: str, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    通过ID获取工作流 (从数据库读取)

    Args:
        workflow_id: 工作流ID
        session: 可选的 SQLAlchemy 会话对象。如果未提供，将创建临时会话。

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    logger.debug(f"[DB Service] Getting workflow by ID: {workflow_id}")
    manage_session_locally = session is None
    db_session = session if session else None
    workflow_data = None
    try:
        if manage_session_locally:
            db_session = get_session_factory()()

        repo = WorkflowDefinitionRepository()
        workflow_obj = repo.get_by_id(db_session, workflow_id)

        if workflow_obj:
            if hasattr(workflow_obj, "to_dict") and callable(workflow_obj.to_dict):
                workflow_data = workflow_obj.to_dict()
            else:
                # Fallback conversion
                workflow_data = {
                    "id": workflow_obj.id,
                    "name": workflow_obj.name,
                    "description": workflow_obj.description,
                    "type": workflow_obj.type,
                    "stages_data": workflow_obj.stages_data if hasattr(workflow_obj, "stages_data") else [],
                }
            logger.debug(f"[DB Service] Found workflow by ID {workflow_id}.")
        else:
            logger.debug(f"[DB Service] Workflow with ID {workflow_id} not found in DB.")

    except Exception as e:
        logger.error(f"[DB Service] Error getting workflow by ID {workflow_id}: {e}", exc_info=True)
    finally:
        if manage_session_locally and db_session:
            db_session.close()

    # Optional: Could trigger file sync check here if needed
    # sync_workflow_from_db_if_needed(workflow_data)

    return workflow_data


def get_workflow_by_name(name: str, session: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    通过名称获取工作流 (从数据库读取)

    Args:
        name: 工作流名称
        session: 可选的 SQLAlchemy 会话对象。如果未提供，将创建临时会话。

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）
    """
    logger.debug(f"[DB Service] Getting workflow by name: {name}")
    manage_session_locally = session is None
    db_session = session if session else None
    workflow_data = None
    try:
        if manage_session_locally:
            db_session = get_session_factory()()

        repo = WorkflowDefinitionRepository()
        workflow_obj = repo.get_by_name(db_session, name)  # Assume get_by_name exists

        if workflow_obj:
            if hasattr(workflow_obj, "to_dict") and callable(workflow_obj.to_dict):
                workflow_data = workflow_obj.to_dict()
            else:
                # Fallback conversion
                workflow_data = {
                    "id": workflow_obj.id,
                    "name": workflow_obj.name,
                    "description": workflow_obj.description,
                    "type": workflow_obj.type,
                    "stages_data": workflow_obj.stages_data if hasattr(workflow_obj, "stages_data") else [],
                }
            logger.debug(f"[DB Service] Found workflow by name '{name}'.")
        else:
            logger.debug(f"[DB Service] Workflow with name '{name}' not found in DB.")
    except Exception as e:
        logger.error(f"[DB Service] Error getting workflow by name '{name}': {e}", exc_info=True)
    finally:
        if manage_session_locally and db_session:
            db_session.close()

    return workflow_data


def get_workflow_by_type(workflow_type: str, session: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    通过类型获取工作流列表 (从数据库读取)

    Args:
        workflow_type: 工作流类型
        session: 可选的 SQLAlchemy 会话对象。如果未提供，将创建临时会话。

    Returns:
        List[Dict[str, Any]]: 符合指定类型的工作流列表
    """
    logger.debug(f"[DB Service] Getting workflows by type: {workflow_type}")
    manage_session_locally = session is None
    db_session = session if session else None
    workflows_data = []
    try:
        if manage_session_locally:
            db_session = get_session_factory()()

        repo = WorkflowDefinitionRepository()
        # Assume get_by_type exists and takes session
        workflow_objects = repo.get_by_type(db_session, workflow_type)

        for workflow_obj in workflow_objects:
            if hasattr(workflow_obj, "to_dict") and callable(workflow_obj.to_dict):
                workflow_data = workflow_obj.to_dict()
            else:
                # Fallback conversion
                workflow_data = {
                    "id": workflow_obj.id,
                    "name": workflow_obj.name,
                    "description": workflow_obj.description,
                    "type": workflow_obj.type,
                    "stages_data": workflow_obj.stages_data if hasattr(workflow_obj, "stages_data") else [],
                }
            workflows_data.append(workflow_data)
        logger.debug(f"[DB Service] Found {len(workflows_data)} workflows of type {workflow_type}.")

    except Exception as e:
        logger.error(f"[DB Service] Error getting workflows by type {workflow_type}: {e}", exc_info=True)
    finally:
        if manage_session_locally and db_session:
            db_session.close()
    return workflows_data

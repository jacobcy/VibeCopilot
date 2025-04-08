#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流运行器

提供运行工作流的功能，使用flow_session管理执行过程
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.db import get_session_factory, init_db
from src.flow_session import FlowSessionManager, StageInstanceManager
from src.workflow.workflow_advanced_operations import save_execution
from src.workflow.workflow_operations import get_workflow, get_workflow_by_id, get_workflow_by_type

logger = logging.getLogger(__name__)


def run_workflow_stage(
    stage_id: str,
    workflow_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    completed_items: Optional[List[str]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run a specific stage of a workflow.

    Args:
        stage_id: The ID of the stage to run
        workflow_id: The ID of the workflow (required if session_id not provided)
        session_id: The ID of an existing session (required if workflow_id not provided)
        context_data: Additional context data to add to the execution context
        completed_items: List of completed items to mark as done

    Returns:
        Tuple containing:
            - Success flag (True/False)
            - Message string
            - Data dictionary with session_id, workflow_id, stage_id, and context
    """
    # Input validation
    if not workflow_id and not session_id:
        error_msg = "Either workflow_id or session_id must be provided"
        logger.error(error_msg)
        return False, error_msg, {}

    # Initialize response data
    response_data = {"session_id": session_id, "workflow_id": workflow_id, "stage_id": stage_id}

    try:
        # Get or initialize execution context
        if session_id:
            logger.info(f"Retrieving execution context for session: {session_id}")
            exec_context = get_workflow_context(session_id)
            if not exec_context:
                error_msg = f"No execution context found for session: {session_id}"
                logger.error(error_msg)
                return False, error_msg, response_data

            workflow_id = exec_context.get("workflow_id")
            response_data["workflow_id"] = workflow_id
        else:
            logger.info(f"Initializing new execution context for workflow: {workflow_id}")
            # Create new execution context with a new session ID
            session_id = str(uuid4())
            exec_context = {"workflow_id": workflow_id, "session_id": session_id, "completed": [], "context": {}, "current_stage": stage_id}
            response_data["session_id"] = session_id

        # Get workflow definition
        workflow = get_workflow_by_id(workflow_id)
        if not workflow:
            error_msg = f"Workflow not found with ID: {workflow_id}"
            logger.error(error_msg)
            return False, error_msg, response_data

        # Validate stage exists in workflow
        stages = workflow.get("stages", [])
        stage_found = False
        for stage in stages:
            if stage.get("id") == stage_id:
                stage_found = True
                break

        if not stage_found:
            error_msg = f"Stage '{stage_id}' not found in workflow: {workflow_id}"
            logger.error(error_msg)
            return False, error_msg, response_data

        # Update context with completed items if provided
        if completed_items:
            if "completed" not in exec_context:
                exec_context["completed"] = []

            for item in completed_items:
                if item not in exec_context["completed"]:
                    exec_context["completed"].append(item)

        # Add additional context data if provided
        if context_data:
            if "context" not in exec_context:
                exec_context["context"] = {}

            exec_context["context"].update(context_data)

        # Update current stage
        exec_context["current_stage"] = stage_id

        # Save execution context
        saved_context = save_execution(exec_context)
        if not saved_context:
            error_msg = "Failed to save execution context"
            logger.error(error_msg)
            return False, error_msg, response_data

        # Include current context in response data
        response_data["context"] = exec_context.get("context", {})
        response_data["completed"] = exec_context.get("completed", [])
        response_data["workflow_name"] = workflow.get("name", "Unknown Workflow")

        return True, f"Successfully prepared stage '{stage_id}' for execution", response_data

    except Exception as e:
        error_msg = f"Error running workflow stage: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg, response_data


def complete_workflow_stage(stage_instance_id: str, output: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    完成工作流阶段

    Args:
        stage_instance_id: 阶段实例ID
        output: 阶段输出数据

    Returns:
        包含完成状态、消息和结果数据的元组
    """
    try:
        # 初始化数据库
        engine = init_db()
        SessionFactory = get_session_factory(engine)

        with SessionFactory() as db_session:
            # 获取阶段实例
            stage_manager = StageInstanceManager(db_session)
            stage_instance = stage_manager.get_instance(stage_instance_id)

            if not stage_instance:
                logger.error(f"找不到阶段实例: {stage_instance_id}")
                return False, f"找不到阶段实例: {stage_instance_id}", None

            # 完成阶段
            stage_manager.complete_instance(stage_instance_id, output)

            return (
                True,
                f"成功完成阶段: {stage_instance.name}",
                {"stage_instance_id": stage_instance_id, "output": output},
            )
    except Exception as e:
        logger.error(f"完成工作流阶段时出错: {str(e)}")
        return False, f"完成工作流阶段时出错: {str(e)}", None


def get_workflow_context(workflow_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取工作流上下文

    Args:
        workflow_id: 工作流ID
        progress_data: 进度数据

    Returns:
        工作流上下文
    """
    # 将导入移到函数内部以避免循环导入
    from src.workflow.interpreter.context_provider import ContextProvider

    context_provider = ContextProvider()
    return context_provider.provide_context_to_agent(workflow_id, progress_data)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流上下文处理模块

提供获取工作流上下文的功能
"""

import argparse
import json  # Import json
import logging
import sys
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from src.cli.commands.flow.handlers.base_handlers import format_stage_summary

# --- Imports for DB access ---
from src.db import get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository

# We need StageInstanceRepository to fetch the specific instance
# Import from correct, separate files
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db.flow_session import StageInstance  # For type hinting

# from src.workflow.workflow_operations import get_workflow_context, view_workflow # Likely deprecated/replaced


# -----------------------------

logger = logging.getLogger(__name__)

# Mapping from stage ID (lowercase) to relevant task statuses
# This should ideally be configurable or part of the workflow definition
STAGE_TO_TASK_STATUS_MAP = {
    "story": ["open", "refinement"],
    "spec": ["open", "in_progress", "reopened"],
    "coding": ["open", "in_progress", "reopened"],
    "test": ["testing", "ready_for_test"],
    "review": ["review", "pending_review"],
    # Add other stage types here
}


def handle_context_subcommand(
    args: Dict[str, Any]  # Accept args dict now
    # workflow_id: str, # These are now in args dict
    # stage_id: str,
    # session_id: Optional[str] = None,
    # completed_items: Optional[List[str]] = None,
    # format_type: str = "text",
    # verbose: bool = False
) -> Dict[str, Any]:  # Return dict consistent with others
    """
    处理获取工作流上下文子命令 (集成实际任务查询)

    Args:
        args: 命令参数字典 (包含 workflow_id, stage_id, session, format, verbose等)

    Returns:
        包含状态、消息和上下文数据的字典
    """
    # Extract arguments from dict
    workflow_id = args.get("workflow_id")
    stage_id = args.get("stage_id")
    session_id = args.get("session")
    # completed_items = args.get("completed") # Possibly deprecated / fetched from instance
    format_type = args.get("format", "text")
    # verbose = args.get("verbose", False) # Use logger instead

    command_meta = {"command": "flow context", "args": args}
    result = {"status": "error", "code": 1, "message": "", "data": None, "meta": command_meta}

    logger.info(f"获取上下文: workflow={workflow_id}, stage={stage_id}, session={session_id}")

    if not workflow_id or not stage_id:
        result["message"] = "必须提供 workflow_id 和 stage_id"
        result["code"] = 400
        return result
    # Session ID is crucial for meaningful context beyond definition
    if not session_id:
        # Return False, "获取阶段实例上下文需要提供 --session ID。", None
        # We might allow fetching definition context if no session provided?
        # For now, require session ID for task integration.
        logger.warning("获取任务相关上下文需要提供 --session ID。仅显示定义信息（如果找到）。")
        # TODO: Implement fetching definition context here if desired
        result["message"] = "获取任务相关上下文需要 --session ID (功能待定)"
        result["code"] = 400  # Or treat as partial success?
        return result

    context = {
        "workflow_id": workflow_id,  # Keep for reference
        "stage_id": stage_id,
        "session_id": session_id,
        "current_stage": stage_id,  # Will be updated if instance found
        # "completed_checks": completed_items or [], # Updated from instance
        "relevant_tasks": [],  # Initialize relevant_tasks
        "stage_instance_data": None,  # To store fetched instance data
        "roadmap_item_id": None,  # To store linked story/epic
    }
    result["data"] = context  # Start populating data

    try:
        session_factory = get_session_factory()
        with session_factory() as db_session:
            stage_repo = StageInstanceRepository(db_session)
            task_repo = TaskRepository(db_session)

            # --- Fetch the specific StageInstance ---
            # Need a method like find_by_session_and_stage_id
            # Assuming such a method exists or can be added:
            # TODO: Implement stage_repo.find_by_session_and_stage_id(session_id, stage_id)
            stage_instance: Optional[StageInstance] = None
            try:
                # Placeholder: Attempt to find the instance.
                # Replace with actual call when method exists.
                if hasattr(stage_repo, "find_by_session_and_stage_id"):
                    stage_instance = stage_repo.find_by_session_and_stage_id(session_id, stage_id)
                else:
                    logger.warning("StageInstanceRepository does not have find_by_session_and_stage_id method yet.")
                    # Fallback: maybe get latest for session?
                    # instances = stage_repo.get_by_session_id(session_id) # Assuming this exists
                    # if instances: stage_instance = instances[-1] # Simplistic fallback

            except Exception as find_e:
                logger.error(f"查找 StageInstance 时出错: {find_e}", exc_info=True)
                # Continue without instance data or return error?
                # Returning error for now
                return result

            if not stage_instance:
                # Attempt to provide context based on definition if instance not found? Risky.
                return result

            context["stage_instance_data"] = stage_instance.to_dict()  # Store instance details
            context["current_stage"] = stage_instance.stage_name  # Update with actual stage name from instance
            context["completed_checks"] = stage_instance.completed_items or []  # Update from instance

            # --- Extract Roadmap Link ---
            # Assuming the link is stored directly on the StageInstance or its parent Session
            # This requires the actual data model structure. Let's assume StageInstance has it.
            # TODO: Verify the actual attribute name for roadmap link on StageInstance/FlowSession model
            roadmap_item_id = getattr(stage_instance, "roadmap_item_id", None)
            if not roadmap_item_id and hasattr(stage_instance, "session") and stage_instance.session:
                # Maybe the link is on the session?
                roadmap_item_id = getattr(stage_instance.session, "roadmap_item_id", None)

            context["roadmap_item_id"] = roadmap_item_id  # Store for reference

            # --- Task Integration Logic ---
            if roadmap_item_id:
                relevant_statuses = STAGE_TO_TASK_STATUS_MAP.get(stage_id.lower(), [])

                if relevant_statuses:
                    try:
                        logger.debug(f"查询与 Story {roadmap_item_id} 关联且状态为 {relevant_statuses} 的任务")
                        relevant_db_tasks = task_repo.search_tasks(roadmap_item_id=roadmap_item_id, status=relevant_statuses)
                        context["relevant_tasks"] = [{"id": task.id, "title": task.title, "status": task.status} for task in relevant_db_tasks]
                        logger.info(f"找到 {len(context['relevant_tasks'])} 个相关任务")
                    except Exception as task_e:
                        logger.error(f"查询关联任务时出错: {task_e}", exc_info=True)
                        context["relevant_tasks_error"] = str(task_e)
                else:
                    logger.info(f"阶段 '{stage_id}' 没有定义相关的任务状态，不查询任务。")
            else:
                logger.info(f"阶段实例 {stage_instance.id} 未关联到 Roadmap Item，不查询任务。")
            # --- End Task Integration ---

        # --- Formatting Logic ---
        message = f"工作流阶段上下文:\n"
        message += f"  Workflow Def ID: {context.get('workflow_id')}\n"  # Maybe get from stage_instance.session.definition_id ?
        message += f"  Session ID: {context.get('session_id', 'N/A')}\n"
        message += f"  Stage: {context.get('current_stage', 'N/A')}\n"
        if context.get("roadmap_item_id"):
            message += f"  关联 Story ID: {context['roadmap_item_id']}\n"

        # Display checklist/completed items from context
        # TODO: Get checklist definition from WorkflowDefinition based on stage_id
        defined_checklist = context.get("stage_instance_data", {}).get("defined_checklist", [])  # Assuming this exists
        if defined_checklist:
            message += f"\n检查清单:\n"
            completed = set(context.get("completed_checks", []))
            for item in defined_checklist:
                mark = "[x]" if item in completed else "[ ]"
                message += f"  {mark} {item}\n"
        else:
            message += f"\n检查清单项: {len(context.get('completed_checks', []))} 项已完成 (无检查清单定义)\n"

        if context.get("relevant_tasks"):
            message += f"\n相关任务 ({len(context['relevant_tasks'])}):\n"
            for task_summary in context["relevant_tasks"]:
                message += f"  - [{task_summary['status']}] {task_summary['title']} (ID: {task_summary['id'][:8]}...)\n"
        elif "relevant_tasks_error" in context:
            message += f"\n[!] 查询相关任务时出错: {context['relevant_tasks_error']}\n"
        elif roadmap_item_id:  # Only mention if we expected to find tasks
            message += f"\n相关任务: 无 (或状态不匹配 '{stage_id}' 阶段)\n"
        else:
            message += f"\n相关任务: (未关联 Story)\n"

        # Return raw context for agent mode, formatted message otherwise
        if format_type == "json":
            # Return the context directly as JSON string in message for now
            result["status"] = "success"
            result["code"] = 0
            result["message"] = message
            result["data"] = context
            return result
        else:
            return result

    except Exception as e:
        logger.exception("获取工作流上下文时出错")
        # Return False, f"获取工作流上下文时出错: {str(e)}", context # Return partial context on error?
        result["message"] = f"获取工作流上下文时出错: {str(e)}"
        result["code"] = 500
        return result

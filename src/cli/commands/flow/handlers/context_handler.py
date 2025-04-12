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
    verbose = args.get("verbose", False)  # 是否显示详细信息

    command_meta = {"command": "flow context", "args": args}
    result = {"status": "error", "code": 1, "message": "", "data": None, "meta": command_meta}

    if verbose:
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
        if verbose:
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
                    if verbose:
                        logger.warning("StageInstanceRepository does not have find_by_session_and_stage_id method yet.")
                    # Fallback: maybe get latest for session?
                    # instances = stage_repo.get_by_session_id(session_id) # Assuming this exists
                    # if instances: stage_instance = instances[-1] # Simplistic fallback

            except Exception as find_e:
                if verbose:
                    logger.error(f"查找 StageInstance 时出错: {find_e}", exc_info=True)
                # Continue without instance data or return error?
                # Returning error for now
                return result

            if not stage_instance:
                # 当工作流被创建但阶段尚未被"执行"时，仍然可以提供阶段的定义信息
                # 注意：我们是工作流解释器，不是执行器。这里不需要实际"执行"阶段，
                # 只需展示阶段定义和上下文信息，帮助用户理解应该做什么。
                if verbose:
                    logger.warning(f"未找到阶段实例记录，将提供阶段定义信息。")

                # 尝试从工作流定义中获取阶段信息
                try:
                    from src.workflow.workflow_operations import get_workflow

                    workflow_def = get_workflow(workflow_id)
                    stage_info = None

                    if workflow_def and "stages" in workflow_def:
                        stages = workflow_def["stages"]
                        # 查找匹配的阶段
                        if isinstance(stages, list):
                            stage_info = next((s for s in stages if s.get("id") == stage_id), None)
                        elif isinstance(stages, dict) and stage_id in stages:
                            stage_info = stages[stage_id]

                    # 成功找到阶段定义信息
                    result["status"] = "success"
                    result["code"] = 200

                    message = f"工作流阶段解释 (基于定义):\n"
                    message += f"  Workflow ID: {workflow_id}\n"
                    message += f"  Session ID: {session_id}\n"
                    message += f"  Stage ID: {stage_id}\n\n"

                    if stage_info:
                        message += f"阶段名称: {stage_info.get('name', 'N/A')}\n"
                        message += f"阶段描述: {stage_info.get('description', 'N/A')}\n\n"

                        # 展示阶段检查清单(如果有)
                        if "checklist" in stage_info and stage_info["checklist"]:
                            message += "阶段检查清单:\n"
                            for item in stage_info["checklist"]:
                                item_name = item if isinstance(item, str) else item.get("name", "未命名项")
                                message += f"  [ ] {item_name}\n"

                        # 展示交付物定义(如果有)
                        if "deliverables" in stage_info and stage_info["deliverables"]:
                            message += "\n预期交付物:\n"
                            for item in stage_info["deliverables"]:
                                item_name = item if isinstance(item, str) else item.get("name", "未命名项")
                                message += f"  - {item_name}\n"
                    else:
                        message += f"注意: 在工作流 '{workflow_id}' 中找不到ID为 '{stage_id}' 的阶段定义。\n"
                        message += f"请检查阶段ID是否正确。\n"

                    message += f"\n提示: 这是阶段的定义信息，不代表任何状态。"
                    message += f"\n\n### 建议操作\n"
                    if stage_info:
                        stage_status = stage_info.get("status", "not_started")
                        if stage_status == "not_started":
                            message += f"\n- 此阶段尚未开始。"
                            message += f"\n      使用 'vc flow create {stage_id}' 开始处理此阶段。"
                        elif stage_status == "in_progress":
                            message += f"\n- 此阶段正在进行中。"
                        elif stage_status == "completed":
                            message += f"\n- 此阶段已完成。"

                    result["message"] = message
                    return result

                except Exception as def_e:
                    if verbose:
                        logger.error(f"获取阶段定义信息失败: {def_e}", exc_info=True)

                # 如果无法获取阶段定义，提供基本信息
                result["status"] = "success"  # 设置为部分成功
                result["code"] = 200

                message = f"工作流阶段解释 (基本信息):\n"
                message += f"  Workflow ID: {workflow_id}\n"
                message += f"  Session ID: {session_id}\n"
                message += f"  Stage ID: {stage_id}\n\n"
                message += f"注意: 未找到此阶段的具体定义或实例记录。\n"
                message += f"可能原因:\n"
                message += f"  - 阶段ID可能不正确\n"
                message += f"  - 工作流定义可能不完整\n\n"
                message += f"建议: 使用 'vc flow show {workflow_id}' 查看完整工作流定义。"

                result["message"] = message
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
                        if verbose:
                            logger.debug(f"查询与 Story {roadmap_item_id} 关联且状态为 {relevant_statuses} 的任务")
                        relevant_db_tasks = task_repo.search_tasks(roadmap_item_id=roadmap_item_id, status=relevant_statuses)
                        context["relevant_tasks"] = [{"id": task.id, "title": task.title, "status": task.status} for task in relevant_db_tasks]
                        if verbose:
                            logger.info(f"找到 {len(context['relevant_tasks'])} 个相关任务")
                    except Exception as task_e:
                        if verbose:
                            logger.error(f"查询关联任务时出错: {task_e}", exc_info=True)
                        context["relevant_tasks_error"] = str(task_e)
                else:
                    if verbose:
                        logger.info(f"阶段 '{stage_id}' 没有定义相关的任务状态，不查询任务。")
            else:
                if verbose:
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
            result["status"] = "success"
            result["code"] = 0
            result["message"] = message
            return result

    except Exception as e:
        if verbose:
            logger.exception("获取工作流上下文时出错")
        # Return False, f"获取工作流上下文时出错: {str(e)}", context # Return partial context on error?
        result["message"] = f"获取工作流上下文时出错: {str(e)}"
        result["code"] = 500
        return result

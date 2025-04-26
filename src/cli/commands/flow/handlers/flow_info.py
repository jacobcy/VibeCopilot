"""
工作流信息处理模块

提供获取工作流上下文和下一阶段建议的功能
"""

import json
import logging
import os
import sys
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 数据库访问
from sqlalchemy.orm import Session  # Keep for type hinting if needed elsewhere

# 导入formatter模块
from src.cli.commands.flow.handlers.formatter import format_stage_summary, format_workflow_summary
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

# Remove get_session_factory, import session_scope
# from src.db import get_session_factory # Removed
from src.db.session_manager import session_scope  # Added

# --- 导入FlowSessionManager功能 ---
from src.flow_session.manager import get_next_stages  # These might need refactoring if they rely on implicit sessions
from src.flow_session.manager import get_session  # Or they should accept db_session as an argument
from src.flow_session.manager import (
    FlowSessionManager,
    get_session_context,
    get_session_first_stage,
    get_session_progress,
    get_session_stages,
    set_current_stage,
)
from src.models.db.flow_session import FlowSession, StageInstance
from src.models.db.stage import Stage
from src.models.db.workflow_definition import WorkflowDefinition

logger = logging.getLogger(__name__)
console = Console()

# Mapping from stage ID (lowercase) to relevant task statuses
# This should ideally be configurable or part of the workflow definition
STAGE_TO_TASK_STATUS_MAP = {
    "story": ["new", "in_progress", "ready_for_review"],
    "spec": ["ready_for_spec", "spec_in_progress", "ready_for_review"],
    "coding": ["ready_for_dev", "in_development", "testing"],
    "test": ["testing", "ready_for_review"],
    "review": ["ready_for_review", "reviewed"],
    "release": ["ready_for_release", "released"],
}


def format_next_stages_text(data: Dict[str, Any], verbose: bool = False) -> str:
    """
    将下一阶段信息格式化为可读文本

    Args:
        data: 下一阶段数据
        verbose: 是否显示详细信息

    Returns:
        格式化的文本
    """
    session_info = data["session"]
    current_stage = data["current_stage"]
    next_stages = data["next_stages"]
    workflow = data["workflow"]

    lines = []

    # 使用format_workflow_summary生成一致的工作流摘要
    if workflow:
        lines.append(format_workflow_summary(workflow))
    else:
        lines.append(f"工作流: {workflow.get('name', '未知')} (ID: {workflow.get('id', '未知')})")

    lines.append(f"会话: {session_info['name']} (ID: {session_info['id']})")

    # 可以使用format_stage_summary生成一致的阶段摘要(如果适用)
    lines.append(f"当前阶段: {current_stage['name']} (ID: {current_stage['id']})")

    if verbose:
        lines.append(f"当前阶段描述: {current_stage['description']}")

    # 添加下一阶段信息
    if not next_stages:
        lines.append("\n没有找到可用的下一阶段。这可能是最后一个阶段，或者没有满足条件的下一阶段。")
    else:
        lines.append(f"\n找到 {len(next_stages)} 个可能的下一阶段:")

        for i, stage in enumerate(next_stages, 1):
            lines.append(f"  {i}. {stage['name']} (ID: {stage['id']})")
            if verbose:
                lines.append(f"     描述: {stage['description']}")
                if stage.get("estimated_time"):
                    lines.append(f"     预计时间: {stage['estimated_time']}")

    # 添加操作建议
    lines.append("\n建议操作:")
    if next_stages:
        suggested_stage = next_stages[0]
        lines.append(f"  推荐进入下一阶段: {suggested_stage['name']}")
        lines.append(f"  执行命令: vc flow create --flow {workflow['id']} --stage {suggested_stage['id']}")  # Assuming vc flow create exists
    else:
        lines.append("  当前工作流没有推荐的下一步操作。可以考虑结束当前会话:")
        lines.append(f"  执行命令: vc flow session complete {session_info['id']}")  # Assuming vc flow session complete exists

    return "\n".join(lines)


# ====== Next Stage 功能 ======


def handle_next_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理获取下一阶段建议子命令

    Args:
        args: 命令参数字典，包含:
            - session_id: 会话ID
            - current: (可选) 当前阶段ID，如果不提供则使用会话当前阶段
            - format: 输出格式 (json/text)
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典，包含:
            - status: 状态 ("success"/"error")
            - code: 状态码
            - message: 结果消息
            - data: 结果数据
    """
    logger.debug(f"获取下一阶段建议: {args}")

    session_id = args.get("session_id")
    if not session_id:
        return {"status": "error", "code": 400, "message": "需要提供会话ID (session_id)", "data": None}

    current_stage_id = args.get("current")
    format_type = args.get("format", "text")
    verbose = args.get("verbose", False)

    try:
        # Use session_scope for automatic session management
        with session_scope() as db_session:
            # Create FlowSessionManager instance
            manager = FlowSessionManager(db_session)

            # 获取会话信息
            flow_session = manager.get_session(session_id)
            if not flow_session:
                # No need to close session, scope handles it
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{session_id}' 的会话", "data": None}

            # 获取工作流定义 (Initialize repo stateless, pass session to methods)
            workflow_repo = WorkflowDefinitionRepository()
            workflow = workflow_repo.get_by_id(db_session, flow_session.workflow_id)
            if not workflow:
                # No need to close session, scope handles it
                return {"status": "error", "code": 404, "message": f"找不到会话对应的工作流定义 (ID: {flow_session.workflow_id})", "data": None}

            # 如果没有提供当前阶段ID，尝试从会话中获取
            if not current_stage_id:
                current_stage_id = flow_session.current_stage_id
                if not current_stage_id:
                    first_stage_id = manager.get_session_first_stage(session_id)
                    if first_stage_id:
                        current_stage_id = first_stage_id
                        # Setting current stage modifies the session, scope will commit
                        success = manager.set_current_stage(session_id, first_stage_id)
                        if success:
                            if verbose:
                                logger.info(f"已将会话 {session_id} 的当前阶段设置为 {current_stage_id}")
                        else:
                            logger.warning(f"设置会话 {session_id} 的当前阶段失败")
                    else:
                        return {"status": "error", "code": 404, "message": f"会话 {session_id} 没有当前阶段，且无法获取工作流的第一个阶段", "data": None}

            # 如果仍然没有当前阶段ID，则返回错误
            if not current_stage_id:
                return {"status": "error", "code": 400, "message": "无法确定当前阶段，请指定 --current 参数", "data": None}

            # 使用FlowSessionManager的get_next_stages方法获取下一阶段
            next_stages = manager.get_next_stages(session_id, current_stage_id)

            # 获取当前阶段信息 (Iterate over workflow stages data)
            current_stage = None
            workflow_stages = workflow.stages_data if hasattr(workflow, "stages_data") else []  # Adapt based on your model

            # 如果 stages_data 是字符串，尝试解析为 JSON
            if isinstance(workflow_stages, str):
                try:
                    workflow_stages = json.loads(workflow_stages)
                except json.JSONDecodeError:
                    logger.error(f"无法解析工作流 {workflow.id} 的阶段数据")
                    workflow_stages = []

            # 处理不同格式的 stages_data
            stages_list = []
            if isinstance(workflow_stages, list):
                stages_list = workflow_stages
            elif isinstance(workflow_stages, dict):
                # 如果是字典，检查是否有 stages 字段
                if "stages" in workflow_stages and isinstance(workflow_stages["stages"], list):
                    stages_list = workflow_stages["stages"]
                else:
                    # 否则假设字典的值就是阶段列表
                    stages_list = list(workflow_stages.values())
            else:
                logger.warning(f"Workflow stages_data is not a list or dict: {type(workflow_stages)}")

            # 在阶段列表中查找当前阶段
            for stage_data in stages_list:
                if isinstance(stage_data, dict) and stage_data.get("id") == current_stage_id:
                    current_stage = stage_data
                    break

            # 如果仍然找不到当前阶段，尝试从 stages 字段中查找
            if not current_stage and hasattr(workflow, "stages") and workflow.stages:
                stages = workflow.stages
                if isinstance(stages, list):
                    for stage in stages:
                        if isinstance(stage, dict) and stage.get("id") == current_stage_id:
                            current_stage = stage
                            break

            # 如果仍然找不到，创建一个基本的阶段信息
            if not current_stage:
                logger.warning(f"在工作流定义中找不到ID为 '{current_stage_id}' 的阶段，创建基本信息")
                current_stage = {"id": current_stage_id, "name": f"阶段 {current_stage_id}", "description": "无描述"}

            # 格式化输出
            result_data = {
                "session": {"id": flow_session.id, "name": flow_session.name, "status": flow_session.status},
                "current_stage": {"id": current_stage.get("id"), "name": current_stage.get("name"), "description": current_stage.get("description")},
                "next_stages": [
                    {
                        "id": stage.get("id"),
                        "name": stage.get("name"),
                        "description": stage.get("description"),
                        "weight": stage.get("weight", 1),
                        "estimated_time": stage.get("estimated_time", "未指定"),
                    }
                    for stage in next_stages  # next_stages should be list of stage dicts/objects
                ],
                "workflow": {"id": workflow.id, "name": workflow.name},
            }

            if format_type == "json":
                message = json.dumps(result_data, ensure_ascii=False, indent=2)
            else:
                message = format_next_stages_text(result_data, verbose)

            # Session scope handles commit/rollback/close automatically
            return {"status": "success", "code": 200, "message": message, "data": result_data}

    except Exception as e:
        # Session scope handles rollback if exception occurred within the 'with'
        logger.error(f"获取下一阶段建议失败", exc_info=True)  # Use logger.error with exc_info
        return {"status": "error", "code": 500, "message": f"获取下一阶段建议失败: {str(e)}", "data": None}


# ====== Context 功能 ======


def handle_context_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理获取工作流上下文子命令 (集成实际任务查询)

    Args:
        args: 命令参数字典 (包含 workflow_id, stage_id, session, format, verbose等)

    Returns:
        包含状态、消息和上下文数据的字典
    """
    logger.debug(f"获取工作流上下文: {args}")
    # Extract arguments from dict
    workflow_id = args.get("workflow_id")
    stage_id = args.get("stage_id")
    session_id = args.get("session")  # Argument name is 'session' in CLI? Verify.
    format_type = args.get("format", "text")
    verbose = args.get("verbose", False)
    output_file = args.get("output")  # Assuming output is an argument

    if not workflow_id and not session_id:
        return {"status": "error", "code": 400, "message": "需要提供工作流ID (--workflow_id) 或会话ID (--session)", "data": None}
    if workflow_id and session_id:
        logger.warning("提供了工作流ID和会话ID，将优先使用会话ID")
        workflow_id = None  # Prioritize session

    context_data = {}
    try:
        # Use session_scope
        with session_scope() as db_session:
            # Create managers/repositories needed (repositories are stateless)
            flow_manager = FlowSessionManager(db_session)
            task_repo = TaskRepository()
            stage_repo = StageRepository()  # Assuming StageRepository exists for definitions
            workflow_repo = WorkflowDefinitionRepository()

            # --- Determine effective workflow_id and stage_id ---
            effective_workflow_id = workflow_id
            effective_stage_id = stage_id
            flow_session = None
            associated_task_id = None

            if session_id:
                flow_session = flow_manager.get_session(session_id)
                if not flow_session:
                    return {"status": "error", "code": 404, "message": f"找不到ID为 '{session_id}' 的会话", "data": None}
                effective_workflow_id = flow_session.workflow_id
                if not stage_id:  # If stage not provided, use session's current stage
                    effective_stage_id = flow_session.current_stage_id
                # Try to get associated task from session context or direct link
                associated_task_id = flow_session.context.get("task_id") or flow_session.task_id

            if not effective_workflow_id:
                return {"status": "error", "code": 400, "message": "无法确定工作流ID", "data": None}
            if not effective_stage_id:
                # If still no stage_id (e.g., workflow provided, no stage given, session has no current)
                # Maybe get the first stage of the workflow? Needs clarification.
                return {"status": "error", "code": 400, "message": "无法确定阶段ID，请提供 --stage_id 或确保会话有当前阶段", "data": None}

            # --- Fetch Core Data ---
            workflow = workflow_repo.get_by_id(db_session, effective_workflow_id)
            if not workflow:
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{effective_workflow_id}' 的工作流定义", "data": None}

            # Fetch stage definition (assuming direct lookup or from workflow data)
            stage_definition = None
            workflow_stages = workflow.stages_data if hasattr(workflow, "stages_data") else None

            # Add robust type checking and parsing for workflow_stages
            if isinstance(workflow_stages, str):
                try:
                    workflow_stages = json.loads(workflow_stages)
                    logger.debug("Parsed workflow_stages from JSON string.")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse workflow stages_data JSON for workflow {effective_workflow_id}")
                    workflow_stages = None  # Reset to None if parsing fails

            stages_to_check = []
            if isinstance(workflow_stages, list):
                # Flatten the list if it contains nested lists of stages
                logger.debug("Workflow stages data is a list. Processing items...")
                for item in workflow_stages:
                    if isinstance(item, dict):
                        stages_to_check.append(item)
                    elif isinstance(item, list):
                        logger.debug("Found nested list within workflow_stages. Processing sub-items...")
                        # If item is a list, extend stages_to_check with dicts from that list
                        for sub_item in item:
                            if isinstance(sub_item, dict):
                                stages_to_check.append(sub_item)
                            else:
                                logger.warning(f"Skipping non-dict item within nested list: {type(sub_item)}")
                    else:
                        logger.warning(f"Skipping non-list/non-dict item in workflow_stages: {type(item)}")
            elif isinstance(workflow_stages, dict):
                # If it's a dictionary, assume values are the stages (list or dict)
                logger.debug("Workflow stages data is a dictionary. Processing values...")
                for value in workflow_stages.values():
                    if isinstance(value, dict):
                        stages_to_check.append(value)
                    elif isinstance(value, list):
                        logger.debug("Found list within workflow_stages dict value. Processing sub-items...")
                        for sub_item in value:
                            if isinstance(sub_item, dict):
                                stages_to_check.append(sub_item)
                            else:
                                logger.warning(f"Skipping non-dict item within nested list (from dict value): {type(sub_item)}")
                    else:
                        logger.warning(f"Skipping non-list/non-dict value in workflow_stages dict: {type(value)}")
            elif workflow_stages is not None:
                logger.warning(
                    f"Workflow stages data for {effective_workflow_id} is not a list or dict after potential parsing. Type: {type(workflow_stages)}"
                )

            # Now iterate through the flattened list of potential stage dictionaries
            logger.debug(f"Prepared stages to check: {stages_to_check}")
            for stage_data in stages_to_check:
                # Check if stage_data is actually a dictionary before accessing .get()
                if isinstance(stage_data, dict) and stage_data.get("id") == effective_stage_id:
                    stage_definition = stage_data
                    logger.info(f"Found stage definition for '{effective_stage_id}'.")  # Use info for success
                    break

            # Fallback logic
            if not stage_definition:
                logger.warning(f"Stage definition for '{effective_stage_id}' not found in stages_data. Trying fallback.")
                # Try StageRepository as fallback if stages not embedded
                stage_obj = stage_repo.get_by_id(db_session, effective_stage_id)
                if stage_obj:
                    stage_definition = stage_obj.to_dict()  # Assuming to_dict exists
                else:
                    return {
                        "status": "error",
                        "code": 404,
                        "message": f"在工作流 '{effective_workflow_id}' 中找不到阶段定义 '{effective_stage_id}'",
                        "data": None,
                    }

            # --- Fetch Associated Task Info ---
            task = None
            if associated_task_id:
                task = task_repo.get_by_id(db_session, associated_task_id)

            # --- Fetch Session Context & Progress (if applicable) ---
            session_context = {}
            session_progress = {}
            if flow_session:
                session_context = flow_manager.get_session_context(session_id)
                session_progress = flow_manager.get_session_progress(session_id)

            # --- Build context_data dictionary ---
            context_data = {
                "workflow": workflow.to_dict() if hasattr(workflow, "to_dict") else {"id": workflow.id, "name": workflow.name},
                "stage_details": stage_definition,
                "session_info": flow_session.to_dict() if flow_session else None,
                "session_context": session_context,
                "session_progress": session_progress,
                "associated_task": task.to_dict() if task else None,
                # Add other relevant data like recent comments, related files, etc.
                "related_tasks": [],  # Placeholder for future enhancement
                "recent_comments": [],  # Placeholder for future enhancement
            }

            # --- Format message based on format_type ---
            if format_type == "json":
                message = json.dumps(context_data, ensure_ascii=False, indent=2)
            else:
                message = format_context_text(context_data, stage_definition, verbose)  # Pass stage_definition

            # --- Handle output file ---
            if output_file:
                try:
                    output_dir = os.path.dirname(output_file)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    with open(output_file, "w", encoding="utf-8") as f:
                        # Write the formatted message (text or JSON)
                        f.write(message)
                    # Update message to indicate file save
                    output_message = f"上下文信息已保存到: {output_file}"
                    # Return success with file path info, keep original data
                    return {"status": "success", "code": 200, "message": output_message, "data": context_data}
                except Exception as write_e:
                    logger.error(f"写入上下文文件失败 {output_file}: {write_e}", exc_info=True)
                    # Fallback to returning message directly, but add warning
                    message += f"\\n\\n[bold yellow]警告:[/bold yellow] 无法写入输出文件 {output_file}: {write_e}"
                    # Continue to return the message directly

            # Session scope handles commit/rollback/close
            return {"status": "success", "code": 200, "message": message, "data": context_data}

    except Exception as e:
        # Session scope handles rollback
        logger.error(f"获取工作流上下文失败: {e}", exc_info=True)
        return {"status": "error", "code": 500, "message": f"获取上下文失败: {str(e)}", "data": None}


def format_context_text(context: Dict[str, Any], stage_details: Dict[str, Any], verbose: bool = False) -> str:
    """
    将上下文信息格式化为可读文本

    Args:
        context: 上下文数据字典 (可能包含嵌套结构)
        stage_details: 阶段详情字典 (从 context['stage_details'] 提取)
        verbose: 是否显示详细信息

    Returns:
        格式化的文本
    """
    # Extract nested info with fallbacks
    workflow_info = context.get("workflow", {})
    session_info = context.get("session_info", {})
    # stage_details is passed separately, but we can also get it from context if needed
    # stage_details = context.get('stage_details', {})

    message = f"工作流阶段上下文:\n"
    # Access nested dictionaries for names and IDs
    message += f"  Workflow: {workflow_info.get('name', '未知')} (ID: {workflow_info.get('id', 'N/A')})\n"
    message += f"  会话: {session_info.get('name', '未知')} (ID: {session_info.get('id', 'N/A')})\n"
    # Use the passed stage_details dictionary
    message += f"  阶段: {stage_details.get('name', '未知')} (ID: {stage_details.get('id', 'N/A')})\n"

    if context.get("roadmap_item_id"):  # Keep this check as is
        message += f"  关联 Story ID: {context['roadmap_item_id']}\n"

    # 显示阶段描述 (using passed stage_details)
    if stage_details.get("description"):
        message += f"\n阶段说明:\n  {stage_details['description']}\n"

    # 显示检查清单 (accessing context directly for these keys)
    completed_checks = set(context.get("completed_checks", []))  # Assume these are top-level
    defined_checklist = context.get("defined_checklist", [])  # Assume these are top-level
    if defined_checklist:
        message += f"\n检查清单:\n"
        for item in defined_checklist:
            mark = "[x]" if item in completed_checks else "[ ]"
            message += f"  {mark} {item}\n"
    elif completed_checks:
        message += f"\n检查清单项: {len(completed_checks)} 项已完成 (无检查清单定义)\n"
    else:
        message += f"\n检查清单: 无\n"  # Clearer message

    # 显示相关任务 (accessing context directly for these keys)
    relevant_tasks = context.get("relevant_tasks")  # Assume top-level
    if relevant_tasks:
        message += f"\n相关任务 ({len(relevant_tasks)}):\n"
        for task_summary in relevant_tasks:
            if isinstance(task_summary, dict):
                message += (
                    f"  - [{task_summary.get('status', 'N/A')}] {task_summary.get('title', '未知标题')} (ID: {task_summary.get('id', 'N/A')[:8]}...)\n"
                )
            else:
                message += f"  - 无效的任务条目: {task_summary}\n"
    elif "relevant_tasks_error" in context:
        message += f"\n[!] 查询相关任务时出错: {context['relevant_tasks_error']}\n"
    elif context.get("associated_task"):  # Check if associated_task exists
        task_info = context["associated_task"]
        message += f"\n关联任务: [{task_info.get('status', 'N/A')}] {task_info.get('title', '未知标题')} (ID: {task_info.get('id', 'N/A')})\n"
    elif context.get("roadmap_item_id"):
        message += f"\n相关任务: 无 (或状态不匹配 '{stage_details.get('id', 'N/A')}' 阶段)\n"
    else:
        message += f"\n相关任务: (未关联 Story 或 Task)\n"

    return message

"""
工作流信息处理模块

提供获取工作流上下文和下一阶段建议的功能
"""

import json
import logging
import sys
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 数据库访问
from sqlalchemy.orm import Session

# 导入formatter模块
from src.cli.commands.flow.handlers.formatter import format_stage_summary, format_workflow_summary
from src.db import get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

# --- 导入FlowSessionManager功能 ---
from src.flow_session.manager import (
    FlowSessionManager,
    get_next_stages,
    get_session,
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
        # 创建数据库会话
        db_session = get_session_factory()()

        try:
            # 创建FlowSessionManager实例
            manager = FlowSessionManager(db_session)

            # 获取会话信息
            flow_session = manager.get_session(session_id)
            if not flow_session:
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{session_id}' 的会话", "data": None}

            # 获取工作流定义
            workflow_repo = WorkflowDefinitionRepository(db_session)
            workflow = workflow_repo.get_by_id(flow_session.workflow_id)
            if not workflow:
                return {"status": "error", "code": 404, "message": f"找不到会话对应的工作流定义 (ID: {flow_session.workflow_id})", "data": None}

            # 如果没有提供当前阶段ID，尝试从会话中获取
            if not current_stage_id:
                # 优先从会话的current_stage_id获取
                current_stage_id = flow_session.current_stage_id

                # 如果会话没有当前阶段，尝试获取第一个阶段
                if not current_stage_id:
                    first_stage_id = manager.get_session_first_stage(session_id)
                    if first_stage_id:
                        current_stage_id = first_stage_id
                        # 设置为当前阶段
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

            # 获取当前阶段信息
            current_stage = None
            for stage in workflow.stages:
                if stage.get("id") == current_stage_id:
                    current_stage = stage
                    break

            if not current_stage:
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{current_stage_id}' 的阶段定义", "data": None}

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
                    for stage in next_stages
                ],
                "workflow": {"id": workflow.id, "name": workflow.name},
            }

            if format_type == "json":
                message = json.dumps(result_data, ensure_ascii=False, indent=2)
            else:
                message = format_next_stages_text(result_data, verbose)

            return {"status": "success", "code": 200, "message": message, "data": result_data}

        finally:
            db_session.close()

    except Exception as e:
        logger.exception(f"获取下一阶段建议失败")
        return {"status": "error", "code": 500, "message": f"获取下一阶段建议失败: {str(e)}", "data": None}


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
        lines.append(f"  执行命令: vc flow create --flow {workflow['id']} --stage {suggested_stage['id']}")
    else:
        lines.append("  当前工作流没有推荐的下一步操作。可以考虑结束当前会话:")
        lines.append(f"  执行命令: vc flow session complete {session_info['id']}")

    return "\n".join(lines)


# ====== Context 功能 ======


def handle_context_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理获取工作流上下文子命令 (集成实际任务查询)

    Args:
        args: 命令参数字典 (包含 workflow_id, stage_id, session, format, verbose等)

    Returns:
        包含状态、消息和上下文数据的字典
    """
    # Extract arguments from dict
    workflow_id = args.get("workflow_id")
    stage_id = args.get("stage_id") or args.get("stage")
    session_id = args.get("session")
    format_type = args.get("format", "text")
    verbose = args.get("verbose", False)  # 是否显示详细信息

    command_meta = {"command": "flow context", "args": args}
    result = {"status": "error", "code": 1, "message": "", "data": None, "meta": command_meta}

    if verbose:
        logger.info(f"获取上下文: workflow={workflow_id}, stage={stage_id}, session={session_id}")

    # Session ID is crucial for meaningful context beyond definition
    if not session_id:
        if verbose:
            logger.warning("获取任务相关上下文需要提供 --session ID。仅显示定义信息（如果找到）。")
        result["message"] = "获取任务相关上下文需要 --session ID (功能待定)"
        result["code"] = 400
        return result

    # 创建FlowSessionManager实例
    db_session = get_session_factory()()
    try:
        # 创建工作流会话管理器
        manager = FlowSessionManager(db_session)

        # 1. 获取会话信息
        flow_session = manager.get_session(session_id)
        if not flow_session:
            result["message"] = f"找不到会话: {session_id}"
            result["code"] = 404
            return result

        # 2. 验证工作流定义存在
        workflow_def_repo = WorkflowDefinitionRepository(db_session)
        workflow_def = workflow_def_repo.get_by_id(flow_session.workflow_id)
        if not workflow_def:
            error_msg = (
                f"错误: 会话 {session_id} 引用了不存在的工作流定义 (ID: {flow_session.workflow_id})。\n"
                "这可能是因为:\n"
                "1. 工作流定义已被删除\n"
                "2. 创建会话时使用了错误的工作流ID或名称\n\n"
                f"建议: 使用 'vc flow session delete {session_id}' 删除此错误会话，然后使用正确的工作流ID创建新会话"
            )
            result["message"] = error_msg
            result["code"] = 404
            return result

        # 2. 确定阶段ID
        # 如果没有提供stage_id，尝试从会话获取当前阶段
        if not stage_id:
            # 优先从会话的current_stage_id获取
            if flow_session.current_stage_id:
                stage_id = flow_session.current_stage_id
                if verbose:
                    logger.info(f"使用会话当前阶段: {stage_id}")
            else:
                # 尝试获取会话的第一个阶段
                if verbose:
                    logger.info(f"会话 {session_id} 没有当前阶段，尝试获取并设置第一个阶段")

                # 3. 获取工作流定义
                workflow_def_repo = WorkflowDefinitionRepository(db_session)
                workflow_def = workflow_def_repo.get_by_id(flow_session.workflow_id)
                if not workflow_def:
                    result["message"] = f"找不到工作流定义: {flow_session.workflow_id}"
                    result["code"] = 404
                    return result

                # 直接从工作流定义中获取第一个阶段
                if workflow_def.stages and len(workflow_def.stages) > 0:
                    first_stage_id = workflow_def.stages[0].get("id")
                    if first_stage_id:
                        if verbose:
                            logger.info(f"找到工作流 {workflow_def.id} 的第一个阶段: {first_stage_id}")

                        # 先检查是否已存在阶段实例
                        stage_repo = StageInstanceRepository(db_session)
                        existing_instance = stage_repo.get_by_session_and_stage(flow_session.id, first_stage_id)

                        if not existing_instance:
                            # 创建阶段实例
                            try:
                                from src.flow_session.stage.manager import StageInstanceManager

                                stage_manager = StageInstanceManager(db_session)
                                stage_data = {"stage_id": first_stage_id, "name": workflow_def.stages[0].get("name", f"阶段-{first_stage_id}")}
                                stage_manager.create_instance(flow_session.id, stage_data)
                                if verbose:
                                    logger.info(f"为会话 {session_id} 创建了第一个阶段实例")
                            except Exception as e:
                                logger.error(f"创建阶段实例失败: {str(e)}")

                        # 设置为当前阶段
                        stage_id = first_stage_id
                        success = manager.set_current_stage(session_id, first_stage_id)
                        if success:
                            if verbose:
                                logger.info(f"已将会话 {session_id} 的当前阶段设置为 {stage_id}")
                        else:
                            logger.warning(f"设置会话 {session_id} 的当前阶段失败")
                    else:
                        result["message"] = f"工作流 {workflow_def.id} 的第一个阶段没有ID"
                        result["code"] = 500
                        return result
                else:
                    result["message"] = f"工作流定义 {flow_session.workflow_id} 没有定义阶段"
                    result["code"] = 400
                    return result

        # 再次确认是否有阶段ID
        if not stage_id:
            result["message"] = f"会话 {session_id} 没有当前阶段，且无法获取或创建工作流的第一个阶段"
            result["code"] = 404
            return result

        # 3. 获取工作流定义（如果上面没有获取）
        if not locals().get("workflow_def"):
            workflow_def_repo = WorkflowDefinitionRepository(db_session)
            workflow_def = workflow_def_repo.get_by_id(flow_session.workflow_id)
            if not workflow_def:
                result["message"] = f"找不到工作流定义: {flow_session.workflow_id}"
                result["code"] = 404
                return result

        # 4. 确定阶段定义
        stage_details = None
        if workflow_def.stages:
            # 从阶段列表中查找匹配的阶段
            for stage in workflow_def.stages:
                if stage.get("id") == stage_id:
                    stage_details = stage
                    break

        if not stage_details:
            result["message"] = f"找不到阶段定义: {stage_id}"
            result["code"] = 404
            return result

        # 5. 构建上下文数据
        # 获取会话上下文
        session_context = manager.get_session_context(session_id)

        # 合并检查列表
        defined_checklist = stage_details.get("checklist", [])
        completed_checks = session_context.get("completed_checks", [])

        # 如果args中有completed参数，添加到已完成检查项
        if args.get("completed"):
            new_completed = list(completed_checks)
            for item in args.get("completed"):
                if item not in new_completed:
                    new_completed.append(item)
            completed_checks = new_completed

            # 更新会话上下文中的已完成检查项
            manager.update_session_context(session_id, {"completed_checks": completed_checks})
            if verbose:
                logger.info(f"已更新会话 {session_id} 的已完成检查项")

        # 添加相关任务信息 (这里可以集成task相关功能)
        relevant_tasks = []
        try:
            # 从task系统获取相关任务
            task_repo = TaskRepository(db_session)
            relevant_task_statuses = STAGE_TO_TASK_STATUS_MAP.get(stage_id.lower(), [])
            if relevant_task_statuses:
                roadmap_item_id = session_context.get("roadmap_item_id")
                if roadmap_item_id:
                    tasks = task_repo.get_by_roadmap_item_and_status(roadmap_item_id, relevant_task_statuses)
                    relevant_tasks = [{"id": task.id, "title": task.title, "status": task.status} for task in tasks]
                    if verbose:
                        logger.info(f"找到 {len(relevant_tasks)} 个相关任务")
        except Exception as e:
            logger.warning(f"获取相关任务失败: {str(e)}")

        # 构建完整上下文
        context = {
            "workflow_id": flow_session.workflow_id,
            "workflow_name": workflow_def.name,
            "session_id": flow_session.id,
            "session_name": flow_session.name,
            "stage_id": stage_id,
            "stage_name": stage_details.get("name", stage_id),
            "stage_description": stage_details.get("description", ""),
            "completed_checks": completed_checks,
            "defined_checklist": defined_checklist,
            "relevant_tasks": relevant_tasks,
            "roadmap_item_id": session_context.get("roadmap_item_id"),
        }

        # 6. 格式化返回结果
        if format_type == "json":
            # 返回JSON格式
            result["status"] = "success"
            result["code"] = 0
            result["data"] = context
            result["message"] = json.dumps(context, indent=2)
        else:
            # 返回文本格式
            result["status"] = "success"
            result["code"] = 0
            result["data"] = context
            result["message"] = format_context_text(context, stage_details, verbose)

        return result
    except Exception as e:
        logger.exception(f"获取工作流上下文失败: {str(e)}")
        result["message"] = f"获取工作流上下文时出错: {str(e)}"
        return result
    finally:
        db_session.close()


def format_context_text(context: Dict[str, Any], stage_details: Dict[str, Any], verbose: bool = False) -> str:
    """
    将上下文信息格式化为可读文本

    Args:
        context: 上下文数据
        stage_details: 阶段详情
        verbose: 是否显示详细信息

    Returns:
        格式化的文本
    """
    message = f"工作流阶段上下文:\n"
    message += f"  Workflow: {context.get('workflow_name', '未知')} (ID: {context.get('workflow_id', 'N/A')})\n"
    message += f"  会话: {context.get('session_name', '未知')} (ID: {context.get('session_id', 'N/A')})\n"
    message += f"  阶段: {context.get('stage_name', '未知')} (ID: {context.get('stage_id', 'N/A')})\n"

    if context.get("roadmap_item_id"):
        message += f"  关联 Story ID: {context['roadmap_item_id']}\n"

    # 显示阶段描述
    if stage_details.get("description"):
        message += f"\n阶段说明:\n  {stage_details['description']}\n"

    # 显示检查清单
    completed_checks = set(context.get("completed_checks", []))
    defined_checklist = context.get("defined_checklist", [])
    if defined_checklist:
        message += f"\n检查清单:\n"
        for item in defined_checklist:
            mark = "[x]" if item in completed_checks else "[ ]"
            message += f"  {mark} {item}\n"
    else:
        message += f"\n检查清单项: {len(completed_checks)} 项已完成 (无检查清单定义)\n"

    # 显示相关任务
    if context.get("relevant_tasks"):
        message += f"\n相关任务 ({len(context['relevant_tasks'])}):\n"
        for task_summary in context["relevant_tasks"]:
            message += f"  - [{task_summary['status']}] {task_summary['title']} (ID: {task_summary['id'][:8]}...)\n"
    elif "relevant_tasks_error" in context:
        message += f"\n[!] 查询相关任务时出错: {context['relevant_tasks_error']}\n"
    elif context.get("roadmap_item_id"):
        message += f"\n相关任务: 无 (或状态不匹配 '{context.get('stage_id')}' 阶段)\n"
    else:
        message += f"\n相关任务: (未关联 Story)\n"

    return message

"""
Flow 'run' 子命令处理器

提供工作流创建和解释的功能，负责处理工作流会话的创建和阶段解释。
作为解释器，不执行实际业务流程，而是提供上下文和指导。
"""
import logging
from typing import Any, Dict, List, Optional

from src.flow_session import FlowSessionManager

# Assuming workflow_runner is accessible
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage
from src.workflow.workflow_operations import get_workflow_by_id, get_workflow_by_name

logger = logging.getLogger(__name__)


def get_current_session_id() -> Optional[str]:
    """获取当前活跃会话ID

    查询数据库中标记为活跃状态的会话，返回最近创建的一个会话ID。
    这是解释器的元数据查询，不涉及业务流程执行。

    Returns:
        当前活跃会话ID或None（如果没有活跃会话）
    """
    try:
        # 获取数据库会话
        from src.db import get_session_factory

        session_factory = get_session_factory()
        db_session = session_factory()

        # 正确初始化会话管理器
        from src.flow_session.session.manager import FlowSessionManager

        session_manager = FlowSessionManager(db_session)

        # 获取活跃会话
        active_sessions = session_manager.list_sessions(status="active")

        if active_sessions and len(active_sessions) > 0:
            # 返回最近创建/使用的会话
            return active_sessions[0].id
        return None
    except Exception as e:
        logger.error(f"获取当前会话时出错: {str(e)}")
        return None


def get_current_stage_id(session_id: str) -> Optional[str]:
    """获取会话当前阶段ID

    查询特定会话的当前阶段ID。作为解释器，这只是元数据查询，
    不会执行或触发实际的阶段业务流程。

    Args:
        session_id: 会话ID

    Returns:
        当前阶段ID或None（如果会话没有当前阶段）
    """
    try:
        # 获取数据库会话
        from src.db import get_session_factory

        session_factory = get_session_factory()
        db_session = session_factory()

        # 正确初始化会话管理器
        from src.flow_session.session.manager import FlowSessionManager

        session_manager = FlowSessionManager(db_session)

        # 获取会话
        session = session_manager.get_session(session_id)

        if session:
            return session.current_stage_id
        return None
    except Exception as e:
        logger.error(f"获取当前阶段时出错: {str(e)}")
        return None


def handle_run_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理工作流解释请求

    作为工作流解释器，此函数负责创建会话或解释特定阶段，但不执行实际业务流程。
    解释器只处理元数据和状态，提供工作流阶段的定义和上下文，供用户了解应该做什么，
    但不会触发实际业务逻辑的执行。

    支持两种主要模式：
    1. 提供session_id参数时，继续解释该会话中的工作流阶段
    2. 提供workflow参数时，创建新的工作流会话并解释特定阶段

    Args:
        args: 命令参数

    Returns:
        命令结果字典，包含状态、消息和会话数据
    """
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow create", "args": args},
    }

    try:
        # 获取参数
        workflow_name = args.get("workflow")  # 工作流名称，用于创建新会话
        stage_id = args.get("stage")  # 阶段ID，可选
        instance_name = args.get("name")  # 会话名称
        session_id = args.get("session")  # 会话ID
        checklist_items = args.get("checklist", [])  # 已完成的检查项
        context_data = args.get("context_data", {})  # 上下文数据
        verbose = args.get("verbose", False)  # 显示详细信息

        # 解析workflow参数，支持"workflow:stage"格式
        workflow_stage = None
        if workflow_name and ":" in workflow_name:
            parts = workflow_name.split(":", 1)
            workflow_name = parts[0]
            workflow_stage = parts[1]

        # 确定最终阶段值（优先使用workflow:stage中的stage部分）
        final_stage = workflow_stage if workflow_stage else stage_id

        # 明确判断用户意图
        is_creating_new_workflow = workflow_name is not None
        is_continuing_session = session_id is not None

        if verbose:
            if is_creating_new_workflow:
                logger.info(f"即将创建新工作流会话，使用工作流: {workflow_name}")
            elif is_continuing_session:
                logger.info(f"即将解释会话: {session_id}, 阶段: {final_stage or '(当前阶段)'}")
            else:
                logger.info("即将解释当前活跃会话")

        # 根据参数确定操作模式
        if is_creating_new_workflow:
            # 创建新工作流会话模式
            workflow = None

            # 判断是否符合8位UID格式
            is_likely_uid = len(workflow_name) == 8 and workflow_name.isalnum()

            # 如果看起来像UID，先尝试通过ID查找，否则先尝试通过名称查找
            if is_likely_uid:
                workflow = get_workflow_by_id(workflow_name)
                if not workflow:
                    workflow = get_workflow_by_name(workflow_name)
            else:
                workflow = get_workflow_by_name(workflow_name)
                if not workflow:
                    workflow = get_workflow_by_id(workflow_name)

            if not workflow:
                result["message"] = f"找不到工作流: {workflow_name}"
                result["code"] = 404
                return result

            # 如果未指定阶段，使用第一个阶段
            if not final_stage and workflow.get("stages"):
                final_stage = workflow["stages"][0]["id"]
                if verbose:
                    logger.info(f"未指定阶段，默认解释第一个阶段: {final_stage}")

            # 确保有阶段ID
            if not final_stage:
                result["message"] = "无法确定要解释的阶段，工作流可能没有定义阶段"
                result["code"] = 400
                return result

            # 使用workflow_name作为workflow_id创建新会话
            workflow_id = workflow.get("id", workflow_name)
            if verbose:
                logger.info(f"使用工作流ID: {workflow_id} (来自名称: {workflow_name})")

        elif is_continuing_session:
            # 明确指定会话ID，继续该会话
            workflow_id = None  # 从会话获取workflow_id

            # 如果未指定阶段，获取当前阶段
            if not final_stage:
                final_stage = get_current_stage_id(session_id)
                if not final_stage:
                    if verbose:
                        logger.warning(f"会话 {session_id} 没有当前阶段，需要手动指定阶段ID")
                    result["message"] = f"会话 {session_id} 没有当前阶段。请使用 --stage 参数指定要解释的阶段。"
                    result["code"] = 400
                    return result

            if verbose:
                logger.info(f"将解释指定会话: {session_id}, 阶段: {final_stage}")

        else:
            # 没有指定workflow也没有指定session_id，尝试继续当前活跃会话
            session_id = get_current_session_id()

            if not session_id:
                # 给出清晰的提示信息
                result["status"] = "success"  # 这不是错误，只是信息性提示
                result["code"] = 0
                result[
                    "message"
                ] = "当前没有活跃的会话。\n\n您可以：\n- 使用 --workflow 参数创建新工作流会话，例如：flow run --workflow dev\n- 使用 --session 参数指定要解释的现有会话ID\n- 使用 flow session list 查看所有会话"
                return result

            if verbose:
                logger.info(f"将解释当前活跃会话: {session_id}")

            # 如果未指定阶段，获取当前阶段
            if not final_stage:
                final_stage = get_current_stage_id(session_id)
                if not final_stage and verbose:
                    logger.warning(f"会话 {session_id} 没有当前阶段，可能需要手动指定阶段ID")

            workflow_id = None  # 从会话获取workflow_id

        # 解释工作流阶段（注意：不是执行业务流程，而是提供定义和上下文）
        success, message, data = run_workflow_stage(
            stage_id=final_stage,
            workflow_id=workflow_id,
            session_id=session_id,
            context_data=context_data,
            completed_items=checklist_items,
            instance_name=instance_name,
        )

        if success:
            result["status"] = "success"
            result["code"] = 0
            result["message"] = message
            result["data"] = data
        else:
            result["message"] = message  # Error message from runner
            # Try to determine appropriate error code (e.g., 404 if not found, 500 for internal)
            result["code"] = data.get("error_code", 500) if isinstance(data, dict) else 500
            result["data"] = data  # Include any error details from runner

        return result

    except Exception as e:
        logger.error(f"解释工作流时出错: {str(e)}")
        if args.get("verbose"):
            logger.exception(e)
        result["message"] = f"解释工作流时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result

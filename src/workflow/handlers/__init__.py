#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流处理器模块

提供工作流命令处理功能
"""

from typing import Any, Dict, List, Optional

from src.flow_session import FlowSessionManager
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage
from src.workflow.workflow_operations import get_workflow_by_id


def get_current_session_id() -> Optional[str]:
    """获取当前活跃会话ID"""
    try:
        # 这里应该实现根据项目具体存储方式获取当前活跃会话
        # 简化示例：获取最近创建的活跃会话
        session_manager = FlowSessionManager()
        active_sessions = session_manager.get_active_sessions()

        if active_sessions and len(active_sessions) > 0:
            # 返回最近创建/使用的会话
            return active_sessions[0].id
        return None
    except Exception as e:
        return None


def get_current_stage_id(session_id: str) -> Optional[str]:
    """获取会话当前阶段ID"""
    try:
        session_manager = FlowSessionManager()
        session = session_manager.get_session(session_id)

        if session:
            return session.current_stage_id
        return None
    except Exception as e:
        return None


def handle_run_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理运行命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    # 构造结果对象
    result = {"success": False, "error": "", "message": "", "data": None}

    try:
        # 获取参数
        stage = args.get("stage")  # 阶段ID，可选
        workflow = args.get("workflow")  # 新工作流参数
        session = args.get("session")  # 会话ID，用于继续现有会话
        name = args.get("name")  # 会话名称，用于创建新会话
        checklist = args.get("checklist", [])  # 已完成的检查项

        # 解析workflow参数，支持"workflow:stage"格式
        workflow_name = workflow
        workflow_stage = None

        if workflow:
            if ":" in workflow:
                parts = workflow.split(":", 1)
                workflow_name = parts[0]
                workflow_stage = parts[1]

        # 确定最终阶段值（优先使用workflow:stage中的stage部分）
        final_stage = workflow_stage if workflow_stage else stage

        # 操作模式判断
        if workflow_name:
            # 创建新工作流会话模式
            workflow_obj = get_workflow_by_id(workflow_name)
            if not workflow_obj:
                result["error"] = f"找不到工作流: {workflow_name}"
                return result

            # 如果未指定阶段，使用第一个阶段
            if not final_stage and workflow_obj.get("stages"):
                final_stage = workflow_obj["stages"][0]["id"]

            # 确保有阶段ID
            if not final_stage:
                result["error"] = "无法确定要运行的阶段，工作流可能没有定义阶段"
                return result

            # 使用workflow_name作为workflow_id创建新会话
            workflow_id = workflow_name
            session_id = None

        else:
            # 继续现有会话模式
            if not session:
                # 获取当前正在进行的会话
                session_id = get_current_session_id()
            else:
                session_id = session

            if not session_id:
                # 这不是错误，只是信息提示
                result["success"] = True
                result[
                    "message"
                ] = "当前没有活跃的会话。\n\n您可以：\n- 使用 --workflow 参数创建新工作流，例如：flow run --workflow dev\n- 使用 --session 参数指定现有会话ID\n- 使用 flow session list 查看所有会话"
                return result

            # 如果未指定阶段，获取当前阶段
            if not final_stage:
                final_stage = get_current_stage_id(session_id)
                if not final_stage:
                    result["error"] = "未指定阶段且无法确定当前阶段，请指定要运行的阶段"
                    return result

            # 从会话获取workflow_id
            workflow_id = None

        # 运行工作流阶段
        success, message, data = run_workflow_stage(
            stage_id=final_stage,
            workflow_id=workflow_id,
            session_id=session_id,
            context_data={},
            completed_items=checklist,
            instance_name=name,
        )

        if success:
            result["success"] = True
            result["message"] = message
            result["data"] = data
        else:
            result["error"] = message

        return result

    except Exception as e:
        result["error"] = f"运行工作流时出错: {str(e)}"
        return result

"""
会话状态管理相关处理函数
"""

import json
from typing import Optional

import click

from src.flow_session.core.utils import echo_error, echo_info, echo_success, echo_warning, format_time, get_db_session, get_error_code
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.status.integration import FlowStatusIntegration


def handle_pause_session(session_id: str, verbose: bool = False, agent_mode: bool = False):
    """处理暂停会话的逻辑

    Args:
        session_id: 会话ID
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {"success": False, "error_code": None, "error_message": None, "session": None}

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)
            flow_session = manager.pause_session(session_id)

            if not flow_session:
                error_code = get_error_code("SESSION_NOT_FOUND")
                error_message = f"找不到ID为 {session_id} 的会话"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查会话ID是否正确")

                return result_data

            # 同步到状态系统
            integration = FlowStatusIntegration(session)
            integration.sync_session_to_status(session_id)

            # 构建会话数据
            session_data = {
                "id": flow_session.id,
                "name": flow_session.name,
                "status": flow_session.status,
                "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
            }

            if verbose:
                # 添加更多详细信息
                session_data.update(
                    {
                        "workflow_id": flow_session.workflow_id,
                        "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                        "current_stage_id": flow_session.current_stage_id,
                    }
                )

            result_data["session"] = session_data
            result_data["success"] = True

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            echo_success(f"已暂停会话: {flow_session.id} ({flow_session.name})")
            echo_info(f"可使用 'vc flow session resume {flow_session.id}' 恢复此会话")

            return result_data

    except Exception as e:
        error_code = get_error_code("PAUSE_SESSION_ERROR")
        error_message = f"暂停会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和会话ID")

        return result_data


def handle_resume_session(session_id: str, verbose: bool = False, agent_mode: bool = False):
    """处理恢复会话的逻辑

    Args:
        session_id: 会话ID
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {"success": False, "error_code": None, "error_message": None, "session": None}

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)
            flow_session = manager.resume_session(session_id)

            if not flow_session:
                error_code = get_error_code("SESSION_NOT_FOUND")
                error_message = f"找不到ID为 {session_id} 的会话"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查会话ID是否正确")

                return result_data

            # 同步到状态系统
            integration = FlowStatusIntegration(session)
            integration.sync_session_to_status(session_id)

            # 构建会话数据
            session_data = {
                "id": flow_session.id,
                "name": flow_session.name,
                "status": flow_session.status,
                "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
                "current_stage_id": flow_session.current_stage_id,
            }

            if verbose:
                # 添加更多详细信息
                session_data.update(
                    {
                        "workflow_id": flow_session.workflow_id,
                        "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                        "context": flow_session.context,
                    }
                )

            result_data["session"] = session_data
            result_data["success"] = True

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            echo_success(f"已恢复会话: {flow_session.id} ({flow_session.name})")

            # 显示当前阶段
            if flow_session.current_stage_id:
                echo_info(f"当前阶段: {flow_session.current_stage_id}")
            else:
                echo_info("会话尚未开始任何阶段")

            return result_data

    except Exception as e:
        error_code = get_error_code("RESUME_SESSION_ERROR")
        error_message = f"恢复会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和会话ID")

        return result_data


def handle_close_session(session_id: str, reason: Optional[str] = None, force: bool = False, verbose: bool = False, agent_mode: bool = False):
    """处理结束会话的逻辑

    Args:
        session_id: 会话ID
        reason: 结束原因
        force: 是否强制结束
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {"success": False, "error_code": None, "error_message": None, "session": None}

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)

            # 如果不是强制模式且没有提供agent模式，询问用户确认
            if not force and not agent_mode:
                if not click.confirm(f"确定要结束会话 {session_id} 吗?", default=False):
                    echo_info("操作已取消")
                    return {"success": False, "error_code": "USER_CANCELLED"}

            flow_session = manager.complete_session(session_id)

            if not flow_session:
                error_code = get_error_code("SESSION_NOT_FOUND")
                error_message = f"找不到ID为 {session_id} 的会话"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查会话ID是否正确")

                return result_data

            # 同步到状态系统
            integration = FlowStatusIntegration(session)
            integration.sync_session_to_status(session_id)

            # 构建会话数据
            session_data = {
                "id": flow_session.id,
                "name": flow_session.name,
                "status": flow_session.status,
                "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
            }

            if verbose:
                # 添加更多详细信息
                session_data.update(
                    {
                        "workflow_id": flow_session.workflow_id,
                        "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                        "current_stage_id": flow_session.current_stage_id,
                        "closed_reason": reason,
                    }
                )

            result_data["session"] = session_data
            result_data["success"] = True

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            echo_success(f"已结束会话: {flow_session.id} ({flow_session.name})")
            if reason:
                echo_info(f"结束原因: {reason}")

            return result_data

    except Exception as e:
        error_code = get_error_code("CLOSE_SESSION_ERROR")
        error_message = f"结束会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和会话ID")

        return result_data

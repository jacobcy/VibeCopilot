"""
会话删除相关处理函数
"""

import json
from typing import Optional

import click

from src.flow_session.core.utils import confirm_action, echo_error, echo_info, echo_success, echo_warning, format_time, get_db_session, get_error_code
from src.flow_session.session.manager import FlowSessionManager


def handle_delete_session(session_id: str, force: bool = False, verbose: bool = False, agent_mode: bool = False):
    """处理删除会话的逻辑

    Args:
        session_id: 会话ID
        force: 是否强制删除
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {
        "success": False,
        "error_code": None,
        "error_message": None,
        "deleted": False,
        "session_id": session_id,
    }

    try:
        if not force and not agent_mode:
            confirm = confirm_action(f"确定要删除ID为 {session_id} 的会话吗？此操作不可撤销。")
            if not confirm:
                echo_info("操作已取消")
                result_data.update(
                    {
                        "error_code": get_error_code("OPERATION_CANCELED"),
                        "error_message": "操作已取消",
                        "success": False,
                    }
                )
                return result_data

        with get_db_session() as session:
            manager = FlowSessionManager(session)
            success = manager.delete_session(session_id)

            if not success:
                error_code = get_error_code("SESSION_NOT_FOUND")
                error_message = f"找不到ID为 {session_id} 的会话"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查会话ID是否正确")

                return result_data

            result_data.update({"success": True, "deleted": True, "session_id": session_id})

            if verbose:
                result_data["timestamp"] = format_time(None, iso_format=True)

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            echo_success(f"已删除会话: {session_id}")

            return result_data

    except Exception as e:
        error_code = get_error_code("DELETE_SESSION_ERROR")
        error_message = f"删除会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和会话ID")

        return result_data

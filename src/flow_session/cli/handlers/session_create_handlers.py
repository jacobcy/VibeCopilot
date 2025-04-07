"""
会话创建相关处理函数
"""

import json
from typing import Optional

import click

from src.flow_session.cli.utils import (
    echo_error,
    echo_info,
    echo_success,
    get_db_session,
    get_error_code,
)
from src.flow_session.session_manager import FlowSessionManager
from src.flow_session.status_integration import FlowStatusIntegration


def handle_create_session(
    workflow_id: str, name: Optional[str] = None, verbose: bool = False, agent_mode: bool = False
):
    """处理创建新会话的逻辑

    Args:
        workflow_id: 工作流ID
        name: 会话名称
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {"success": False, "error_code": None, "error_message": None, "session": None}

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)

            try:
                flow_session = manager.create_session(workflow_id, name)

                # 同步到状态系统
                integration = FlowStatusIntegration(session)
                integration.create_status_for_session(flow_session.id)

                # 构建会话数据
                session_data = {
                    "id": flow_session.id,
                    "name": flow_session.name,
                    "workflow_id": flow_session.workflow_id,
                    "status": flow_session.status,
                    "created_at": flow_session.created_at.isoformat()
                    if flow_session.created_at
                    else None,
                }

                if verbose:
                    # 添加更多详细信息
                    session_data.update(
                        {
                            "context": flow_session.context,
                            "updated_at": flow_session.updated_at.isoformat()
                            if flow_session.updated_at
                            else None,
                        }
                    )

                result_data["session"] = session_data
                result_data["success"] = True

                if agent_mode:
                    # 在agent模式下，直接打印JSON结果
                    click.echo(json.dumps(result_data, indent=2))
                    return result_data

                echo_success(f"已创建会话: {flow_session.id} ({flow_session.name})")
                echo_info(f"可使用 'vc flow session show {flow_session.id}' 查看详情")

                return result_data

            except ValueError as e:
                error_code = get_error_code("CREATE_SESSION_ERROR")
                error_message = f"创建会话失败: {str(e)}"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查工作流ID是否存在")

                return result_data

    except Exception as e:
        error_code = get_error_code("CREATE_SESSION_ERROR")
        error_message = f"创建会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和输入参数")

        return result_data

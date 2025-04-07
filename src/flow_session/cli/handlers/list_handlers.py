"""
会话列表相关处理函数
"""

import json
from typing import Any, Dict, Optional

import click
from tabulate import tabulate

from src.flow_session.cli.utils import (
    echo_error,
    echo_info,
    echo_success,
    format_time,
    get_db_session,
    get_error_code,
    output_json,
)
from src.flow_session.session_manager import FlowSessionManager


def handle_list_sessions(
    status: Optional[str] = None,
    workflow: Optional[str] = None,
    format: str = "text",
    verbose: bool = False,
    agent_mode: bool = False,
):
    """处理列出所有活动会话的逻辑

    Args:
        status: 会话状态
        workflow: 工作流ID
        format: 输出格式
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {
        "success": False,
        "error_code": None,
        "error_message": None,
        "sessions": [],
        "count": 0,
    }

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)
            sessions = manager.list_sessions(status=status, workflow_id=workflow)

            sessions_data = []
            for s in sessions:
                session_info = {
                    "id": s.id,
                    "workflow_id": s.workflow_id,
                    "name": s.name,
                    "status": s.status,
                    "current_stage": s.current_stage_id,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }

                if verbose:
                    # 添加更多详细信息
                    session_info.update(
                        {
                            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                            "completed_stages": s.completed_stages,
                            "context": s.context,
                        }
                    )

                sessions_data.append(session_info)

            result_data["sessions"] = sessions_data
            result_data["count"] = len(sessions_data)
            result_data["success"] = True

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            if format == "json":
                # 在JSON格式下，优雅地打印结果
                output_json(result_data)
                return result_data

            # 默认表格文本输出
            if not sessions:
                echo_success("未找到工作流会话")
                return result_data

            # 准备表格数据
            table_data = []
            for s in sessions:
                workflow_id = s.workflow_id
                created_at = format_time(s.created_at)

                table_data.append(
                    [s.id, workflow_id, s.name, s.status, s.current_stage_id or "无", created_at]
                )

            # 打印表格
            headers = ["ID", "工作流", "名称", "状态", "当前阶段", "创建时间"]
            echo_info("\n✅ 工作流会话:")
            echo_info(tabulate(table_data, headers=headers, tablefmt="simple"))
            echo_info(f"\n总计: {len(sessions)}个会话\n")
            echo_info("提示: 使用 'vc flow session show <ID>' 查看详情")
            echo_info("      使用 'vc flow session resume <ID>' 恢复暂停的会话")

            return result_data

    except Exception as e:
        error_code = get_error_code("LIST_SESSIONS_ERROR")
        error_message = f"列出会话时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        elif format == "json":
            output_json(result_data)
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接是否正常")

        return result_data

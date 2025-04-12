"""
会话详情相关处理函数
"""

import json
from typing import Optional

import click

from src.flow_session.core.utils import echo_error, echo_info, echo_success, format_progress, format_time, get_db_session, get_error_code, output_json
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager


def handle_show_session(session_id: str, format: str = "text", verbose: bool = False, agent_mode: bool = False):
    """处理显示会话详情的逻辑

    Args:
        session_id: 会话ID
        format: 输出格式
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式
    """
    result_data = {"success": False, "error_code": None, "error_message": None, "session": None}

    try:
        with get_db_session() as session:
            manager = FlowSessionManager(session)
            flow_session = manager.get_session(session_id)

            if not flow_session:
                error_code = get_error_code("SESSION_NOT_FOUND")
                error_message = f"找不到ID为 {session_id} 的会话"
                result_data.update({"error_code": error_code, "error_message": error_message})

                if agent_mode:
                    click.echo(json.dumps(result_data, indent=2))
                elif format == "json":
                    output_json(result_data)
                else:
                    echo_error(error_message)
                    echo_info("提示: 请检查会话ID是否正确")

                return result_data

            # 获取进度信息
            progress_info = manager.get_session_progress(session_id)

            # 构建会话数据
            session_data = {
                "id": flow_session.id,
                "name": flow_session.name,
                "workflow_id": flow_session.workflow_id,
                "status": flow_session.status,
                "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
                "current_stage_id": flow_session.current_stage_id,
                "progress": progress_info,
            }

            if verbose:
                # 添加更多详细信息
                session_data.update(
                    {
                        "context": flow_session.context,
                        "completed_stages": flow_session.completed_stages,
                    }
                )

            result_data["session"] = session_data
            result_data["success"] = True

            if agent_mode:
                # 在agent模式下，直接打印JSON结果
                click.echo(json.dumps(result_data, indent=2))
                return result_data

            if format == "json":
                # 在JSON格式下，优雅地打印结果
                output_json(result_data)
                return result_data

            # 默认文本输出
            echo_info(f"\n📋 工作流会话: {flow_session.id} ({flow_session.name})\n")

            echo_info("基本信息:")
            echo_info(f"- 工作流: {flow_session.workflow_id}")
            echo_info(f"- 状态: {flow_session.status}")
            created_at = format_time(flow_session.created_at)
            updated_at = format_time(flow_session.updated_at)
            echo_info(f"- 创建时间: {created_at}")
            echo_info(f"- 最后更新: {updated_at}")

            # 显示阶段进度
            echo_info("\n阶段进度:")

            # 已完成阶段
            for stage in progress_info.get("completed_stages", []):
                completed_at = stage.get("completed_at", "未知")
                if completed_at and completed_at != "未知":
                    # 简化时间格式
                    completed_at = completed_at.split("T")[0] + " " + completed_at.split("T")[1][:5]
                echo_info(f"✅ {stage['name']} - 已完成 ({completed_at})")

            # 当前阶段
            current_stage = progress_info.get("current_stage")
            if current_stage:
                echo_info(f"▶️ {current_stage['name']} - 进行中")

                # 如果有当前阶段的详细信息
                if "completed_items" in current_stage:
                    stage_manager = StageInstanceManager(session)
                    stage_instances = manager.get_session_stages(session_id)
                    current_instance = next((s for s in stage_instances if s.stage_id == current_stage["id"]), None)

                    if current_instance:
                        instance_progress = stage_manager.get_instance_progress(current_instance.id)
                        items = instance_progress.get("items", [])
                        total = len(items)
                        completed = sum(1 for item in items if item["status"] == "COMPLETED")

                        if total > 0:
                            echo_info(f"- 名称: {current_stage['name']}")
                            started_at = format_time(current_instance.started_at)
                            echo_info(f"- 开始时间: {started_at}")
                            echo_info(f"- 已完成项: {completed}/{total} ({format_progress(completed, total)})")

                            # 列出所有项目及其状态
                            for item in items:
                                status_symbol = "✅" if item["status"] == "COMPLETED" else "⏳"
                                echo_info(f"  {status_symbol} {item['name']}")

            # 待进行阶段
            for stage in progress_info.get("pending_stages", []):
                echo_info(f"⏳ {stage['name']} - 待进行")

            # 显示可执行的操作
            echo_info("\n操作:")
            echo_info(f"- 查看会话上下文: vc flow context --session {session_id}")
            echo_info(f"- 获取下一步建议: vc flow next --session {session_id}")
            echo_info(f"- 设为当前会话: vc flow session switch {session_id}")
            echo_info(f"- 继续执行该会话: vc flow create --session {session_id} [stage_id]")

            return result_data

    except Exception as e:
        error_code = get_error_code("SHOW_SESSION_ERROR")
        error_message = f"显示会话详情时发生错误: {str(e)}"
        result_data.update({"error_code": error_code, "error_message": error_message})

        if agent_mode:
            click.echo(json.dumps(result_data, indent=2))
        elif format == "json":
            output_json(result_data)
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接和会话ID")

        return result_data

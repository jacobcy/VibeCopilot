"""
工作流会话列表处理模块

提供工作流会话列表的获取和格式化功能。
"""

import json
import logging
import sys
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from src.flow_session.core.session_utils import format_session_list
from src.flow_session.core.utils import echo_error, echo_info, echo_success, format_time, get_db_session, get_error_code, output_json
from src.flow_session.manager import FlowSessionManager

# Get module-level logger
logger = logging.getLogger(__name__)  # Use standard logger


def handle_list_sessions(
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    format: str = "yaml",
    verbose: bool = False,
    agent_mode: bool = False,
) -> Dict[str, Any]:
    """
    处理列出所有会话的逻辑

    Args:
        status: 状态过滤器
        workflow_id: 工作流ID过滤器
        format: 输出格式 (yaml, text, json)
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式

    Returns:
        Result dictionary
    """
    result = {"success": False, "sessions": [], "message": "", "error": ""}

    # Use the standard session scope from db.session_manager
    from src.db.session_manager import session_scope

    try:
        with session_scope() as session:  # Use session_scope
            # Use the module-level logger defined above
            # logger_factory = LoggerFactory.get_instance() # Removed
            # manager = FlowSessionManager(session, logger_param=logger_factory.get_logger("default")) # Removed
            manager = FlowSessionManager(session, logger_param=logger)  # Pass the standard logger
            sessions = manager.list_sessions(status=status, workflow_id=workflow_id)

            # Remove verbose print statements, rely on logger levels
            # if verbose: print(f"[调试] 从manager获取到 {len(sessions)} 个会话")
            logger.debug(f"Retrieved {len(sessions)} sessions from manager.")

            # If no sessions found...
            if not sessions:
                # if verbose: print("[调试] 没有找到会话")
                logger.debug("No sessions found.")
                result["success"] = True
                result["message"] = "当前没有工作流会话"
                if not agent_mode:
                    console = Console()
                    console.print("\n[yellow]当前没有工作流会话。[/yellow]\n")
                    console.print("您可以使用 [cyan]vibecopilot flow session create <工作流ID>[/cyan] 创建新会话。\n")
                return result

            # Convert sessions to dicts
            # if verbose: print("[调试] 开始转换会话对象到字典")
            logger.debug("Formatting session list...")
            session_dicts = format_session_list(sessions, verbose)
            logger.debug(f"Formatted {len(session_dicts)} session dicts.")

            # Update results
            result["success"] = True
            result["sessions"] = session_dicts
            result["message"] = f"找到 {len(sessions)} 个会话"

            # Output results
            if not agent_mode:
                if format == "yaml":
                    # if verbose: print("[调试] 使用YAML格式输出会话列表")
                    logger.debug("Outputting session list as YAML.")
                    # 默认使用YAML格式输出
                    if verbose:
                        print("[调试] 使用YAML格式输出会话列表")
                    print("\n会话列表:\n")

                    # 在非verbose模式下只显示基本信息
                    if not verbose:
                        simple_sessions = []
                        for session in session_dicts:
                            simple_sessions.append(
                                {
                                    "id": session.get("id", "-"),
                                    "name": session.get("name", "-") or "-",
                                    "task_id": session.get("task_id", "-") or "-",
                                    "task_title": session.get("task_title", "-") or "-",
                                    "workflow_id": session.get("workflow_id", "-"),
                                    "current_stage_id": session.get("current_stage_id", "-") or "-",
                                }
                            )
                        print(yaml.dump(simple_sessions, sort_keys=False, default_flow_style=False, allow_unicode=True))
                    else:
                        # verbose模式下显示所有信息
                        print(yaml.dump(session_dicts, sort_keys=False, default_flow_style=False, allow_unicode=True))

                    print(f"\n找到 {len(sessions)} 个会话。\n")
                elif format == "text":
                    # 使用新的格式化函数
                    try:
                        from src.cli.commands.flow.handlers.formatter import format_session_list as formatter_format_session_list

                        formatted_output = formatter_format_session_list(session_dicts, verbose)
                        print(f"\n{formatted_output}\n")
                    except ImportError:
                        # 降级回原来的表格模式
                        if verbose:
                            print("[调试] 无法导入格式化器，使用表格模式")

                        # 以下是原来的表格模式代码
                        console = Console()
                        table = Table(show_header=True)

                        # 添加列 - 简化版本
                        if not verbose:
                            table.add_column("ID", style="cyan")
                            table.add_column("名称", style="green")
                            table.add_column("关联任务", style="magenta")
                            table.add_column("工作流", style="blue")
                            table.add_column("当前阶段", style="red")
                        else:
                            # verbose模式下显示更多列
                            table.add_column("ID", style="cyan")
                            table.add_column("名称", style="green")
                            table.add_column("任务ID", style="magenta")
                            table.add_column("任务标题", style="magenta")
                            table.add_column("工作流", style="blue")
                            table.add_column("状态", style="yellow")
                            table.add_column("当前阶段", style="red")
                            table.add_column("创建时间", style="magenta")
                            table.add_column("更新时间", style="magenta")
                            table.add_column("完成清单", style="green")

                        # 添加行
                        for i, session in enumerate(session_dicts):
                            if verbose:
                                print(f"[调试] 添加会话 {i+1} 到表格: ID={session.get('id', '-')}")

                            if not verbose:
                                # 简化版行
                                task_info = f"{session.get('task_title', '-')}"
                                if session.get("task_id"):
                                    task_info = f"{session.get('task_title', '-')} ({session.get('task_id', '-')})"

                                table.add_row(
                                    session.get("id", "-"),
                                    session.get("name", "-") or "-",
                                    task_info,
                                    session.get("workflow_id", "-"),
                                    session.get("current_stage_id", "-") or "-",
                                )
                            else:
                                # verbose模式行
                                completed_stages = ", ".join(str(s) for s in session.get("completed_stages", []))
                                table.add_row(
                                    session.get("id", "-"),
                                    session.get("name", "-") or "-",
                                    session.get("task_id", "-") or "-",
                                    session.get("task_title", "-") or "-",
                                    session.get("workflow_id", "-"),
                                    session.get("status", "-"),
                                    session.get("current_stage_id", "-") or "-",
                                    session.get("created_at", "-"),
                                    session.get("updated_at", "-"),
                                    completed_stages or "-",
                                )

                        # 打印表格
                        if verbose:
                            print("[调试] 打印表格")
                        console.print("\n")
                        console.print(table)
                        console.print(f"\n找到 {len(sessions)} 个会话。\n")
                elif format == "json":
                    # if verbose: print("[调试] 使用JSON格式输出会话列表")
                    logger.debug("Outputting session list as JSON.")
                    # JSON格式输出
                    output_json(result)  # Keep direct output for JSON

            return result

    except Exception as e:
        # if verbose: print(f"[调试] 处理会话列表时出错: {str(e)}") # Remove print
        logger.error(f"处理会话列表时出错: {e}", exc_info=True)  # Use logger
        result["success"] = False
        result["error"] = str(e)
        result["message"] = "获取会话列表失败"
        # echo_error might be redundant if logger handles console output
        # Consider standardizing error output via logger or a dedicated console util
        echo_error(f"获取会话列表失败: {str(e)}")
        return result

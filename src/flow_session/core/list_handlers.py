"""
会话列表相关处理函数
"""

import json
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from src.flow_session.core.utils import echo_error, echo_info, echo_success, format_time, get_db_session, get_error_code, output_json
from src.flow_session.session.manager import FlowSessionManager


def handle_list_sessions(
    status: Optional[str] = None,
    workflow: Optional[str] = None,
    format: str = "yaml",
    verbose: bool = False,
    agent_mode: bool = False,
) -> Dict[str, Any]:
    """
    处理列出所有会话的逻辑

    Args:
        status: 状态过滤器
        workflow: 工作流ID过滤器
        format: 输出格式 (yaml, text, json)
        verbose: 是否显示详细信息
        agent_mode: 是否为程序处理模式

    Returns:
        Result dictionary
    """
    result = {"success": False, "sessions": [], "message": "", "error": ""}

    # 初始化数据库
    try:
        with get_db_session() as session:
            # 只在verbose模式下打印调试信息
            if verbose:
                print("[调试] 开始获取会话列表")

            manager = FlowSessionManager(session)
            sessions = manager.list_sessions(status=status, workflow_id=workflow)

            if verbose:
                print(f"[调试] 从manager获取到 {len(sessions)} 个会话")

            # 如果没有会话，则返回成功但显示无会话消息
            if not sessions:
                if verbose:
                    print("[调试] 没有找到会话")

                result["success"] = True
                result["message"] = "当前没有工作流会话"

                if format == "text" and not agent_mode:
                    console = Console()
                    console.print("\n当前没有工作流会话。\n")
                    console.print("您可以使用 [cyan]vibecopilot flow session create <工作流ID>[/cyan] 创建新会话。\n")
                return result

            # 将会话转换为字典列表
            session_dicts = []
            if verbose:
                print("[调试] 开始转换会话对象到字典")

            for i, s in enumerate(sessions):
                if verbose:
                    print(f"[调试] 处理会话 {i+1}: 类型={type(s)}")

                # 安全地将会话对象转换为字典
                try:
                    if isinstance(s, dict):
                        if verbose:
                            print(f"[调试] 会话 {i+1} 已经是字典")
                        session_dict = s
                    else:
                        if verbose:
                            print(f"[调试] 会话 {i+1} 是对象，ID={getattr(s, 'id', 'unknown')}")

                        # 确保对象有to_dict方法
                        if hasattr(s, "to_dict") and callable(getattr(s, "to_dict")):
                            if verbose:
                                print(f"[调试] 使用to_dict方法转换会话 {i+1}")
                            session_dict = s.to_dict()
                        else:
                            if verbose:
                                print(f"[调试] 手动转换会话 {i+1}的属性")
                            # 如果没有to_dict方法，手动创建字典
                            session_dict = {
                                "id": getattr(s, "id", None),
                                "name": getattr(s, "name", None),
                                "workflow_id": getattr(s, "workflow_id", None),
                                "status": getattr(s, "status", None),
                                "current_stage_id": getattr(s, "current_stage_id", None),
                                "created_at": format_time(getattr(s, "created_at", None)),
                                "updated_at": format_time(getattr(s, "updated_at", None)),
                                "completed_stages": getattr(s, "completed_stages", []),
                                "context": getattr(s, "context", {}),
                            }

                    if verbose:
                        print(f"[调试] 会话 {i+1} 转换结果: ID={session_dict.get('id', 'unknown')}")

                    # 添加详细信息如果需要
                    if verbose and not isinstance(s, dict):
                        # 可能的额外详细字段
                        pass

                    session_dicts.append(session_dict)
                except Exception as conversion_error:
                    # 记录转换错误但继续处理其他会话
                    if verbose:
                        print(f"[调试] 转换会话 {i+1} 时出错: {str(conversion_error)}")
                    echo_error(f"转换会话对象时出错: {str(conversion_error)}")
                    continue

            # 更新结果
            if verbose:
                print(f"[调试] 成功转换 {len(session_dicts)} 个会话字典")

            result["success"] = True
            result["sessions"] = session_dicts
            result["message"] = f"找到 {len(sessions)} 个会话"

            # 输出结果
            if not agent_mode:
                if format == "yaml":
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
                    # 只有明确要求text时才使用表格
                    if verbose:
                        print("[调试] 开始构建表格")

                    console = Console()
                    table = Table(show_header=True)

                    # 添加列 - 简化版本
                    if not verbose:
                        table.add_column("ID", style="cyan")
                        table.add_column("名称", style="green")
                        table.add_column("工作流", style="blue")
                        table.add_column("当前阶段", style="red")
                    else:
                        # verbose模式下显示更多列
                        table.add_column("ID", style="cyan")
                        table.add_column("名称", style="green")
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
                            row = [
                                session.get("id", "-"),
                                session.get("name", "-") or "-",
                                session.get("workflow_id", "-"),
                                session.get("current_stage_id", "-") or "-",
                            ]
                        else:
                            # verbose模式行
                            row = [
                                session.get("id", "-"),
                                session.get("name", "-") or "-",
                                session.get("workflow_id", "-"),
                                session.get("status", "-"),
                                session.get("current_stage_id", "-") or "-",
                                session.get("created_at", "-"),
                                session.get("updated_at", "-"),
                                ", ".join(session.get("completed_stages", [])) if session.get("completed_stages") else "-",
                            ]

                        table.add_row(*row)

                    if verbose:
                        print("[调试] 打印表格")

                    console.print("\n会话列表:\n")
                    console.print(table)
                    console.print(f"\n找到 {len(sessions)} 个会话。\n")

                    if verbose:
                        print("[调试] 表格已打印完成")
                elif format == "json":
                    # JSON格式输出
                    output_json(result)
            elif agent_mode:
                # Agent模式输出
                click.echo(json.dumps(result, indent=2))

            return result

    except Exception as e:
        error_code = get_error_code("LIST_SESSIONS_ERROR")
        error_message = f"列出会话时发生错误: {str(e)}"
        result["error"] = error_message

        if agent_mode:
            click.echo(json.dumps(result, indent=2))
        elif format == "json":
            output_json(result)
        else:
            echo_error(error_message)
            echo_info("提示: 请检查数据库连接是否正常")
            echo_success("操作完成")  # 更改消息，避免误导

        return result

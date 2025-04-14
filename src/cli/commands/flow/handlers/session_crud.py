#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流会话命令处理函数

提供工作流会话命令的处理函数
"""

import logging
from typing import Any, Dict, Optional, Tuple, Union

from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session as SQLAlchemySession

from src.db import init_db
from src.flow_session.core import handle_list_sessions, handle_show_session
from src.flow_session.manager import FlowSessionManager

logger = logging.getLogger(__name__)
console = Console()


def handle_session_command(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理session子命令，直接调用flow_session的CLI函数

    Args:
        args: 命令行参数，可以是字典或argparse.Namespace对象

    Returns:
        包含状态、消息和数据的元组
    """
    # 将字典转换为类似Namespace的对象以支持getattr
    if isinstance(args, dict):

        class DictWrapper:
            def __init__(self, data):
                self.__data = data

            def __getattr__(self, name):
                return self.__data.get(name)

        args_obj = DictWrapper(args)
    else:
        args_obj = args

    # 检查是否没有提供action子命令
    if not hasattr(args_obj, "subcommand") and not hasattr(args_obj, "action"):
        # 创建一个更友好的错误提示
        console.print("\n[bold red]错误:[/bold red] 请指定一个会话操作\n")

        # 创建表格展示可用操作
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        table.add_row("list", "列出所有工作流会话")
        table.add_row("show", "查看指定会话的详细信息")
        table.add_row("switch", "切换当前活动会话")
        table.add_row("update", "更新会话属性")
        table.add_row("close", "结束指定的工作流会话")
        table.add_row("delete", "删除指定的工作流会话")
        table.add_row("create", "创建新的工作流会话")

        console.print("可用的会话操作:")
        console.print(table)
        console.print("\n使用 [cyan]vibecopilot flow session <操作> --help[/cyan] 获取具体操作的帮助信息")

        return False, "请指定一个会话操作", None

    # 获取action
    action = getattr(args_obj, "subcommand", None) or getattr(args_obj, "action", None)

    try:
        # 获取数据库会话
        engine = init_db()
        db_session = SQLAlchemySession(engine)

        try:
            # 根据操作调用相应的函数
            if action == "list":
                status = getattr(args_obj, "status", None)
                workflow = getattr(args_obj, "workflow", None)
                format_type = getattr(args_obj, "format", "yaml")  # 默认格式改为yaml
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 直接执行list_sessions，其会自行处理输出
                result = handle_list_sessions(status, workflow, format_type, verbose, agent_mode)
                return True, "", result  # 空消息，表示已输出

            elif action == "show":
                id_or_name = getattr(args_obj, "id_or_name", None)
                if not id_or_name:
                    return False, "❌ show操作需要会话ID或名称参数", None

                format_type = getattr(args_obj, "format", "yaml")  # 默认格式改为yaml
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 转换id_or_name到session_id
                flow_session_manager = FlowSessionManager(db_session)
                session = flow_session_manager.get_session(id_or_name)
                if not session:
                    return False, f"❌ 找不到ID或名称为 '{id_or_name}' 的会话", None
                session_id = session.id

                result = handle_show_session(session_id, format_type, verbose, agent_mode)
                return True, "", result  # 空消息，表示已输出

            elif action == "switch":
                id_or_name = getattr(args_obj, "id_or_name", None)
                if not id_or_name:
                    return False, "❌ switch操作需要会话ID或名称参数", None

                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 直接在这里处理switch操作
                flow_session_manager = FlowSessionManager(db_session)
                try:
                    session = flow_session_manager.switch_session(id_or_name)
                    db_session.commit()
                    return True, "", {"session": session.to_dict()}
                except ValueError as e:
                    return False, f"❌ {str(e)}", None
                except Exception as e:
                    logger.exception(f"切换会话失败: {str(e)}")
                    return False, f"❌ 切换会话失败: {str(e)}", None

            elif action == "update":
                id_or_name = getattr(args_obj, "id_or_name", None)
                if not id_or_name:
                    return False, "❌ update操作需要会话ID或名称参数", None

                name = getattr(args_obj, "name", None)
                status = getattr(args_obj, "status", None)
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 处理更新操作
                flow_session_manager = FlowSessionManager(db_session)
                try:
                    data = {}
                    if name:
                        data["name"] = name

                    if status:
                        data["status"] = status

                    # 至少需要一个要更新的属性
                    if not data:
                        return False, "❌ 请指定至少一个要更新的属性 (例如: --name 或 --status)", None

                    session = flow_session_manager.update_session(id_or_name, data)
                    db_session.commit()
                    return True, f"会话 {id_or_name} 已更新", {"session": session.to_dict()}
                except ValueError as e:
                    return False, f"❌ {str(e)}", None
                except Exception as e:
                    logger.exception(f"更新会话失败: {str(e)}")
                    return False, f"❌ 更新会话失败: {str(e)}", None

            elif action == "close":
                id_or_name = getattr(args_obj, "id_or_name", None)
                if not id_or_name:
                    return False, "❌ close操作需要会话ID或名称参数", None

                reason = getattr(args_obj, "reason", None)
                force = getattr(args_obj, "force", False)
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 处理结束会话操作
                flow_session_manager = FlowSessionManager(db_session)
                try:
                    closed_session = flow_session_manager.close_session(id_or_name, reason)
                    db_session.commit()
                    return True, "", {"session": closed_session.to_dict()}
                except ValueError as e:
                    return False, f"❌ {str(e)}", None
                except Exception as e:
                    logger.exception(f"结束会话失败: {str(e)}")
                    return False, f"❌ 结束会话失败: {str(e)}", None

            elif action == "delete":
                id_or_name = getattr(args_obj, "id_or_name", None)
                if not id_or_name:
                    return False, "❌ delete操作需要会话ID或名称参数", None

                force = getattr(args_obj, "force", False)
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 直接执行删除操作
                flow_session_manager = FlowSessionManager(db_session)
                try:
                    success = flow_session_manager.delete_session(id_or_name)
                    db_session.commit()
                    if success:
                        return True, "", None
                    else:
                        return False, f"❌ 删除会话 {id_or_name} 失败", None
                except ValueError as e:
                    return False, f"❌ {str(e)}", None
                except Exception as e:
                    logger.exception(f"删除会话失败: {str(e)}")
                    return False, f"❌ 删除会话失败: {str(e)}", None

            elif action == "create":
                workflow_id = getattr(args_obj, "workflow_id", None)
                if not workflow_id:
                    return False, "❌ create操作需要工作流ID参数", None

                name = getattr(args_obj, "name", None)
                task_id = getattr(args_obj, "task_id", None)
                verbose = getattr(args_obj, "verbose", False)
                agent_mode = getattr(args_obj, "agent_mode", False)

                # 处理创建会话操作
                flow_session_manager = FlowSessionManager(db_session)
                try:
                    # 创建会话，支持任务ID参数
                    session = flow_session_manager.create_session(workflow_id=workflow_id, name=name, task_id=task_id)
                    db_session.commit()
                    return True, "", {"session": session.to_dict()}
                except ValueError as e:
                    return False, f"❌ {str(e)}", None
                except Exception as e:
                    logger.exception(f"创建会话失败: {str(e)}")
                    return False, f"❌ 创建会话失败: {str(e)}", None

            else:
                return False, f"❌ 未知的会话操作: {action}", None

        finally:
            # 无论如何都要关闭会话
            db_session.close()

    except Exception as e:
        logger.exception(f"执行会话命令失败: {str(e)}")

        # 如果是list操作，即使出错也不抛出错误，而是提示没有会话
        if action == "list":
            console.print("\n当前没有工作流会话。\n")
            console.print("您可以使用 [cyan]vibecopilot flow run --workflow <工作流ID>[/cyan] 创建新会话。\n")
            return True, "", {"sessions": []}

        return False, f"❌ 会话命令执行失败: {str(e)}", None


def _create_session(db_session, args, ctx):
    """Create a new workflow session."""
    workflow_id = args.workflow
    session_name = args.name
    task_id = args.task  # Get task_id from args
    verbose = args.verbose

    try:
        manager = FlowSessionManager(db_session)
        session = manager.create_session(workflow_id=workflow_id, session_name=session_name, task_id=task_id)  # Pass task_id to the manager
        if verbose:
            click.echo(f"Created session: {session.session_id} for workflow: {workflow_id}")
            if task_id:
                click.echo(f"Session linked to task: {task_id}")
        return True
    except ValueError as e:
        print_error(f"Error creating session: {str(e)}")
        return False


def handle_create_session(db_session, workflow: str, name: str = None, task: str = None, verbose: bool = False):
    """创建新的工作流会话"""
    try:
        session_manager = FlowSessionManager(db_session)
        new_session = session_manager.create_session(workflow_id=workflow, name=name, task_id=task)

        if verbose:
            click.echo(f"创建新会话 {new_session.name} (ID: {new_session.id})")
            if task:
                click.echo(f"会话已关联到任务 ID: {task}")
            click.echo(f"已设置为当前会话")
        return 0
    except Exception as e:
        click.echo(f"创建会话失败: {str(e)}", err=True)
        return 1

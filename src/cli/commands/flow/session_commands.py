"""
工作流会话命令模块

提供工作流会话相关命令的实现，包括列表、查看、切换、暂停、恢复等功能。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from sqlalchemy.orm import Session as SQLAlchemySession

from src.cli.commands.flow.handlers.session_crud import handle_session_command
from src.db import init_db

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="session", help="管理工作流会话")
def session():
    """
    工作流会话管理

    工作流会话是工作流定义的运行实例，记录执行状态和上下文。
    会话通过 'vc flow session create --flow <工作流>' 命令创建。

    常用命令:
      vc flow session create --flow <id>  # 创建新会话
      vc flow session list                    # 列出所有会话
      vc flow session show <id>               # 显示会话详情
      vc flow session close <id>              # 结束会话
      vc flow session switch <id>             # 切换当前活动会话
    """
    pass


@session.command(name="list", help="列出所有会话")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["yaml", "text", "json"]), default="yaml", help="输出格式")
@click.option("--status", help="按状态筛选会话")
@click.option("--flow", help="按工作流ID筛选会话")
def list_sessions(verbose: bool, format: str, status: Optional[str], flow: Optional[str]) -> None:
    """列出工作流会话

    显示所有已创建的工作流会话及其状态。

    选项:
      --status   按会话状态筛选 (ACTIVE、PAUSED、COMPLETED、CLOSED)
      --flow     按工作流ID筛选
      --format   输出格式 (yaml、text、json)
    """
    try:
        if verbose:
            console.print("正在获取会话列表...")

        # 使用命令参数直接传递，不再创建argparse.Namespace对象
        params: Dict[str, Any] = {"subcommand": "list", "verbose": verbose, "format": format, "status": status, "flow": flow}
        success, message, data = handle_session_command(params)

        if success:
            if verbose:
                console.print("[green]成功获取会话列表[/green]")
            console.print(message)
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"列出会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="switch", help="切换当前活动会话")
@click.argument("id_or_name", type=str, required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def switch_session(id_or_name: Optional[str], verbose: bool) -> None:
    """切换当前活动会话

    将指定会话设置为当前活动会话。切换后，所有不指定会话ID的命令
    （如flow run、flow context等）都将默认使用此会话。

    ID_OR_NAME: 会话ID或名称
    """
    try:
        if id_or_name is None:
            console.print("[red]错误: 缺少必要参数 'ID_OR_NAME'[/red]")
            console.print("用法: vibecopilot flow session switch <ID或名称>")
            console.print("示例: vibecopilot flow session switch session_abc123")
            return

        if verbose:
            console.print(f"切换到会话: {id_or_name}")

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "switch", "id_or_name": id_or_name, "verbose": verbose}
        success, message, data = handle_session_command(params)

        if success:
            session_info: Dict[str, Any] = data.get("session", {})
            name = session_info.get("name", id_or_name)
            workflow_id = session_info.get("workflow_id", "未知")
            console.print(f"[green]已切换到会话: {name}[/green]")
            console.print(f"会话ID: {session_info.get('id')}")
            console.print(f"工作流: {workflow_id}")
            console.print(f"当前阶段: {session_info.get('current_stage_id', '无')}")
            console.print(f"使用 'vc flow context' 命令查看当前阶段的定义和上下文")
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"切换会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="show", help="显示特定会话的详细信息")
@click.argument("id_or_name", type=str, required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["yaml", "text", "json"]), default="yaml", help="输出格式")
def show_session(id_or_name: Optional[str], verbose: bool, format: str) -> None:
    """显示工作流会话的详细信息

    显示会话的完整信息，包括基本信息、当前状态和阶段进度。

    ID_OR_NAME: 会话ID或名称
    """
    try:
        if id_or_name is None:
            console.print("[red]错误: 缺少必要参数 'ID_OR_NAME'[/red]")
            console.print("用法: vibecopilot flow session show <ID或名称>")
            console.print("示例: vibecopilot flow session show session_abc123")
            return

        if verbose:
            console.print(f"获取会话详情: {id_or_name}")

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "show", "id_or_name": id_or_name, "verbose": verbose, "format": format}
        success, message, data = handle_session_command(params)

        if success:
            if verbose:
                console.print("[green]成功获取会话详情[/green]")
            console.print(message)
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"显示会话详情失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="create", help="创建并启动新会话")
@click.option("--flow", "-w", required=True, help="工作流的ID或名称 (不是工作流类型)")
@click.option("--name", "-n", required=False, help="会话名称")
@click.option("--task", "-t", required=False, help="关联的任务ID")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
def create_session(flow: str, name: Optional[str], task: Optional[str], verbose: bool) -> None:
    """创建工作流会话

    创建新的工作流会话并将其设置为当前活动会话。
    每个会话可以关联到一个任务，表明会话的目的是完成该任务。

    选项:
      --flow  工作流的ID或名称 (必填)，注意不是工作流类型如"dev"
      --name      会话名称 (可选，默认使用工作流名称)
      --task      关联的任务ID (可选，会话将专注于完成此任务)

    示例:
      vc flow session create --flow dev-workflow-123  # 使用ID创建
      vc flow session create --flow "需求分析流程"    # 使用名称创建
    """
    try:
        if verbose:
            console.print(f"创建新会话, 工作流: {flow}")
            if task:
                console.print(f"关联到任务: {task}")

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "create", "workflow_id": flow, "name": name, "task_id": task, "verbose": verbose}
        success, message, data = handle_session_command(params)

        if success:
            session_info: Dict[str, Any] = data.get("session", {})
            name = session_info.get("name", "未命名")
            id = session_info.get("id")
            task_id = session_info.get("task_id")
            console.print(f"[green]已创建会话: {name}[/green]")
            console.print(f"会话ID: {id}")
            if task_id:
                console.print(f"关联任务: {task_id}")
            console.print(f"使用 'vc flow context' 命令查看当前阶段")
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"创建工作会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="close", help="结束会话")
@click.argument("id_or_name", type=str, required=False)
@click.option("--reason", help="会话结束原因")
@click.option("--force", "-f", is_flag=True, help="强制结束，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def close_session(id_or_name: Optional[str], reason: Optional[str], force: bool, verbose: bool) -> None:
    """结束工作流会话

    将会话状态设置为已关闭。已关闭的会话可以查看但不能继续使用。

    ID_OR_NAME: 会话ID或名称
    """
    try:
        if id_or_name is None:
            console.print("[red]错误: 缺少必要参数 'ID_OR_NAME'[/red]")
            console.print("用法: vibecopilot flow session close <ID或名称>")
            console.print("示例: vibecopilot flow session close session_abc123")
            return

        if not force:
            # 确认提示
            if not click.confirm(f"确定要结束会话 {id_or_name} 吗? 结束后会话将无法继续运行。"):
                console.print("操作已取消")
                return

        if verbose:
            console.print(f"结束会话: {id_or_name}")

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "close", "id_or_name": id_or_name, "reason": reason, "force": force, "verbose": verbose}
        success, message, data = handle_session_command(params)

        if success:
            session_info: Dict[str, Any] = data.get("session", {})
            name = session_info.get("name", id_or_name)
            console.print(f"[green]已成功结束会话: {name}[/green]")
            if reason:
                console.print(f"结束原因: {reason}")
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"结束会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="delete", help="永久删除会话（不可恢复）")
@click.argument("id_or_name", type=str, required=False)
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def delete_session(id_or_name: Optional[str], force: bool, verbose: bool) -> None:
    """永久删除会话及其相关数据

    此操作将会永久删除会话及其所有相关数据。
    ⚠️ 警告：此操作不可恢复！如果只是想结束会话，请使用close命令。

    ID_OR_NAME: 会话ID或名称
    """
    try:
        if id_or_name is None:
            console.print("[red]错误: 缺少必要参数 'ID_OR_NAME'[/red]")
            console.print("用法: vibecopilot flow session delete <ID或名称>")
            console.print("示例: vibecopilot flow session delete session_abc123")
            return

        if not force:
            # 确认提示
            if not click.confirm(f"⚠️ 警告: 确定要永久删除会话 {id_or_name} 吗? 此操作不可撤销!"):
                console.print("操作已取消")
                return

        if verbose:
            console.print(f"删除会话: {id_or_name}")

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "delete", "id_or_name": id_or_name, "force": force, "verbose": verbose}
        success, message, data = handle_session_command(params)

        if success:
            console.print(f"[green]已永久删除会话: {id_or_name}[/green]")
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@session.command(name="update", help="更新会话属性")
@click.argument("id_or_name", type=str, required=False)
@click.option("--name", help="新的会话名称")
@click.option("--status", type=click.Choice(["ACTIVE", "PAUSED", "COMPLETED", "CLOSED"], case_sensitive=True), help="设置会话状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def update_session(id_or_name: Optional[str], name: Optional[str], status: Optional[str], verbose: bool) -> None:
    """更新会话属性

    ID_OR_NAME: 会话ID或名称
    """
    try:
        if id_or_name is None:
            console.print("[red]错误: 缺少必要参数 'ID_OR_NAME'[/red]")
            console.print("用法: vibecopilot flow session update <ID或名称> --name <新名称> --status <新状态>")
            console.print("示例: vibecopilot flow session update session_abc123 --name '新项目会话'")
            return

        if verbose:
            console.print(f"更新会话属性: {id_or_name}")

        # 至少需要一个要更新的属性
        if not name and not status:
            console.print("[yellow]请指定至少一个要更新的属性 (例如: --name 或 --status)[/yellow]")
            return

        # 使用命令参数直接传递
        params: Dict[str, Any] = {"subcommand": "update", "id_or_name": id_or_name, "name": name, "status": status, "verbose": verbose}
        success, message, data = handle_session_command(params)

        if success:
            session_info: Dict[str, Any] = data.get("session", {})
            console.print(f"[green]已更新会话[/green]")
            if name:
                console.print(f"新名称: {name}")
            if status:
                console.print(f"新状态: {status}")
        else:
            console.print(f"[red]错误: {message}[/red]")

    except Exception as e:
        logger.error(f"更新会话失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")

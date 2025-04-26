"""
工作流命令模块

提供工作流创建、管理和执行的命令接口。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console

# 从flow_crud_commands模块导入CRUD命令
from src.cli.commands.flow.flow_crud_commands import create, delete, export, update

# 从flow_info模块导入处理函数
from src.cli.commands.flow.handlers.flow_info import handle_context_subcommand, handle_next_subcommand

# 保留其他处理程序的导入
from src.cli.commands.flow.handlers.list import handle_list_subcommand
from src.cli.commands.flow.handlers.session_utils import get_active_session
from src.cli.commands.flow.handlers.show import handle_show_subcommand

# 从session_commands模块导入session命令
from src.cli.commands.flow.session_commands import session

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="flow", help="工作流管理命令")
def flow():
    """
    工作流管理命令组

    提供工作流定义和会话的管理功能。
    """
    pass


def register_basic_commands(flow_group):
    """向主命令组注册基本命令"""

    @flow_group.command(name="list", help="列出所有工作流定义")
    @click.option("--type", "workflow_type", help="按工作流类型筛选")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    # 使用pass_service装饰器注入FlowService实例
    # ServiceFactory会根据service_type创建对应的服务实例
    def list_flow(workflow_type: Optional[str], verbose: bool) -> None:
        """列出所有工作流定义"""
        try:
            if verbose:
                console.print("正在获取工作流列表...")

            # 调用处理函数
            result: Dict[str, Any] = handle_list_subcommand({"workflow_type": workflow_type, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取工作流列表[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"列出工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="context", help="获取并解释工作流阶段上下文")
    @click.argument("stage_id", required=False)
    @click.option("--session", "-s", help="会话ID或名称，不指定则使用当前活动会话")
    @click.option("--completed", "-c", multiple=True, help="标记为已完成的检查项名称或ID")
    @click.option("--format", "-f", type=click.Choice(["json", "text"]), default="text", help="输出格式")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    # 注入flow类型的服务实例
    def context_flow(stage_id: Optional[str], session: Optional[str], completed: Tuple[str, ...], format: str, verbose: bool) -> None:
        """
        获取并解释工作流阶段上下文

        如果不指定参数，将获取当前活动会话的当前阶段上下文。
        使用--session选项指定特定会话的ID或名称。
        使用--completed选项标记检查项已完成。

        示例:
          vc flow context                       # 获取当前会话的当前阶段上下文
          vc flow context planning              # 获取当前会话中planning阶段的上下文
          vc flow context --session demo        # 获取名为"demo"会话的当前阶段上下文
          vc flow context planning --session demo # 获取名为"demo"会话的planning阶段上下文
          vc flow context --completed "需求分析" # 标记"需求分析"检查项为已完成
        """
        try:
            # 获取会话信息，这里不要求阶段信息，允许没有阶段也能继续
            target_session, session_id, session_name, current_stage_id = get_active_session(session_id=session, verbose=verbose, require_stage=False)
            if not session_id:
                return

            # 确定阶段ID
            stage = stage_id
            if not stage and target_session:
                # 使用当前阶段ID，即使它可能为None
                # handler会负责进一步处理
                stage = current_stage_id

            if verbose:
                console.print(f"正在获取会话 '{session_name}' ({session_id}) 的上下文...")
                if stage:
                    console.print(f"目标阶段: {stage}")
                else:
                    console.print(f"[yellow]提示: 未指定目标阶段，将尝试使用当前阶段或第一个阶段[/yellow]")

            # 调用处理函数
            result: Dict[str, Any] = handle_context_subcommand(
                {
                    "stage_id": stage,
                    "stage": stage,
                    "session": session_id,
                    "completed": list(completed) if completed else None,
                    "format": format,
                    "verbose": verbose,
                    "_agent_mode": False,
                }
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功解释工作流阶段[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.exception("解释工作流阶段失败")
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="next", help="获取下一阶段建议")
    @click.option("--session", "-s", help="会话ID或名称，不指定则使用当前活动会话")
    @click.option("--current", help="当前阶段ID (可选，不指定则使用会话当前阶段)")
    @click.option("--format", "-f", type=click.Choice(["json", "text"]), default="text", help="输出格式")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    # FlowService实例由ServiceFactory创建并注入
    def next_flow(session: Optional[str], current: Optional[str], format: str, verbose: bool) -> None:
        """
        获取下一阶段建议

        如果不指定参数，将获取当前活动会话的下一阶段建议。
        使用--session选项指定特定会话的ID或名称。

        示例:
          vc flow next                 # 获取当前会话的下一阶段建议
          vc flow next --session demo  # 获取名为"demo"会话的下一阶段建议
        """
        try:
            # 获取会话信息，这里不要求阶段信息，允许没有阶段也能继续
            target_session, session_id, session_name, current_stage_id = get_active_session(session_id=session, verbose=verbose, require_stage=False)
            if not session_id:
                return

            # 如果没有指定当前阶段，使用会话当前阶段
            current_stage = current or current_stage_id

            if verbose:
                console.print(f"正在获取会话 '{session_name}' ({session_id}) 的下一阶段建议...")
                if current_stage:
                    console.print(f"当前阶段: {current_stage}")
                else:
                    console.print(f"[yellow]提示: 未指定当前阶段，将尝试使用当前阶段或第一个阶段[/yellow]")

            # 调用处理函数
            result: Dict[str, Any] = handle_next_subcommand(
                {"session_id": session_id, "current": current_stage, "format": format, "verbose": verbose, "_agent_mode": False}
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取下一阶段建议[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"获取下一阶段建议失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="show", help="查看会话或工作流定义详情")
    @click.argument("id", required=False)
    @click.option("--format", "-f", type=click.Choice(["json", "text", "mermaid", "yaml"]), default="yaml", help="输出格式 (yaml格式用于显示阶段和转换)")
    @click.option("--diagram", is_flag=True, help="在文本或JSON输出中包含Mermaid图表 (仅工作流定义)")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    def show(id: Optional[str], format: str, diagram: bool, verbose: bool) -> None:
        """
        查看会话或工作流定义详情

        根据提供的ID前缀 (如 'wf_', 'ss_') 自动判断是查看工作流还是会话。
        如果未提供ID，则显示当前活动会话信息。
        如果ID没有标准前缀，则假定为会话ID或名称。

        示例:
          vc flow show                # 显示当前会话信息
          vc flow show ss_xxxx        # 显示ID为ss_xxxx的会话信息
          vc flow show wf_yyyy        # 显示ID为wf_yyyy的工作流定义
          vc flow show my-session-name # 显示名称为my-session-name的会话信息
        """
        try:
            target_id_or_name = id

            # If no ID provided, default to showing current session
            if not target_id_or_name:
                _, active_session_id, _, _ = get_active_session(session_id=None, verbose=verbose)
                if not active_session_id:
                    # get_active_session already prints error, just return
                    return
                target_id_or_name = active_session_id
                if verbose:
                    console.print(f"未提供ID，将显示当前活动会话: {target_id_or_name}")

            if verbose:
                # Type determination happens in handler, log is generic here
                console.print(f"正在获取 {target_id_or_name} 的详情...")

            # Call the handler
            result = handle_show_subcommand(
                {
                    "id": target_id_or_name,
                    "format": format,
                    "diagram": diagram,
                    "verbose": verbose,
                    "_agent_mode": False,
                }
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取详情[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")


# 注册命令
register_basic_commands(flow)
flow.add_command(session)
flow.add_command(create)
flow.add_command(update)
flow.add_command(delete)
flow.add_command(export)

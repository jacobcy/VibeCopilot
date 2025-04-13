"""
工作流基本命令模块

提供工作流基本命令的实现，如列表、显示、运行等。
创建命令已移至flow_create_commands.py模块中。
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console

# 导入所有处理函数
from src.cli.commands.flow.handlers.context import handle_context_subcommand
from src.cli.commands.flow.handlers.delete import handle_delete_subcommand
from src.cli.commands.flow.handlers.export import handle_export_subcommand
from src.cli.commands.flow.handlers.imports import handle_import_subcommand
from src.cli.commands.flow.handlers.list import handle_list_subcommand
from src.cli.commands.flow.handlers.next import handle_next_subcommand
from src.cli.commands.flow.handlers.show import handle_show_subcommand
from src.cli.commands.flow.handlers.update import handle_update_subcommand
from src.cli.commands.flow.handlers.visualize import handle_visualize_subcommand
from src.cli.decorators import pass_service
from src.workflow.service.flow_service import FlowService

console = Console()
logger = logging.getLogger(__name__)


def register_basic_commands(flow_group):
    """向主命令组注册基本命令"""

    @flow_group.command(name="list", help="列出所有工作流定义")
    @click.option("--type", "workflow_type", help="按工作流类型筛选")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def list_flow(service: FlowService, workflow_type: Optional[str], verbose: bool) -> None:
        """列出所有工作流定义"""
        try:
            if verbose:
                console.print("正在获取工作流列表...")

            # 调用处理函数
            result = handle_list_subcommand({"workflow_type": workflow_type, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取工作流列表[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"列出工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="show", help="查看会话或工作流定义详情")
    @click.argument("id", required=False)
    @click.option("--workflow", "-w", is_flag=True, help="查看工作流定义而非会话信息")
    @click.option("--format", "-f", type=click.Choice(["json", "text", "mermaid"]), default="text", help="输出格式")
    @click.option("--diagram", is_flag=True, help="在文本或JSON输出中包含Mermaid图表")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def show_flow(service: FlowService, id: Optional[str], workflow: bool, format: str, diagram: bool, verbose: bool) -> None:
        """
        查看会话或工作流定义详情

        默认显示当前会话信息。
        直接指定ID参数时查看指定会话信息。
        使用--workflow选项时查看工作流定义。

        示例:
          vc flow show                # 显示当前会话信息
          vc flow show session123     # 显示ID为session123的会话信息
          vc flow show --workflow dev # 显示ID为dev的工作流定义
          vc flow show dev --workflow # 显示ID为dev的工作流定义
        """
        try:
            target_id = id
            is_workflow = workflow

            # 如果未提供ID
            if not target_id:
                if is_workflow:
                    # 请求查看工作流但未提供ID
                    console.print("[red]错误: 使用--workflow选项时必须提供工作流ID[/red]")
                    return
                else:
                    # 查看当前会话
                    current_session = service.get_current_session()
                    if not current_session:
                        console.print("[yellow]没有活跃的会话。请先创建会话或指定会话ID。[/yellow]")
                        console.print("[blue]提示: 使用 'vc flow create session --workflow <工作流ID>' 创建新会话[/blue]")
                        return
                    target_id = current_session.id
                    if verbose:
                        console.print(f"使用当前活跃会话: {target_id}")

            if verbose:
                console.print(f"正在获取{'工作流' if is_workflow else '会话'} {target_id} 的详情...")

            # 调用整合后的处理函数
            result = handle_show_subcommand(
                {"id": target_id, "is_workflow": is_workflow, "format": format, "diagram": diagram, "verbose": verbose, "_agent_mode": False}
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取详情[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"获取详情失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="update", help="更新工作流定义")
    @click.argument("id")
    @click.option("--name", help="新的工作流名称")
    @click.option("--desc", "--description", help="新的工作流描述")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def update_flow(service: FlowService, id: str, name: Optional[str], description: Optional[str], verbose: bool) -> None:
        """更新工作流定义"""
        try:
            if verbose:
                console.print(f"正在更新工作流 {id}...")

            # 调用处理函数
            result = handle_update_subcommand({"id": id, "name": name, "description": description, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功更新工作流[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"更新工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="context", help="获取并解释工作流阶段上下文")
    @click.argument("stage_id", required=False)
    @click.option("--session", "-s", help="会话ID或名称，不指定则使用当前活动会话")
    @click.option("--completed", "-c", multiple=True, help="标记为已完成的检查项名称或ID")
    @click.option("--format", "-f", type=click.Choice(["json", "text"]), default="text", help="输出格式")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def context_flow(service: FlowService, stage_id: Optional[str], session: Optional[str], completed: tuple, format: str, verbose: bool) -> None:
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
            # 首先获取会话信息
            from src.flow_session.session.manager import FlowSessionManager

            # 直接使用service中已有的会话管理器
            session_manager = service.session_manager

            target_session = None
            if session:
                # 如果指定了会话ID或名称，获取该会话
                target_session = session_manager.get_session(session)
                if not target_session:
                    console.print(f"[red]错误: 找不到ID或名称为 '{session}' 的会话[/red]")
                    return
            else:
                # 否则使用当前活动会话
                target_session = session_manager.get_current_session()
                if not target_session:
                    console.print("[red]错误: 没有活动会话。请先创建会话或使用 --session 指定会话。[/red]")
                    console.print("[blue]提示: 使用 'vc flow create session --workflow <工作流ID>' 创建新会话[/blue]")
                    return

            # 确定阶段ID
            stage = stage_id
            if not stage:
                # 如果没有指定阶段，使用会话当前阶段
                stage = target_session.current_stage_id
                if not stage:
                    console.print("[red]错误: 会话没有当前阶段。请指定阶段ID。[/red]")
                    return

            if verbose:
                console.print(f"正在获取会话 '{target_session.name}' ({target_session.id}) 的阶段 '{stage}' 上下文...")

            # 调用处理函数
            result = handle_context_subcommand(
                {
                    "stage": stage,
                    "session": target_session.id,
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
    @pass_service(service_type="flow")
    def next_flow(service: FlowService, session: Optional[str], current: Optional[str], format: str, verbose: bool) -> None:
        """
        获取下一阶段建议

        如果不指定参数，将获取当前活动会话的下一阶段建议。
        使用--session选项指定特定会话的ID或名称。

        示例:
          vc flow next                 # 获取当前会话的下一阶段建议
          vc flow next --session demo  # 获取名为"demo"会话的下一阶段建议
        """
        try:
            # 首先获取会话信息
            from src.flow_session.session.manager import FlowSessionManager

            # 直接使用service中已有的会话管理器
            session_manager = service.session_manager

            target_session = None
            if session:
                # 如果指定了会话ID或名称，获取该会话
                target_session = session_manager.get_session(session)
                if not target_session:
                    console.print(f"[red]错误: 找不到ID或名称为 '{session}' 的会话[/red]")
                    return
            else:
                # 否则使用当前活动会话
                target_session = session_manager.get_current_session()
                if not target_session:
                    console.print("[red]错误: 没有活动会话。请先创建会话或使用 --session 指定会话。[/red]")
                    console.print("[blue]提示: 使用 'vc flow create session --workflow <工作流ID>' 创建新会话[/blue]")
                    return

            if verbose:
                console.print(f"正在获取会话 '{target_session.name}' ({target_session.id}) 的下一阶段建议...")

            # 如果没有指定当前阶段，使用会话当前阶段
            current_stage = current or target_session.current_stage_id

            # 调用处理函数
            result = handle_next_subcommand(
                {"session_id": target_session.id, "current": current_stage, "format": format, "verbose": verbose, "_agent_mode": False}
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取下一阶段建议[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.exception("获取下一阶段建议失败")
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="visualize", help="可视化工作流结构和进度")
    @click.argument("id", required=False)
    @click.option("--session", "-s", is_flag=True, help="目标是会话ID而非工作流ID")
    @click.option("--format", "-f", type=click.Choice(["mermaid", "text"]), default="mermaid", help="可视化格式")
    @click.option("--output", "-o", help="输出文件路径")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def visualize_flow(service: FlowService, id: Optional[str], session: bool, format: str, output: Optional[str], verbose: bool) -> None:
        """可视化工作流结构和执行进度

        如果不提供ID参数，则显示当前活跃会话。
        如果提供ID且使用--session选项，则显示指定会话。
        如果提供ID但不使用--session选项，则显示指定工作流定义。

        ID: 工作流ID或会话ID（可选）
        """
        try:
            # 如果没有提供ID，则获取当前会话
            target_id = id
            is_session = session

            if not target_id:
                # 获取当前会话
                current_session = service.get_current_session()
                if not current_session:
                    console.print("[yellow]没有活跃的会话。请指定工作流ID或会话ID，或者先创建/激活一个会话[/yellow]")
                    return
                target_id = current_session.id
                is_session = True

                if verbose:
                    console.print(f"使用当前活跃会话: {target_id}")

            # 调用处理函数
            result = handle_visualize_subcommand(
                {"id": target_id, "session": is_session, "format": format, "output": output, "verbose": verbose, "_agent_mode": False}
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功生成可视化结果[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"可视化工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="export", help="导出工作流定义")
    @click.argument("workflow_id")
    @click.option("--format", "-f", type=click.Choice(["json", "mermaid"]), default="json", help="导出格式")
    @click.option("--output", "-o", help="输出文件路径")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def export_flow(service: FlowService, workflow_id: str, format: str, output: Optional[str], verbose: bool) -> None:
        """导出工作流定义"""
        try:
            if verbose:
                console.print(f"正在导出工作流 {workflow_id}...")

            # 调用处理函数
            result = handle_export_subcommand(
                {"workflow_id": workflow_id, "format": format, "output": output, "verbose": verbose, "_agent_mode": False}
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功导出工作流[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"导出工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="import", help="导入工作流定义（同名工作流将自动替换）")
    @click.argument("file_path")
    @click.option("--name", help="导入后使用的工作流名称，如不提供则使用原名称")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def import_flow(service: FlowService, file_path: str, name: Optional[str], verbose: bool) -> None:
        """导入工作流定义"""
        try:
            if verbose:
                console.print(f"正在导入工作流文件 {file_path}...")

            # 调用处理函数
            result = handle_import_subcommand({"file_path": file_path, "name": name, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功导入工作流[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"导入工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="delete", help="删除工作流定义")
    @click.argument("workflow_id")
    @click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    @pass_service(service_type="flow")
    def delete_flow(service: FlowService, workflow_id: str, force: bool, verbose: bool) -> None:
        """删除工作流定义"""
        try:
            if verbose:
                console.print(f"正在删除工作流 {workflow_id}...")

            # 调用处理函数
            result = handle_delete_subcommand({"workflow_id": workflow_id, "force": force, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功删除工作流[/green]")
                console.print(result["message"])
            elif result["status"] == "cancelled":
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"删除工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

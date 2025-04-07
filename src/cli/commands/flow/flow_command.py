#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flow 命令实现

提供工作流相关命令的实现
"""

import argparse
import logging
import subprocess
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

from src.cli.commands.base_command import BaseCommand

# Import all handlers from the handlers directory
from src.cli.commands.flow.handlers.context_handler import handle_context_subcommand
from src.cli.commands.flow.handlers.create_handler import handle_create_subcommand
from src.cli.commands.flow.handlers.export_handler import handle_export_subcommand
from src.cli.commands.flow.handlers.import_handler import handle_import_subcommand
from src.cli.commands.flow.handlers.list_handler import handle_list_subcommand
from src.cli.commands.flow.handlers.next_handler import handle_next_subcommand
from src.cli.commands.flow.handlers.run_handler import handle_run_subcommand
from src.cli.commands.flow.handlers.session_handlers import handle_session_command
from src.cli.commands.flow.handlers.show_handler import handle_show_subcommand
from src.cli.commands.flow.handlers.update_handler import handle_update_subcommand
from src.cli.commands.flow.handlers.visualize_handler import handle_visualize_subcommand

# Keep register_commands for session subcommand setup
from src.flow_session import register_commands

logger = logging.getLogger(__name__)
console = Console()


class FlowCommand(BaseCommand):
    """flow 命令"""

    def __init__(self):
        super().__init__(
            name="flow",
            description="管理和执行工作流",
        )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

        # list 子命令
        list_parser = subparsers.add_parser("list", help="列出所有工作流定义")
        list_parser.add_argument("--type", help="按工作流类型筛选", dest="workflow_type")
        list_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # create 子命令
        create_parser = subparsers.add_parser("create", help="创建工作流定义")
        # Arguments for create handler need checking/updating
        create_parser.add_argument("--rule-path", help="从规则文件创建", dest="rule_path")
        create_parser.add_argument("--template", help="从模板创建", dest="template")
        create_parser.add_argument("--variables", help="模板变量JSON文件路径", dest="variables")
        create_parser.add_argument("--output", "-o", help="输出工作流文件路径（可选）", dest="output")
        # create_parser.add_argument("workflow_type", help="工作流类型 (如dev, research, design, docs)") # Old arg
        # create_parser.add_argument("--name", help="工作流名称") # Old arg
        # create_parser.add_argument("--desc", "--description", help="工作流描述", dest="description") # Old arg
        create_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # update 子命令
        update_parser = subparsers.add_parser("update", help="更新工作流定义")
        update_parser.add_argument("id", help="工作流ID")
        update_parser.add_argument("--name", help="新的工作流名称")
        update_parser.add_argument("--desc", "--description", help="新的工作流描述", dest="description")
        update_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # show 子命令 (原view命令)
        show_parser = subparsers.add_parser("show", help="查看工作流定义详情")
        show_parser.add_argument("workflow_id", help="工作流ID或类型")  # Updated help text
        show_parser.add_argument("--format", "-f", choices=["json", "text", "mermaid"], default="text", help="输出格式")
        show_parser.add_argument("--diagram", action="store_true", help="在文本或JSON输出中包含Mermaid图表")  # Added diagram flag
        show_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # run 子命令 - 新的统一方式
        run_parser = subparsers.add_parser("run", help="运行工作流的特定阶段")
        run_parser.add_argument("--workflow-id", help="工作流定义ID (用于启动新会话或参考)", dest="workflow_id")
        run_parser.add_argument("stage", help="要运行的目标阶段ID")
        # run_parser.add_argument("workflow_stage", help="工作流和阶段，格式为workflow_name:stage_name") # Old arg
        run_parser.add_argument("--name", "-n", help="会话名称 (如果创建新会话)")
        run_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")
        run_parser.add_argument("--session", "-s", help="会话ID，如果提供则使用现有会话")
        # Add way to pass context?
        # run_parser.add_argument("--context", help="JSON string or file path for context data")
        run_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # context 子命令
        context_parser = subparsers.add_parser("context", help="获取工作流阶段上下文")
        context_parser.add_argument("workflow_id", help="工作流ID")
        context_parser.add_argument("stage_id", help="阶段ID")
        context_parser.add_argument("--session", "-s", help="会话ID，如果提供则获取会话中的阶段上下文")
        context_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项 (可能已弃用)")
        context_parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
        context_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # next 子命令
        next_parser = subparsers.add_parser("next", help="获取下一阶段建议")
        next_parser.add_argument("session_id", help="会话ID")
        next_parser.add_argument("--current", help="当前阶段实例ID (可选)")
        next_parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
        next_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # visualize 子命令
        visualize_parser = subparsers.add_parser("visualize", help="可视化工作流结构")
        visualize_parser.add_argument("id", help="工作流ID或会话ID")
        visualize_parser.add_argument("--session", "-s", action="store_true", help="目标是会话ID而非工作流ID")
        visualize_parser.add_argument("--format", "-f", choices=["mermaid", "text"], default="mermaid", help="可视化格式")
        visualize_parser.add_argument("--output", "-o", help="输出文件路径")
        visualize_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # export 子命令
        export_parser = subparsers.add_parser("export", help="导出工作流定义")
        export_parser.add_argument("workflow_id", help="工作流ID或类型")  # Updated help text
        export_parser.add_argument("--format", "-f", choices=["json", "mermaid"], default="json", help="导出格式")
        export_parser.add_argument("--output", "-o", help="输出文件路径")
        export_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # import 子命令
        import_parser = subparsers.add_parser("import", help="导入工作流定义")
        import_parser.add_argument("file_path", help="要导入的工作流文件路径")
        import_parser.add_argument("--overwrite", action="store_true", help="覆盖同名工作流")
        import_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # session 子命令 - 注册会话管理命令
        session_parser = subparsers.add_parser("session", help="管理工作流会话")
        # Session arguments are configured by register_commands
        register_commands(session_parser)

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if not hasattr(args, "subcommand") or not args.subcommand:
            # 如果没有子命令，显示更友好的错误信息和帮助
            console.print("\n[bold red]错误:[/bold red] 请指定一个子命令\n")

            # 创建一个表格来展示子命令
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Command", style="cyan")
            table.add_column("Description")

            table.add_row("list", "列出所有工作流定义")
            table.add_row("create", "创建新的工作流定义")
            table.add_row("show", "查看工作流定义详情")
            table.add_row("run", "运行工作流的特定阶段")
            table.add_row("update", "更新工作流定义")
            table.add_row("context", "获取工作流阶段上下文")
            table.add_row("next", "获取下一阶段建议")
            table.add_row("visualize", "可视化工作流结构")
            table.add_row("export", "导出工作流定义")
            table.add_row("import", "导入工作流定义")
            table.add_row("session", "管理工作流会话")

            console.print("可用的子命令:")
            console.print(table)
            console.print("\n使用 [cyan]vibecopilot flow <子命令> --help[/cyan] 获取具体命令的帮助信息")
            return 1

        # Convert Namespace to dict for handlers
        args_dict = vars(args)
        # Add agent mode flag if needed (passed from higher level?)
        args_dict["_agent_mode"] = False  # Placeholder

        # 将子命令分派到相应的处理函数
        try:
            result_dict = None
            if args.subcommand == "list":
                result_dict = handle_list_subcommand(args_dict)
            elif args.subcommand == "create":
                result_dict = handle_create_subcommand(args_dict)
            elif args.subcommand == "update":
                result_dict = handle_update_subcommand(args_dict)
            elif args.subcommand == "show":
                result_dict = handle_show_subcommand(args_dict)
            elif args.subcommand == "context":
                result_dict = handle_context_subcommand(args_dict)
            elif args.subcommand == "next":
                result_dict = handle_next_subcommand(args_dict)
            elif args.subcommand == "visualize":
                result_dict = handle_visualize_subcommand(args_dict)
            elif args.subcommand == "export":
                result_dict = handle_export_subcommand(args_dict)
            elif args.subcommand == "import":
                result_dict = handle_import_subcommand(args_dict)
            elif args.subcommand == "run":
                result_dict = handle_run_subcommand(args_dict)
            elif args.subcommand == "session":
                # 使用完整实现的 session_handlers.py 中的处理函数
                success, message, data = handle_session_command(args)
                result_dict = {
                    "status": "success" if success else "error",
                    "code": 0 if success else 1,
                    "message": message,
                    "data": data,
                    "meta": {"command": "flow session", "args": args_dict},
                }
            else:
                logger.error(f"未知子命令: {args.subcommand}")
                print(f"错误: 未知子命令 '{args.subcommand}'. 使用 --help 查看选项.")
                return 1

            # Process result
            if result_dict:
                success = result_dict.get("status") == "success"
                message = result_dict.get("message", "(无消息)")
                print(message)
                # Optionally print data if verbose or specific format
                # if args.verbose and result_dict.get("data"):
                #    print("\n--- Data ---")
                #    print(json.dumps(result_dict["data"], indent=2, ensure_ascii=False))
                return 0 if success else result_dict.get("code", 1)
            else:
                logger.error(f"处理器 for '{args.subcommand}' did not return a result dictionary.")
                print("命令执行时发生内部错误。")
                return 1

        except Exception as e:
            logger.exception(f"执行子命令 {args.subcommand} 时出错")
            print(f"执行命令出错: {str(e)}")
            return 1

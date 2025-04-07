#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flow 命令实现

提供工作流相关命令的实现
"""

import argparse
import logging
import subprocess
from typing import Any

from src.cli.commands.base_command import BaseCommand
from src.cli.commands.flow.flow_subcommands import (
    handle_context_subcommand,
    handle_create_subcommand,
    handle_export_subcommand,
    handle_import_subcommand,
    handle_list_subcommand,
    handle_next_subcommand,
    handle_run_subcommand,
    handle_session_subcommand,
    handle_show_subcommand,
    handle_update_subcommand,
    handle_visualize_subcommand,
)
from src.flow_session import register_commands

logger = logging.getLogger(__name__)


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
        create_parser.add_argument("workflow_type", help="工作流类型 (如dev, research, design, docs)")
        create_parser.add_argument("--name", help="工作流名称")
        create_parser.add_argument("--desc", "--description", help="工作流描述", dest="description")
        create_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # update 子命令
        update_parser = subparsers.add_parser("update", help="更新工作流定义")
        update_parser.add_argument("id", help="工作流ID")
        update_parser.add_argument("--name", help="新的工作流名称")
        update_parser.add_argument("--desc", "--description", help="新的工作流描述", dest="description")
        update_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # show 子命令 (原view命令)
        show_parser = subparsers.add_parser("show", help="查看工作流定义详情")
        show_parser.add_argument("id", help="工作流ID")
        show_parser.add_argument(
            "--format", "-f", choices=["json", "text"], default="text", help="输出格式"
        )
        show_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # run 子命令 - 新的统一方式
        run_parser = subparsers.add_parser("run", help="运行工作流的特定阶段")
        run_parser.add_argument("workflow_stage", help="工作流和阶段，格式为workflow_name:stage_name")
        run_parser.add_argument("--name", "-n", help="阶段名称")
        run_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")
        run_parser.add_argument("--session", "-s", help="会话ID，如果提供则使用现有会话")
        run_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # context 子命令
        context_parser = subparsers.add_parser("context", help="获取工作流阶段上下文")
        context_parser.add_argument("workflow_id", help="工作流ID")
        context_parser.add_argument("stage_id", help="阶段ID")
        context_parser.add_argument("--session", "-s", help="会话ID，如果提供则获取会话中的阶段上下文")
        context_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")
        context_parser.add_argument(
            "--format", "-f", choices=["json", "text"], default="text", help="输出格式"
        )
        context_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # next 子命令
        next_parser = subparsers.add_parser("next", help="获取下一阶段建议")
        next_parser.add_argument("session_id", help="会话ID")
        next_parser.add_argument("--current", help="当前阶段实例ID")
        next_parser.add_argument(
            "--format", "-f", choices=["json", "text"], default="text", help="输出格式"
        )
        next_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # visualize 子命令
        visualize_parser = subparsers.add_parser("visualize", help="可视化工作流结构")
        visualize_parser.add_argument("id", help="工作流ID或会话ID")
        visualize_parser.add_argument("--session", "-s", action="store_true", help="目标是会话ID而非工作流ID")
        visualize_parser.add_argument(
            "--format", "-f", choices=["mermaid", "text"], default="mermaid", help="可视化格式"
        )
        visualize_parser.add_argument("--output", "-o", help="输出文件路径")
        visualize_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # export 子命令
        export_parser = subparsers.add_parser("export", help="导出工作流定义")
        export_parser.add_argument("id", help="工作流ID")
        export_parser.add_argument(
            "--format", "-f", choices=["json", "mermaid"], default="json", help="导出格式"
        )
        export_parser.add_argument("--output", "-o", help="输出文件路径")
        export_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # import 子命令
        import_parser = subparsers.add_parser("import", help="导入工作流定义")
        import_parser.add_argument("file_path", help="要导入的工作流文件路径")
        import_parser.add_argument("--overwrite", action="store_true", help="覆盖同名工作流")
        import_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

        # session 子命令 - 注册会话管理命令
        session_parser = subparsers.add_parser("session", help="管理工作流会话")
        register_commands(session_parser)

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if not hasattr(args, "subcommand") or not args.subcommand:
            logger.error("未指定子命令")
            return 1

        # 将子命令分派到相应的处理函数
        try:
            if args.subcommand == "list":
                success, message, _ = handle_list_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "create":
                success, message, _ = handle_create_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "update":
                success, message, _ = handle_update_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "show":
                success, message, _ = handle_show_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "context":
                success, message, _ = handle_context_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "next":
                success, message, _ = handle_next_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "visualize":
                success, message, _ = handle_visualize_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "export":
                success, message, result = handle_export_subcommand(args)
                print(message)
                if success and result:
                    print("\n" + str(result))
                return 0 if success else 1

            elif args.subcommand == "import":
                success, message, _ = handle_import_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "run":
                success, message, _ = handle_run_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "session":
                success, message, _ = handle_session_subcommand(args)
                print(message)
                return 0 if success else 1

            else:
                logger.error(f"未知子命令: {args.subcommand}")
                return 1

        except Exception as e:
            logger.exception(f"执行子命令 {args.subcommand} 时出错")
            print(f"执行命令出错: {str(e)}")
            return 1

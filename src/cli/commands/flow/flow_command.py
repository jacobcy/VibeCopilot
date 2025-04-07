#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flow 命令实现

提供工作流相关命令的实现
"""

import argparse
import logging
from typing import Any

from src.cli.commands.base_command import BaseCommand
from src.cli.commands.flow.flow_subcommands import (
    handle_context_subcommand,
    handle_create_subcommand,
    handle_export_subcommand,
    handle_flow_type_subcommand,
    handle_list_subcommand,
    handle_view_subcommand,
)

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
        subparsers.add_parser("list", help="列出所有工作流")

        # create 子命令
        create_parser = subparsers.add_parser("create", help="从规则创建工作流")
        create_parser.add_argument("rule_path", help="规则文件路径")
        create_parser.add_argument("--output", "-o", help="输出文件路径")

        # view 子命令
        view_parser = subparsers.add_parser("view", help="查看工作流详情")
        view_parser.add_argument("workflow_id", help="工作流ID")
        view_parser.add_argument(
            "--format", "-f", choices=["json", "mermaid"], default="json", help="输出格式"
        )

        # 各个流程规则对应的子命令
        for flow_type in ["story", "spec", "coding", "test", "review", "commit"]:
            flow_parser = subparsers.add_parser(flow_type, help=f"执行{flow_type}流程")
            flow_parser.add_argument("--stage", "-s", help="指定阶段")
            flow_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")

        # context 子命令
        context_parser = subparsers.add_parser("context", help="获取工作流上下文")
        context_parser.add_argument("workflow_id", help="工作流ID")
        context_parser.add_argument("--stage", "-s", help="当前阶段ID")
        context_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")

        # export 子命令
        export_parser = subparsers.add_parser("export", help="导出工作流")
        export_parser.add_argument("workflow_id", help="工作流ID")
        export_parser.add_argument(
            "--format", "-f", choices=["json", "mermaid"], default="json", help="导出格式"
        )
        export_parser.add_argument("--output", "-o", help="输出文件路径")

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

            elif args.subcommand == "view":
                success, message, _ = handle_view_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "context":
                success, message, _ = handle_context_subcommand(args)
                print(message)
                return 0 if success else 1

            elif args.subcommand == "export":
                success, message, result = handle_export_subcommand(args)
                print(message)
                if success and result:
                    print("\n" + str(result))
                return 0 if success else 1

            elif args.subcommand in ["story", "spec", "coding", "test", "review", "commit"]:
                # 设置流程类型
                setattr(args, "flow_type", args.subcommand)
                success, message, _ = handle_flow_type_subcommand(args)
                print(message)
                return 0 if success else 1

            else:
                logger.error(f"未知子命令: {args.subcommand}")
                return 1

        except Exception as e:
            logger.exception(f"执行子命令 {args.subcommand} 时出错")
            print(f"执行命令出错: {str(e)}")
            return 1

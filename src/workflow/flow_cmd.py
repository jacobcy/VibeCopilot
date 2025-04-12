#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流命令行工具

提供工作流相关命令行操作
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional

from src.workflow.flow_cmd import (
    create_workflow_from_rule,
    format_checklist,
    format_deliverables,
    get_workflow_context,
    handle_create_command,
    handle_export_command,
    handle_list_command,
    handle_show_command,
    handle_start_command,
    run_workflow_stage,
)
from src.workflow.handlers import handle_run_command

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="工作流命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 创建子命令
    create_parser = subparsers.add_parser("create", help="创建工作流")
    create_parser.add_argument("--rule", dest="rule_path", help="规则文件路径")
    create_parser.add_argument("--template", help="模板名称")
    create_parser.add_argument("--variables", help="变量文件路径")
    create_parser.add_argument("--output", help="输出文件路径")

    # 列表子命令
    list_parser = subparsers.add_parser("list", help="列出工作流")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    list_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

    # 显示子命令
    show_parser = subparsers.add_parser("show", help="显示工作流")
    show_parser.add_argument("workflow_id", help="工作流ID")
    show_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    show_parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    show_parser.add_argument("--diagram", action="store_true", help="生成图表")

    # 运行子命令
    run_parser = subparsers.add_parser(
        "run",
        help="运行工作流或继续当前会话",
        description="""
运行工作流或继续当前会话。

不指定参数时，继续执行当前活跃会话的当前阶段。
指定STAGE参数时，在当前会话中运行指定阶段。
使用--workflow启动新的工作流，可以使用"工作流名称:阶段名称"格式指定阶段。

示例:
  vibecopilot flow run                     # 继续当前会话的当前阶段
  vibecopilot flow run planning            # 在当前会话中运行planning阶段
  vibecopilot flow run --workflow dev      # 启动dev工作流（从第一个阶段开始）
  vibecopilot flow run --workflow dev:test # 启动dev工作流的test阶段
    """,
    )
    run_parser.add_argument("stage", nargs="?", help="当前会话中要运行的阶段名称（可选）")
    run_parser.add_argument("--workflow", "-w", help="启动新工作流（格式：工作流名称 或 工作流名称:阶段名称）")
    run_parser.add_argument("--name", "-n", help="新会话的名称 (仅用于创建新会话)")
    run_parser.add_argument("--checklist", "-c", nargs="*", default=[], help="已完成的检查项")
    run_parser.add_argument("--session", "-s", help="指定会话ID (不指定则使用当前活跃会话)")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

    # 启动子命令
    start_parser = subparsers.add_parser("start", help="启动工作流")
    start_parser.add_argument("workflow_type", help="工作流类型")
    start_parser.add_argument("--name", help="会话名称")

    # 导出子命令
    export_parser = subparsers.add_parser("export", help="导出工作流")
    export_parser.add_argument("workflow_id", help="工作流ID")
    export_parser.add_argument("--output", help="输出文件路径")
    export_parser.add_argument("--format", choices=["json", "mermaid"], default="json", help="输出格式")

    # 解析命令行参数
    args = parser.parse_args()

    # 如果没有提供子命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1

    # 将参数转换为字典
    args_dict = vars(args)

    # 处理子命令
    try:
        if args.command == "create":
            result = handle_create_command(args_dict)
        elif args.command == "list":
            result = handle_list_command(args_dict)
        elif args.command == "show":
            result = handle_show_command(args_dict)
        elif args.command == "run":
            result = handle_run_command(args_dict)
        elif args.command == "start":
            result = handle_start_command(args_dict)
        elif args.command == "export":
            result = handle_export_command(args_dict)
        else:
            logger.error(f"未知命令: {args.command}")
            parser.print_help()
            return 1

        # 处理结果
        if result.get("success"):
            print(result.get("message", "操作成功"))
            return 0
        else:
            print(f"错误: {result.get('error', '未知错误')}")
            return 1
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
        print(f"错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

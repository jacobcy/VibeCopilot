#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库命令模块

提供知识库命令的实现，支持内容存储、检索和管理。
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table

from src.cli.commands.base_command import BaseCommand
from src.cli.commands.memory.memory_subcommands import (
    handle_create_subcommand,
    handle_delete_subcommand,
    handle_export_subcommand,
    handle_import_subcommand,
    handle_list_subcommand,
    handle_search_subcommand,
    handle_show_subcommand,
    handle_sync_subcommand,
    handle_update_subcommand,
)

logger = logging.getLogger(__name__)
console = Console()


class MemoryCommand(BaseCommand):
    """知识库命令，提供知识库管理功能"""

    def __init__(self):
        """初始化知识库命令"""
        super().__init__(name="memory", description="管理VibeCopilot知识库，支持内容存储、检索和管理")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        配置命令行解析器

        Args:
            parser: 命令行解析器
        """
        # 添加通用选项
        parser.add_argument("--verbose", action="store_true", help="提供详细输出")
        parser.add_argument("--agent-mode", action="store_true", help="启用agent优化的输出格式")

        subparsers = parser.add_subparsers(dest="subcommand", help="操作类型")

        # list子命令 - 列出知识库内容
        list_parser = subparsers.add_parser("list", help="列出知识库内容")
        list_parser.add_argument("--folder", help="筛选特定目录的内容")
        list_parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")

        # show子命令 - 显示知识库内容详情
        show_parser = subparsers.add_parser("show", help="显示知识库内容详情")
        show_parser.add_argument("--path", required=True, help="文档路径或标识符")
        show_parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")

        # create子命令 (原write) - 创建知识库内容
        create_parser = subparsers.add_parser("create", help="创建知识库内容")
        create_parser.add_argument("--title", required=True, help="文档标题")
        create_parser.add_argument("--folder", required=True, help="存储目录")
        create_parser.add_argument("--tags", help="标签列表，逗号分隔")
        create_parser.add_argument("--content", help="要保存的内容（如果不提供，将使用当前对话内容）")

        # update子命令 - 更新知识库内容
        update_parser = subparsers.add_parser("update", help="更新知识库内容")
        update_parser.add_argument("--path", required=True, help="文档路径或标识符")
        update_parser.add_argument("--content", required=True, help="更新后的内容")
        update_parser.add_argument("--tags", help="更新的标签，逗号分隔")

        # delete子命令 - 删除知识库内容
        delete_parser = subparsers.add_parser("delete", help="删除知识库内容")
        delete_parser.add_argument("--path", required=True, help="文档路径或标识符")
        delete_parser.add_argument("--force", action="store_true", help="强制删除，不提示确认")

        # search子命令 - 语义搜索知识库
        search_parser = subparsers.add_parser("search", help="语义搜索知识库")
        search_parser.add_argument("--query", required=True, help="搜索关键词")
        search_parser.add_argument("--type", help="内容类型")
        search_parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")

        # import子命令 - 导入本地文档到知识库
        import_parser = subparsers.add_parser("import", help="导入本地文档到知识库")
        import_parser.add_argument("--source-dir", required=True, help="源文档目录")
        import_parser.add_argument("--recursive", action="store_true", help="递归导入子目录")

        # export子命令 - 导出知识库到Obsidian
        export_parser = subparsers.add_parser("export", help="导出知识库到Obsidian")
        export_parser.add_argument("--db", help="数据库路径")
        export_parser.add_argument("--output", help="Obsidian输出目录")
        export_parser.add_argument("--format", choices=["md", "json"], default="md", help="导出格式")

        # sync子命令 - 同步Obsidian和标准文档
        sync_parser = subparsers.add_parser("sync", help="同步Obsidian和标准文档")
        sync_parser.add_argument("--sync-type", required=True, choices=["to-obsidian", "to-docs", "watch"], help="同步类型")

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """
        执行命令，使用解析后的参数

        Args:
            args: 解析后的参数对象

        Returns:
            命令执行结果状态码
        """
        if not hasattr(args, "subcommand") or not args.subcommand:
            # 如果没有子命令，显示更友好的错误信息和帮助
            console.print("\n[bold red]错误:[/bold red] 请指定一个子命令\n")

            # 创建一个表格来展示子命令
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Command", style="cyan")
            table.add_column("Description")

            table.add_row("list", "列出知识库内容")
            table.add_row("show", "显示知识库内容详情")
            table.add_row("create", "创建知识库内容")
            table.add_row("update", "更新知识库内容")
            table.add_row("delete", "删除知识库内容")
            table.add_row("search", "语义搜索知识库")
            table.add_row("import", "导入本地文档到知识库")
            table.add_row("export", "导出知识库到Obsidian")
            table.add_row("sync", "同步Obsidian和标准文档")

            console.print("可用的子命令:")
            console.print(table)
            console.print("\n使用 [cyan]vibecopilot memory <子命令> --help[/cyan] 获取具体命令的帮助信息")
            return 1

        # 根据子命令调用相应的处理函数
        try:
            if args.subcommand == "list":
                success, message, data = handle_list_subcommand(args)
            elif args.subcommand == "show":
                success, message, data = handle_show_subcommand(args)
            elif args.subcommand == "create":
                success, message, data = handle_create_subcommand(args)
            elif args.subcommand == "update":
                success, message, data = handle_update_subcommand(args)
            elif args.subcommand == "delete":
                success, message, data = handle_delete_subcommand(args)
            elif args.subcommand == "search":
                success, message, data = handle_search_subcommand(args)
            elif args.subcommand == "import":
                success, message, data = handle_import_subcommand(args)
            elif args.subcommand == "export":
                success, message, data = handle_export_subcommand(args)
            elif args.subcommand == "sync":
                success, message, data = handle_sync_subcommand(args)
            else:
                print(f"错误: 未知子命令 '{args.subcommand}'")
                return 1

            # 输出结果 - 根据agent模式决定输出格式
            if args.agent_mode:
                self._output_agent_mode(success, message, data, args.subcommand)
            else:
                self._output_human_mode(
                    success,
                    message,
                    data,
                    args.subcommand,
                    args.verbose if hasattr(args, "verbose") else False,
                )

            return 0 if success else 1

        except Exception as e:
            logger.exception(f"执行 memory {args.subcommand} 命令时发生错误")

            if args.agent_mode:
                self._output_agent_error(str(e), args.subcommand)
            else:
                print(f"❌ 命令执行失败: /memory {args.subcommand} [参数]\n")
                print(f"错误原因: {str(e)}")
                if hasattr(args, "verbose") and args.verbose:
                    import traceback

                    print(f"\n调试信息:\n{traceback.format_exc()}")

            return 1

    def _output_human_mode(self, success: bool, message: str, data: Any, subcommand: str, verbose: bool) -> None:
        """输出人类可读格式的结果"""
        if success:
            print(f"✅ 执行命令: /memory {subcommand} [参数]\n")
            print(message)

            if verbose and data:
                print("\n详细信息:")
                if isinstance(data, list):
                    for idx, item in enumerate(data, 1):
                        print(f"[{idx}] {item}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        print(f"{key}: {value}")
        else:
            print(f"❌ 命令执行失败: /memory {subcommand} [参数]\n")
            print(f"错误原因: {message}")

    def _output_agent_mode(self, success: bool, message: str, data: Any, subcommand: str) -> None:
        """输出Agent模式的结构化JSON结果"""
        import json

        result = {
            "status": "success" if success else "error",
            "code": 0 if success else 1,
            "message": message,
            "data": data,
            "next_actions": self._get_next_actions(success, subcommand, data),
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    def _output_agent_error(self, error_message: str, subcommand: str) -> None:
        """输出Agent模式的错误信息"""
        import json

        result = {
            "status": "error",
            "code": 1,
            "message": error_message,
            "data": None,
            "next_actions": [{"command": f"vibecopilot memory {subcommand} --help", "description": "获取命令使用帮助"}],
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    def _get_next_actions(self, success: bool, subcommand: str, data: Any) -> List[Dict[str, str]]:
        """根据当前操作获取建议的下一步操作"""
        if not success:
            return [{"command": f"vibecopilot memory {subcommand} --help", "description": "获取命令使用帮助"}]

        # 根据不同的子命令推荐不同的后续操作
        if subcommand == "list":
            return [{"command": "vibecopilot memory show --path=<path>", "description": "查看特定文档详情"}]
        elif subcommand == "show":
            return [
                {
                    "command": "vibecopilot memory update --path=<path> --content=<content>",
                    "description": "更新该文档",
                }
            ]
        elif subcommand == "create":
            if isinstance(data, dict) and "path" in data:
                return [
                    {
                        "command": f"vibecopilot memory show --path={data['path']}",
                        "description": "查看刚创建的文档",
                    }
                ]
            return []
        elif subcommand == "search":
            return [{"command": "vibecopilot memory show --path=<path>", "description": "查看搜索结果中的特定文档"}]

        return []

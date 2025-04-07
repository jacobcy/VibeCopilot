# src/cli/commands/task/task_command.py

import logging
import sys
from typing import Any, Dict, List, Type

import typer  # Import typer

from src.cli.command import Command

# Import BaseCommand
from src.cli.commands.base_command import BaseCommand

# IMPORTANT: Import the Typer app itself
from . import task_app  # Import the typer app defined in __init__.py
from .task_comment_command import CommentTaskCommand
from .task_create_command import CreateTaskCommand
from .task_delete_command import DeleteTaskCommand
from .task_link_command import LinkTaskCommand

# Import subcommand classes only for registration/help text generation perhaps
from .task_list_command import ListTaskCommand
from .task_show_command import ShowTaskCommand
from .task_update_command import UpdateTaskCommand

# from src.cli.command_result import CommandResult # Assuming this exists


logger = logging.getLogger(__name__)


class TaskCommand(BaseCommand, Command):
    """Task 命令组，处理所有 'task' 子命令

    提供完整的任务管理功能，包括创建、查看、更新、删除任务，
    以及添加评论和管理任务关联关系。任务系统类似于GitHub Issues，
    支持标签、负责人分配、状态跟踪等功能。

    可用子命令:
        list: 列出和过滤任务
        show: 显示任务详情
        create: 创建新任务
        update: 更新任务信息
        delete: 删除任务
        comment: 添加任务评论
        link: 管理任务关联

    用法:
        vibecopilot task <子命令> [选项]
        vibecopilot task --help
        vibecopilot task <子命令> --help

    示例:
        vibecopilot task list --status open
        vibecopilot task create -t "修复bug" -d "修复登录问题"
        vibecopilot task show abc123 --verbose
        vibecopilot task update def456 --status done
        vibecopilot task comment ghi789 -c "问题已修复"
        vibecopilot task link jkl012 -t roadmap --target S1
    """

    # Subcommands dictionary might now be mainly for help text generation
    # as the execution relies on the task_app
    subcommands_meta: Dict[str, Type[Command]] = {
        "list": ListTaskCommand,
        "show": ShowTaskCommand,
        "create": CreateTaskCommand,
        "update": UpdateTaskCommand,
        "delete": DeleteTaskCommand,
        "comment": CommentTaskCommand,
        "link": LinkTaskCommand,
    }

    def __init__(self):
        super().__init__("task", "任务管理命令 (类似 GitHub issue)")

    def execute(self, args: List[str]) -> int:
        """解析并执行 Task 子命令，使用 task_app"""
        if not args:
            self.print_help()
            return 1

        # Typer/Click expects the command name as part of the args list for run/invoke
        # So, args should be like ['list', '--status', 'open']
        # The main dispatcher in main.py already separates 'task' from the rest.

        try:
            # Use Typer's run method (which internally handles context and execution)
            # Pass the subcommand and its arguments directly
            # This leverages Typer's parsing, help handling (--help), etc.
            task_app(args=args, prog_name="vibecopilot task")  # prog_name helps with help messages
            return 0  # Typer handles SystemExit on errors, usually non-zero
        except typer.Exit as e:
            # Typer often uses Exit for clean exits (like after --help) or known errors
            return e.exit_code  # Return the code Typer intended
        except Exception as e:
            # Catch unexpected errors during command execution
            logger.exception(f"执行 task 命令 '{args}' 时发生意外错误: {e}")
            # Maybe print a generic error using rich console here if needed
            print(f"[bold red]错误:[/bold red] 执行 task 命令时发生意外错误: {e}", file=sys.stderr)
            return 1

    def print_help(self):
        """打印 Task 命令组的帮助信息 (使用 Typer app)"""
        try:
            # Use Typer's built-in help generation by invoking with --help
            task_app(args=["--help"], prog_name="vibecopilot task")
        except typer.Exit:
            # Expected exit after printing help
            pass
        except Exception as e:
            logger.error(f"生成 task 帮助信息时出错: {e}")
            # Fallback help text if Typer fails
            print("任务管理 (task)")
            print("用法: vibecopilot task <子命令> [参数]")
            print("\n可用子命令:")
            # Try to get descriptions from meta if Typer failed
            for name, cmd_class in self.subcommands_meta.items():
                try:
                    instance = cmd_class()
                    print(f"  {name:<10} {getattr(instance, 'description', 'No description')}")
                except Exception:
                    print(f"  {name:<10} (无法加载描述)")
            print("\n使用 'vibecopilot task <子命令> --help' 获取具体命令的帮助。")


__all__ = ["TaskCommand"]

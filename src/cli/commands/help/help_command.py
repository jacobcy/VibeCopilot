#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帮助命令实现

提供命令行帮助信息
"""

import argparse
import logging
from typing import Any, Dict, List, Optional

from src.cli.commands.base_command import BaseCommand

logger = logging.getLogger(__name__)


class HelpCommand(BaseCommand):
    """帮助命令"""

    def __init__(self):
        super().__init__(
            name="help",
            description="显示帮助信息",
        )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        parser.add_argument("command", nargs="?", help="要查看帮助的命令")

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if hasattr(args, "command") and args.command:
            return self._show_command_help(args.command)
        else:
            return self._show_general_help()

    def _show_general_help(self) -> int:
        """显示通用帮助信息"""
        print("VibeCopilot CLI工具")
        print("\n可用命令:")
        print("  help        显示帮助信息")
        print("  roadmap     路线图管理命令")
        print("  rule        规则管理命令")
        print("  flow        工作流管理命令")

        print("\n用法:")
        print("  vibecopilot <命令> [参数]")
        print("  vibecopilot help [命令]")
        print("  vibecopilot roadmap story S1")
        print("  vibecopilot rule list")
        print("  vibecopilot flow test")

        return 0

    def _show_command_help(self, command_name: str) -> int:
        """显示特定命令的帮助信息"""
        if command_name == "help":
            print("帮助命令")
            print("\n用法:")
            print("  vibecopilot help [命令]")
            print("\n参数:")
            print("  命令        要查看帮助的命令名称")

        elif command_name == "roadmap":
            print("路线图管理命令")
            print("\n用法:")
            print("  vibecopilot roadmap <子命令> [参数]")
            print("\n子命令:")
            print("  story       故事管理")
            print("  epic        史诗管理")
            print("  task        任务管理")
            print("  sync        同步路线图")

        elif command_name == "rule":
            print("规则管理命令")
            print("\n用法:")
            print("  vibecopilot rule <子命令> [参数]")
            print("\n子命令:")
            print("  list        列出所有规则")
            print("  show        显示规则详情")
            print("  create      创建新规则")
            print("  update      更新规则")
            print("  delete      删除规则")

        elif command_name == "flow":
            print("工作流管理命令")
            print("\n用法:")
            print("  vibecopilot flow <子命令> [参数]")
            print("\n子命令:")
            print("  list        列出所有工作流")
            print("  create      从规则创建工作流")
            print("  view        查看工作流详情")
            print("  context     获取工作流上下文")
            print("  export      导出工作流")
            print("\n流程类型命令:")
            print("  story       执行故事流程")
            print("  spec        执行规格流程")
            print("  coding      执行编码流程")
            print("  test        执行测试流程")
            print("  review      执行审查流程")
            print("  commit      执行提交流程")
            print("\n示例:")
            print("  vibecopilot flow list")
            print("  vibecopilot flow create .cursor/rules/flow-rules/test-flow.mdc")
            print("  vibecopilot flow test")
            print('  vibecopilot flow test --stage stage_2 --completed "准备测试环境" "创建测试用例"')

        else:
            logger.error(f"未知命令: {command_name}")
            return self._show_general_help()

        return 0

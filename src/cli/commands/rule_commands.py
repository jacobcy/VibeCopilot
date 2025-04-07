"""
规则命令模块

为CLI提供规则相关的命令实现。
此文件已被拆分为多个模块，导入这些模块。
"""

# 导入规则命令
from src.cli.commands.rule import RuleCommand

__all__ = ["RuleCommand"]

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional, Type

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.cli.command import Command

# 设置日志
logger = logging.getLogger(__name__)


class RuleCommands(Command):
    """规则命令集"""

    @classmethod
    def get_command(cls) -> str:
        return "rules"

    @classmethod
    def get_description(cls) -> str:
        return "规则管理命令集"

    @classmethod
    def get_help(cls) -> str:
        return """
        管理规则，支持创建、查看、修改、删除规则等操作。

        用法:
            rules list                 列出所有规则
            rules show <rule_id>       显示规则详情
            rules create               创建新规则
            rules edit <rule_id>       编辑规则
            rules delete <rule_id>     删除规则
            rules validate <rule_id>   验证规则
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args:
            return parsed

        # 获取子命令
        subcommand = args.pop(0)
        parsed["subcommand"] = subcommand

        # 子命令对应的命令类
        commands = {
            "list": RuleCommand,
            "show": RuleCommand,
            "create": RuleCommand,
            "edit": RuleCommand,
            "delete": RuleCommand,
            "validate": RuleCommand,
            "export": RuleCommand,
            "import": RuleCommand,
        }

        # 检查子命令是否有效
        if subcommand not in commands:
            valid_subcommands = ", ".join(commands.keys())
            raise ValueError(f"无效的子命令: {subcommand}，有效子命令: {valid_subcommands}")

        # 保存子命令实例和参数
        parsed["subcommand_instance"] = commands[subcommand]()
        parsed["subcommand_args"] = [subcommand] + args  # 加上子命令名作为rule_action

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        # 如果没有子命令，显示帮助信息
        if "subcommand" not in parsed_args:
            print(self.get_help())
            print("\n可用的子命令:")
            print("  - list     列出所有规则")
            print("  - show     显示规则详情")
            print("  - create   创建新规则")
            print("  - edit     编辑规则")
            print("  - delete   删除规则")
            print("  - validate 验证规则")
            print("  - export   导出规则")
            print("  - import   导入规则")
            return

        try:
            # 获取子命令实例和参数
            subcommand_instance = parsed_args["subcommand_instance"]
            subcommand_args = parsed_args["subcommand_args"]

            # 解析子命令参数并执行
            parsed_subcommand_args = subcommand_instance.parse_args(subcommand_args)
            subcommand_instance.execute(parsed_subcommand_args)
        except Exception as e:
            print(f"错误: {str(e)}")


def main():
    """主函数"""
    command = RuleCommands()

    # 获取命令行参数（跳过脚本名称）
    args = sys.argv[1:]

    try:
        # 解析参数
        parsed_args = command.parse_args(args)
        # 执行命令
        command.execute(parsed_args)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

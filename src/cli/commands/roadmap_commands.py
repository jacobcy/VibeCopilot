"""
路线图命令模块

为CLI提供路线图相关的命令实现。
此文件已被拆分为多个模块，导入这些模块。
"""

# 导入所有路线图命令
from src.cli.commands.roadmap import (
    CreateCommand,
    RoadmapListCommand,
    StoryCommand,
    SwitchCommand,
    SyncCommand,
    UpdateRoadmapCommand,
)

__all__ = [
    "UpdateRoadmapCommand",
    "SyncCommand",
    "CreateCommand",
    "StoryCommand",
    "SwitchCommand",
    "RoadmapListCommand",
]

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


class RoadmapCommands(Command):
    """路线图命令集"""

    @classmethod
    def get_command(cls) -> str:
        return "roadmap"

    @classmethod
    def get_description(cls) -> str:
        return "路线图管理命令"

    @classmethod
    def get_help(cls) -> str:
        return """
        管理和同步路线图数据，支持多路线图切换

        用法:
            roadmap sync               同步路线图数据
            roadmap switch             切换活动路线图
            roadmap list               列出所有路线图
            roadmap update             更新路线图元素状态
            roadmap plan               创建路线图计划元素
            roadmap story              查看路线图故事
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
            "sync": SyncCommand,
            "switch": SwitchCommand,
            "list": RoadmapListCommand,
            "update": UpdateRoadmapCommand,
            "plan": CreateCommand,
            "story": StoryCommand,
        }

        # 检查子命令是否有效
        if subcommand not in commands:
            valid_subcommands = ", ".join(commands.keys())
            raise ValueError(f"无效的子命令: {subcommand}，有效子命令: {valid_subcommands}")

        # 保存子命令实例和参数
        parsed["subcommand_instance"] = commands[subcommand]()
        parsed["subcommand_args"] = args

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        # 如果没有子命令，显示帮助信息
        if "subcommand" not in parsed_args:
            print(self.get_help())
            print("\n可用的子命令:")
            print("  - sync    同步路线图数据")
            print("  - switch  切换活动路线图")
            print("  - list    列出所有路线图")
            print("  - update  更新路线图元素状态")
            print("  - plan    创建路线图计划元素")
            print("  - story   查看路线图故事")
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
    command = RoadmapCommands()

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

"""
路线图CLI模块

提供命令行接口，用于处理路线图相关命令。
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

# 修改相对导入为绝对导入
from scripts.roadmap_sync.commands import (
    CheckCommand,
    PlanCommand,
    StoryCommand,
    SyncCommand,
    TaskCommand,
    UpdateCommand,
)
from scripts.roadmap_sync.roadmap_processor import RoadmapProcessor

from .connector import GitHubConnector


class RoadmapCLI:
    """路线图命令行接口类"""

    def __init__(self):
        """初始化路线图CLI"""
        self.processor = RoadmapProcessor()
        self.github_sync = None

        # 初始化命令处理器
        self.commands = {
            "check": CheckCommand(self.processor, self.github_sync),
            "update": UpdateCommand(self.processor, self.github_sync),
            "story": StoryCommand(self.processor, self.github_sync),
            "task": TaskCommand(self.processor, self.github_sync),
            "plan": PlanCommand(self.processor, self.github_sync),
            "sync": SyncCommand(self.processor, self.github_sync),
        }

    def setup_github_sync(self, owner: str = None, repo: str = None):
        """
        设置GitHub同步工具

        Args:
            owner: 仓库所有者
            repo: 仓库名称
        """
        from scripts.github_project.api import GitHubClient

        client = GitHubClient()
        self.github_sync = GitHubConnector(
            github_client=client,
            owner=owner or os.environ.get("GITHUB_OWNER"),
            repo=repo or os.environ.get("GITHUB_REPO"),
        )

        # 更新各命令的github_sync属性
        for cmd in self.commands.values():
            cmd.github_sync = self.github_sync

    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        """
        解析命令行参数

        Args:
            args: 命令行参数列表

        Returns:
            argparse.Namespace: 解析后的参数
        """
        parser = argparse.ArgumentParser(description="路线图管理工具")
        subparsers = parser.add_subparsers(dest="command", help="子命令")

        # 为每个命令添加参数解析器
        for name, cmd in self.commands.items():
            cmd.add_parser(subparsers)

        return parser.parse_args(args)

    def run(self, args: List[str] = None) -> Dict[str, Any]:
        """
        运行CLI

        Args:
            args: 命令行参数列表

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        parsed_args = self.parse_args(args)

        if not parsed_args.command:
            return {"success": False, "error": "请提供子命令"}

        if parsed_args.command not in self.commands:
            return {"success": False, "error": f"未知命令: {parsed_args.command}"}

        # 分发命令给相应的处理器
        return self.commands[parsed_args.command].execute(parsed_args)


def main():
    """CLI主入口"""
    cli = RoadmapCLI()
    result = cli.run(sys.argv[1:])

    if result.get("success"):
        if "message" in result:
            print(result["message"])
        else:
            print(result)
    else:
        print(f"错误: {result.get('error', '未知错误')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

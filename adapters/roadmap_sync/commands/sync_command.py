"""
同步命令模块

处理路线图与GitHub项目同步相关命令。
"""

import argparse
import os
from typing import Any, Dict

from scripts.github_project.api import GitHubClient
from scripts.roadmap.commands.command_base import CommandBase
from scripts.roadmap.connector import GitHubConnector


class SyncCommand(CommandBase):
    """同步命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加同步命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("sync", help="同步数据")
        parser.add_argument(
            "--direction", choices=["to-github", "from-github"], required=True, help="同步方向"
        )
        parser.add_argument("--owner", help="GitHub仓库所有者")
        parser.add_argument("--repo", help="GitHub仓库名称")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理同步命令，在Markdown故事和GitHub项目之间同步数据

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            # 使用新的GitHub连接器
            github_connector = self._get_github_connector(args.owner, args.repo)

            if args.direction == "to-github":
                # 直接使用故事数据同步到GitHub
                milestones_count, tasks_count = github_connector.sync_to_github()

                return {
                    "success": True,
                    "message": f"已同步 {milestones_count} 个里程碑和 {tasks_count} 个任务到GitHub",
                    "milestones": milestones_count,
                    "tasks": tasks_count,
                }

            elif args.direction == "from-github":
                # 目前暂不支持从GitHub同步到Markdown的功能
                # 这需要更复杂的实现来处理Markdown文件的更新
                return {"success": False, "error": "暂不支持从GitHub同步到Markdown的功能"}

            else:
                return {"success": False, "error": f"不支持的同步方向: {args.direction}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_github_connector(self, owner=None, repo=None):
        """
        获取GitHub连接器

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            GitHubConnector: GitHub连接器
        """
        from scripts.github_project.api import GitHubClient

        client = GitHubClient()
        return GitHubConnector(
            github_client=client,
            owner=owner or os.environ.get("GITHUB_OWNER"),
            repo=repo or os.environ.get("GITHUB_REPO"),
        )

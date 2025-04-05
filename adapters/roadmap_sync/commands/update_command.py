"""
更新命令模块

处理路线图更新相关命令。
"""

import argparse
from typing import Any, Dict

from scripts.github_roadmap.commands.command_base import CommandBase


class UpdateCommand(CommandBase):
    """更新命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加更新命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("update", help="更新任务或里程碑状态")
        parser.add_argument("--type", choices=["task", "milestone"], required=True, help="更新类型")
        parser.add_argument("--id", help="任务或里程碑ID")
        parser.add_argument("--status", help="新状态")
        parser.add_argument("--assignee", help="任务指派人")
        parser.add_argument("--sync", action="store_true", help="同步到GitHub")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        执行更新命令，更新任务或里程碑状态

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            roadmap = self.processor.read_roadmap()

            if args.type == "task":
                if not args.id:
                    return {"success": False, "error": "未提供任务ID"}

                task = roadmap.get_task_by_id(args.id)
                if not task:
                    return {"success": False, "error": f"未找到任务: {args.id}"}

                # 更新任务状态
                roadmap = self.processor.update_task_status(
                    task_id=args.id, status=args.status, assignee=args.assignee
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_task_to_github(task)

                return {"success": True, "message": f"已更新任务 {args.id} 状态为 {args.status}"}

            elif args.type == "milestone":
                if not args.id:
                    return {"success": False, "error": "未提供里程碑ID"}

                milestone = roadmap.get_milestone_by_id(args.id)
                if not milestone:
                    return {"success": False, "error": f"未找到里程碑: {args.id}"}

                # 更新里程碑状态
                roadmap = self.processor.update_milestone_status(
                    milestone_id=args.id, new_status=args.status
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_milestone_to_github(milestone)

                return {"success": True, "message": f"已更新里程碑 {args.id} 状态为 {args.status}"}

            else:
                return {"success": False, "error": f"不支持的更新类型: {args.type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

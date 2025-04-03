"""
计划命令模块

处理计划相关命令。
"""

import argparse
from typing import Any, Dict

from scripts.github_roadmap.commands.command_base import CommandBase


class PlanCommand(CommandBase):
    """计划命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加计划命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("plan", help="添加项目计划")
        parser.add_argument("--type", choices=["milestone", "phase"], required=True, help="计划类型")
        parser.add_argument("--title", required=True, help="计划标题")
        parser.add_argument("--description", help="计划描述")
        parser.add_argument("--start-date", help="开始日期")
        parser.add_argument("--end-date", help="结束日期")
        parser.add_argument("--sync", action="store_true", help="同步到GitHub")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理计划命令，添加新的项目计划（里程碑）

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            if not args.title:
                return {"success": False, "error": "缺少计划标题"}

            if args.type not in ["milestone", "phase"]:
                return {"success": False, "error": f"不支持的计划类型: {args.type}"}

            # 添加里程碑
            milestone = self.processor.add_milestone(
                name=args.title,
                description=args.description or "",
                start_date=args.start_date,
                end_date=args.end_date,
                status="planned",
            )

            # 同步到GitHub
            if self.github_sync and args.sync:
                self.github_sync.sync_milestone_to_github(milestone)

            return {
                "success": True,
                "message": f"已添加{args.type}计划 {milestone.id}",
                "milestone_id": milestone.id,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

"""
故事命令模块

处理用户故事相关命令。
"""

import argparse
from typing import Any, Dict, Optional

from scripts.github_roadmap.commands.command_base import CommandBase


class StoryCommand(CommandBase):
    """故事命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加故事命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("story", help="管理用户故事/任务")
        parser.add_argument("--type", choices=["task", "milestone"], help="类型")
        parser.add_argument("--title", help="标题")
        parser.add_argument("--description", help="描述")
        parser.add_argument("--milestone", help="所属里程碑ID")
        parser.add_argument("--priority", choices=["P0", "P1", "P2", "P3"], help="优先级")
        parser.add_argument("--assignees", help="指派人，逗号分隔")
        parser.add_argument("--start-date", help="开始日期")
        parser.add_argument("--end-date", help="结束日期")
        parser.add_argument("--sync", action="store_true", help="同步到GitHub")
        parser.add_argument("--list", action="store_true", help="显示所有故事")
        parser.add_argument("--id", help="指定故事ID")
        parser.add_argument("--status", help="按状态筛选故事")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        执行故事命令

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            # 显示当前活跃故事（不带参数的情况）
            if not args.type and not args.title and not args.list and not args.id:
                return self.get_current_active_story()

            # 显示所有故事列表
            if args.list:
                return self.list_stories(status=args.status)

            # 显示特定故事
            if args.id and not args.type:
                return self.get_story_by_id(args.id)

            # 添加新故事/任务的原有逻辑
            if args.type and args.title:
                if args.type == "task":
                    if not args.milestone:
                        return {"success": False, "error": "未指定所属里程碑"}

                    task = self.processor.add_task(
                        title=args.title,
                        description=args.description or "",
                        milestone_id=args.milestone,
                        status="todo",
                        priority=args.priority or "P2",
                        assignees=args.assignees.split(",") if args.assignees else [],
                    )

                    # 同步到GitHub
                    if self.github_sync and args.sync:
                        self.github_sync.sync_task_to_github(task)

                    return {"success": True, "message": f"已添加任务 {task.id}", "task_id": task.id}

                elif args.type == "milestone":
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
                        "message": f"已添加里程碑 {milestone.id}",
                        "milestone_id": milestone.id,
                    }
                else:
                    return {"success": False, "error": f"不支持的类型: {args.type}"}
            else:
                return {"success": False, "error": "参数不完整，请提供type和title参数，或不带参数查看当前故事"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_current_active_story(self) -> Dict[str, Any]:
        """
        获取当前活跃故事信息

        Returns:
            Dict[str, Any]: 当前活跃故事信息
        """
        try:
            # 读取路线图数据
            roadmap = self.processor.read_roadmap()

            # 查找处于进行中的里程碑
            active_milestone = None
            for milestone in roadmap.milestones:
                if milestone.status == "in_progress":
                    active_milestone = milestone
                    break

            if not active_milestone:
                return {"success": False, "message": "没有进行中的里程碑或故事"}

            # 获取该里程碑下的任务
            tasks = roadmap.get_tasks_by_milestone(active_milestone.id)

            # 构建返回结果
            result = {
                "success": True,
                "active_milestone": {
                    "id": active_milestone.id,
                    "name": active_milestone.name,
                    "status": active_milestone.status,
                    "progress": active_milestone.progress,
                    "description": active_milestone.description,
                },
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "assignees": task.assignees,
                        "description": task.description,
                    }
                    for task in tasks
                ],
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.status == "completed"]),
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_stories(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        列出所有故事/里程碑

        Args:
            status: 可选，按状态筛选

        Returns:
            Dict[str, Any]: 故事列表
        """
        try:
            roadmap = self.processor.read_roadmap()

            # 筛选里程碑
            milestones = roadmap.milestones
            if status:
                milestones = [m for m in milestones if m.status == status]

            # 构建返回结果
            result = {
                "success": True,
                "milestones": [
                    {
                        "id": milestone.id,
                        "name": milestone.name,
                        "status": milestone.status,
                        "progress": milestone.progress,
                        "task_count": len(roadmap.get_tasks_by_milestone(milestone.id)),
                    }
                    for milestone in milestones
                ],
                "total": len(milestones),
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_story_by_id(self, story_id: str) -> Dict[str, Any]:
        """
        获取特定故事/里程碑的详细信息

        Args:
            story_id: 故事/里程碑ID

        Returns:
            Dict[str, Any]: 故事详情
        """
        try:
            roadmap = self.processor.read_roadmap()

            # 查找里程碑
            milestone = roadmap.get_milestone_by_id(story_id)
            if not milestone:
                return {"success": False, "error": f"未找到故事/里程碑: {story_id}"}

            # 获取该里程碑下的任务
            tasks = roadmap.get_tasks_by_milestone(milestone.id)

            # 构建返回结果
            result = {
                "success": True,
                "milestone": {
                    "id": milestone.id,
                    "name": milestone.name,
                    "status": milestone.status,
                    "progress": milestone.progress,
                    "description": milestone.description,
                    "start_date": milestone.start_date,
                    "end_date": milestone.end_date,
                },
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "assignees": task.assignees,
                        "description": task.description,
                    }
                    for task in tasks
                ],
                "total_tasks": len(tasks),
                "completed_tasks": len([t for t in tasks if t.status == "completed"]),
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

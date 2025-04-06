"""
路线图更新命令模块

提供更新路线图元素状态的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class UpdateRoadmapCommand(Command):
    """更新路线图元素命令"""

    @classmethod
    def get_command(cls) -> str:
        return "update"

    @classmethod
    def get_description(cls) -> str:
        return "更新路线图中的任务或里程碑状态"

    @classmethod
    def get_help(cls) -> str:
        return """
        更新路线图元素状态

        用法:
            update task T1 in_progress     将任务T1状态更新为进行中
            update milestone M1 completed  将里程碑M1状态更新为已完成

        参数:
            task <id> <status>         更新任务状态
            milestone <id> <status>    更新里程碑状态

        状态:
            任务状态: todo, in_progress, completed
            里程碑状态: planned, in_progress, completed

        选项:
            --sync                     同步到GitHub
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if len(args) < 3:
            raise ValueError("参数不足。格式: update [task|milestone] <id> <status>")

        element_type = args.pop(0)
        if element_type in ["task", "milestone"]:
            parsed["element_type"] = element_type
        else:
            raise ValueError(f"未知的元素类型: {element_type}")

        # 解析元素ID
        parsed["element_id"] = args.pop(0)

        # 解析状态
        parsed["status"] = args.pop(0)

        # 解析--sync选项
        if "--sync" in args:
            parsed["sync_github"] = True
            args.remove("--sync")
        else:
            parsed["sync_github"] = False

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        try:
            element_id = parsed_args.get("element_id")
            element_type = parsed_args.get("element_type")
            status = parsed_args.get("status")
            sync_github = parsed_args.get("sync_github", False)

            # 验证状态值是否有效
            valid_task_statuses = ["todo", "in_progress", "completed"]
            valid_milestone_statuses = ["planned", "in_progress", "completed"]

            if element_type == "task" and status not in valid_task_statuses:
                print(f"无效的任务状态: {status}，有效值为: {', '.join(valid_task_statuses)}")
                return

            if element_type == "milestone" and status not in valid_milestone_statuses:
                print(f"无效的里程碑状态: {status}，有效值为: {', '.join(valid_milestone_statuses)}")
                return

            # 更新元素状态
            result = service.update_roadmap_status(
                element_id=element_id, element_type=element_type, status=status
            )

            if not result.get("success", False):
                print(f"更新失败: {result.get('error', '未知错误')}")
                return

            print(f"成功更新{element_type} {element_id} 的状态为 {status}")

            # 如果需要同步到GitHub
            if sync_github:
                print("正在同步到GitHub...")
                github_result = service.sync_to_github()

                if github_result.get("success", False):
                    print("已成功同步到GitHub")
                else:
                    print(f"GitHub同步失败: {github_result.get('error', '未知错误')}")
        except Exception as e:
            print(f"错误: {str(e)}")

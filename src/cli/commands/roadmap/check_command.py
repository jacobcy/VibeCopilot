"""
路线图检查命令模块

提供检查路线图状态的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class CheckRoadmapCommand(Command):
    """检查路线图状态命令"""

    @classmethod
    def get_command(cls) -> str:
        return "check"

    @classmethod
    def get_description(cls) -> str:
        return "检查路线图或特定元素的状态"

    @classmethod
    def get_help(cls) -> str:
        return """
        检查路线图状态

        用法:
            check roadmap              检查整个路线图状态
            check milestone M1         检查里程碑M1的状态
            check milestone M1 --update 检查并更新里程碑M1的状态
            check task T1              检查任务T1的状态

        参数:
            roadmap                    检查整个路线图
            milestone <id>             检查特定里程碑
            task <id>                  检查特定任务

        选项:
            --update                   更新状态（计算进度并更新）
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args:
            parsed["check_type"] = "roadmap"
            return parsed

        check_type = args.pop(0)
        if check_type in ["roadmap", "milestone", "task"]:
            parsed["check_type"] = check_type
        else:
            raise ValueError(f"未知的检查类型: {check_type}")

        # 解析资源ID
        if check_type in ["milestone", "task"] and args:
            parsed["resource_id"] = args.pop(0)

        # 解析--update选项
        if "--update" in args:
            parsed["update"] = True
            args.remove("--update")
        else:
            parsed["update"] = False

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        try:
            check_type = parsed_args.get("check_type", "roadmap")
            resource_id = parsed_args.get("resource_id")
            update = parsed_args.get("update", False)

            # 执行检查
            result = service.check_roadmap_status(
                check_type=check_type, element_id=resource_id, roadmap_id=None  # 使用活跃路线图
            )

            if not result.get("success", False):
                print(f"错误: {result.get('error', '检查失败')}")
                return

            # 如果需要更新状态
            if update and check_type in ["milestone", "task"] and resource_id:
                update_result = service.update_roadmap(roadmap_id=None)  # 使用活跃路线图
                if update_result.get("success", False):
                    print(f"已更新{check_type} {resource_id}的状态")
                    # 重新获取状态
                    result = service.check_roadmap_status(
                        check_type=check_type, element_id=resource_id
                    )
                else:
                    print(f"状态更新失败: {update_result.get('error', '未知错误')}")

            # 格式化输出
            self._format_output(result.get("status", {}), check_type)
        except Exception as e:
            print(f"错误: {str(e)}")

    def _format_output(self, result: Dict, check_type: str) -> None:
        """格式化输出结果"""
        if check_type == "roadmap":
            print("\n=== 路线图状态 ===")
            print(f"里程碑数量: {result.get('milestones', 0)}")
            print(f"任务数量: {result.get('tasks', 0)}")

            task_status = result.get("task_status", {})
            print(
                f"任务状态: 待办({task_status.get('todo', 0)}), "
                f"进行中({task_status.get('in_progress', 0)}), "
                f"已完成({task_status.get('completed', 0)})"
            )

            active_milestone = result.get("active_milestone")
            if active_milestone:
                milestone_info = result.get("milestone_status", {}).get(active_milestone, {})
                print(f"\n当前活跃里程碑: {active_milestone} - {milestone_info.get('name')}")
                print(f"进度: {milestone_info.get('progress')}% ({milestone_info.get('status')})")
                print(f"任务数: {milestone_info.get('tasks', 0)}")

        elif check_type == "milestone":
            print(f"\n=== 里程碑: {result.get('milestone_id')} - {result.get('name')} ===")
            print(f"状态: {result.get('status')}")
            print(f"进度: {result.get('progress')}%")
            print(f"任务总数: {result.get('tasks', 0)}")

            task_status = result.get("task_status", {})
            print(
                f"任务状态: 待办({task_status.get('todo', 0)}), "
                f"进行中({task_status.get('in_progress', 0)}), "
                f"已完成({task_status.get('completed', 0)})"
            )

        elif check_type == "task":
            print(f"\n=== 任务: {result.get('task_id')} - {result.get('title')} ===")
            print(f"状态: {result.get('status')}")
            print(f"优先级: {result.get('priority', 'P2')}")

            milestone = result.get("milestone")
            if milestone:
                print(f"所属里程碑: {milestone.get('id')} - {milestone.get('name')}")
                print(f"里程碑状态: {milestone.get('status')}")

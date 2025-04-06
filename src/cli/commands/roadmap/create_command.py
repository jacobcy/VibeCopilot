"""
路线图计划命令模块

提供创建新的里程碑、故事或任务的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class CreateCommand(Command):
    """计划创建命令"""

    @classmethod
    def get_command(cls) -> str:
        return "create"

    @classmethod
    def get_description(cls) -> str:
        return "创建新的里程碑、故事或任务"

    @classmethod
    def get_help(cls) -> str:
        return """
        创建路线图计划元素

        用法:
            create milestone "发布1.0版本"          创建新的里程碑
            create story "登录功能" -m M1          在里程碑M1下创建新的故事
            create task "设计用户界面" -m M1 -p P1  创建新的高优先级任务

        参数:
            milestone <标题>            创建新的里程碑
            story <标题>                创建新的故事
            task <标题>                 创建新的任务

        选项:
            -m, --milestone <id>       指定所属里程碑ID
            -p, --priority <级别>      指定优先级(P0, P1, P2, P3)
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        if not args:
            raise ValueError("参数不足。需要指定计划类型和标题")

        # 解析计划类型
        plan_type = args.pop(0)
        if plan_type in ["milestone", "story", "task"]:
            parsed["plan_type"] = plan_type
        else:
            raise ValueError(f"未知的计划类型: {plan_type}")

        # 解析标题（处理包含空格的标题）
        if not args:
            raise ValueError("缺少标题")

        title = args.pop(0)
        if title.startswith('"') and title.endswith('"'):
            parsed["title"] = title[1:-1]
        else:
            # 如果标题没有用引号包围，尝试拼接
            title_parts = [title]
            while args and not (args[0].startswith("-") or args[0].startswith("--")):
                title_parts.append(args.pop(0))
            parsed["title"] = " ".join(title_parts)

        # 解析选项
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["-m", "--milestone"]:
                if i + 1 < len(args):
                    parsed["milestone_id"] = args[i + 1]
                    i += 2
                else:
                    raise ValueError("缺少里程碑ID")
            elif arg in ["-p", "--priority"]:
                if i + 1 < len(args):
                    parsed["priority"] = args[i + 1]
                    i += 2
                else:
                    raise ValueError("缺少优先级")
            else:
                i += 1

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        try:
            plan_type = parsed_args.get("plan_type")
            title = parsed_args.get("title")
            milestone_id = parsed_args.get("milestone_id")
            priority = parsed_args.get("priority", "P2")

            # 获取当前路线图信息
            roadmap_info = service.get_roadmap_info()
            if not roadmap_info.get("success", False):
                print(f"错误: {roadmap_info.get('error', '无法获取路线图信息')}")
                return

            roadmap_id = roadmap_info.get("roadmap", {}).get("id")

            # 更新路线图，添加新元素
            if plan_type == "milestone":
                result = service.update_roadmap_status(
                    element_id="M"
                    + str(len(roadmap_info.get("stats", {}).get("milestones_count", 0)) + 1),
                    element_type="milestone",
                    status="planned",
                    roadmap_id=roadmap_id,
                )
                created_id = result.get("element", {}).get("id")
            elif plan_type == "story":
                if not milestone_id:
                    print("错误: 创建故事需要指定里程碑ID")
                    return

                result = service.update_roadmap_status(
                    element_id="S"
                    + str(len(roadmap_info.get("stats", {}).get("stories_count", 0)) + 1),
                    element_type="story",
                    status="planned",
                    roadmap_id=roadmap_id,
                )
                result["element"]["title"] = title
                result["element"]["milestone_id"] = milestone_id
                created_id = result.get("element", {}).get("id")
            elif plan_type == "task":
                if not milestone_id:
                    print("错误: 创建任务需要指定里程碑ID")
                    return

                result = service.update_roadmap_status(
                    element_id="T"
                    + str(len(roadmap_info.get("stats", {}).get("tasks_count", 0)) + 1),
                    element_type="task",
                    status="todo",
                    roadmap_id=roadmap_id,
                )
                result["element"]["title"] = title
                result["element"]["milestone_id"] = milestone_id
                result["element"]["priority"] = priority
                created_id = result.get("element", {}).get("id")

            # 输出结果
            if result.get("success", False):
                print(f"成功创建{plan_type}: {created_id} - {title}")

                if plan_type in ["story", "task"] and milestone_id:
                    print(f"所属里程碑: {milestone_id}")

                if plan_type == "task" and priority:
                    print(f"优先级: {priority}")
            else:
                print(f"创建失败: {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"错误: {str(e)}")

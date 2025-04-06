"""
路线图故事命令模块

提供查看路线图中故事信息的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class StoryCommand(Command):
    """故事查看命令"""

    @classmethod
    def get_command(cls) -> str:
        return "story"

    @classmethod
    def get_description(cls) -> str:
        return "查看路线图中的故事信息"

    @classmethod
    def get_help(cls) -> str:
        return """
        查看故事信息

        用法:
            story                      列出所有故事
            story S1                   查看特定故事详情
            story -m M1                查看里程碑M1下的所有故事

        参数:
            <story_id>                 故事ID，例如S1

        选项:
            -m, --milestone <id>       指定里程碑ID
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        # 处理选项
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ["-m", "--milestone"]:
                if i + 1 < len(args):
                    parsed["milestone_id"] = args[i + 1]
                    i += 2
                else:
                    raise ValueError("缺少里程碑ID参数")
            else:
                if "story_id" not in parsed and not arg.startswith("-"):
                    parsed["story_id"] = arg
                i += 1

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        try:
            result = service.get_roadmap_info()
            stories = []

            if "story_id" in parsed_args:
                # 获取单个故事详情
                story_id = parsed_args.get("story_id")
                stories = [
                    s
                    for s in result.get("roadmap", {}).get("stories", [])
                    if s.get("id") == story_id
                ]
                if not stories:
                    print(f"错误: 未找到故事 {story_id}")
                    return
                result = stories[0]
            elif "milestone_id" in parsed_args:
                # 获取里程碑下的所有故事
                milestone_id = parsed_args.get("milestone_id")
                milestone = service.check_roadmap_status("milestone", milestone_id)
                stories = [
                    s
                    for s in result.get("roadmap", {}).get("stories", [])
                    if s.get("milestone_id") == milestone_id
                ]
                result = {"milestone": milestone.get("status", {}), "stories": stories}
            else:
                # 获取所有故事
                stories = result.get("roadmap", {}).get("stories", [])
                result = {"stories": stories}

            # 格式化输出
            self._format_output(result, parsed_args)
        except Exception as e:
            print(f"错误: {str(e)}")

    def _format_output(self, result: Dict, parsed_args: Dict) -> None:
        """格式化输出结果"""
        if "story_id" in parsed_args:
            # 显示单个故事详情
            story_id = parsed_args.get("story_id")
            print(f"\n=== 故事: {story_id} - {result.get('title')} ===")
            print(f"状态: {result.get('status')}")
            print(f"进度: {result.get('progress')}%")

            if result.get("description"):
                print(f"\n描述:\n{result.get('description')}")

            tasks = result.get("tasks", [])
            if tasks:
                print("\n相关任务:")
                for task in tasks:
                    print(f"  - {task.get('id')}: {task.get('title')} [{task.get('status')}]")

        elif "milestone_id" in parsed_args:
            # 显示里程碑下的所有故事
            milestone = result.get("milestone", {})
            print(f"\n=== 里程碑: {milestone.get('id')} - {milestone.get('name')} ===")
            print(f"状态: {milestone.get('status')}")
            print(f"进度: {milestone.get('progress')}%")

            stories = result.get("stories", [])
            if stories:
                print("\n相关故事:")
                for story in stories:
                    print(
                        f"  - {story.get('id')}: {story.get('title')} "
                        + f"[{story.get('status')}] ({story.get('progress')}%)"
                    )
            else:
                print("\n该里程碑下没有故事")

        else:
            # 显示所有故事
            stories = result.get("stories", [])
            print("\n=== 所有故事 ===")

            if stories:
                for story in stories:
                    print(
                        f"  - {story.get('id')}: {story.get('title')} "
                        + f"[{story.get('status')}] ({story.get('progress')}%)"
                    )
            else:
                print("没有找到故事")

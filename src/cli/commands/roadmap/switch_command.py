"""
路线图切换命令模块

提供切换当前活跃路线图的命令实现
"""

from typing import Dict, List

from src.cli.command import Command
from src.roadmap import RoadmapService


class SwitchCommand(Command):
    """路线图切换命令"""

    @classmethod
    def get_command(cls) -> str:
        return "switch"

    @classmethod
    def get_description(cls) -> str:
        return "切换当前活跃路线图"

    @classmethod
    def get_help(cls) -> str:
        return """
        切换当前活跃路线图

        用法:
            switch                     显示当前活跃路线图
            switch <roadmap_id>        切换到指定ID的路线图

        参数:
            <roadmap_id>               路线图ID，例如 roadmap_123
        """

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        # 如果有参数，则是指定要切换的路线图ID
        if args:
            parsed["roadmap_id"] = args[0]

        return parsed

    def execute(self, parsed_args: Dict) -> None:
        """执行命令"""
        service = RoadmapService()

        try:
            # 如果指定了路线图ID，则切换
            if "roadmap_id" in parsed_args:
                roadmap_id = parsed_args.get("roadmap_id")
                result = service.switch_roadmap(roadmap_id)

                if result.get("success", False):
                    print(f"已切换到路线图: {result.get('roadmap_name')} (ID: {result.get('roadmap_id')})")
                else:
                    print(f"切换路线图失败: {result.get('error', '未知错误')}")
            else:
                # 显示当前活跃路线图
                roadmaps = service.list_roadmaps()

                if not roadmaps.get("success", False):
                    print("获取路线图列表失败")
                    return

                active_id = roadmaps.get("active_id")
                active_roadmap = None

                for roadmap in roadmaps.get("roadmaps", []):
                    if roadmap.get("id") == active_id:
                        active_roadmap = roadmap
                        break

                if active_roadmap:
                    print(f"当前活跃路线图: {active_roadmap.get('name')} (ID: {active_id})")
                else:
                    print("未找到活跃路线图")

                print("\n可用路线图:")
                for roadmap in roadmaps.get("roadmaps", []):
                    status = "活跃" if roadmap.get("id") == active_id else ""
                    print(f"  - {roadmap.get('name')} (ID: {roadmap.get('id')}) {status}")
        except Exception as e:
            print(f"错误: {str(e)}")

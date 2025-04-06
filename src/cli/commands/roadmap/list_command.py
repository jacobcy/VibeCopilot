import argparse
import logging
import os
import sys
from typing import List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.cli.command import Command
from src.db.service import DatabaseService

# 设置日志
logger = logging.getLogger(__name__)


class RoadmapListCommand(Command):
    """路线图列表命令"""

    @property
    def name(self) -> str:
        return "list"

    @property
    def description(self) -> str:
        return "列出所有路线图"

    @property
    def help(self) -> str:
        return "显示所有可用的路线图及其详细信息"

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--details", "-d", action="store_true", help="显示详细信息")
        parser.add_argument(
            "--format", "-f", choices=["table", "json"], default="table", help="输出格式"
        )
        parser.add_argument("--roadmap", "-r", type=str, help="获取特定路线图的详细信息")

    def run(self, args: argparse.Namespace) -> int:
        # 获取数据库路径
        db_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "roadmap.db")

        # 初始化数据库服务
        db_service = DatabaseService(db_path)

        # 如果指定了特定路线图ID
        if args.roadmap:
            roadmap = db_service.get_roadmap(args.roadmap)
            if not roadmap:
                print(f"错误: 找不到ID为 {args.roadmap} 的路线图")
                return 1

            print(f"路线图: {roadmap['name']} (ID: {roadmap['id']})")
            print(f"描述: {roadmap['description']}")
            print(f"状态: {roadmap['status']}")
            print(f"活动: {'是' if roadmap['is_active'] else '否'}")
            print(f"创建时间: {roadmap['created_at']}")
            print(f"最后更新: {roadmap['updated_at']}")

            # 获取该路线图下的内容
            epics = db_service.list_epics(roadmap["id"])
            milestones = db_service.list_milestones(roadmap["id"])
            stories = db_service.list_stories(roadmap["id"])
            tasks = db_service.list_tasks(roadmap["id"])

            print("\n路线图内容:")
            print(f"  - Epic数量: {len(epics)}")
            print(f"  - 里程碑数量: {len(milestones)}")
            print(f"  - 故事数量: {len(stories)}")
            print(f"  - 任务数量: {len(tasks)}")

            # 如果需要显示详细信息
            if args.details:
                if epics:
                    print("\nEpics:")
                    for epic in epics:
                        print(f"  - {epic['name']} (ID: {epic['id']}, 状态: {epic['status']})")

                if milestones:
                    print("\n里程碑:")
                    for milestone in milestones:
                        print(
                            f"  - {milestone['name']} (ID: {milestone['id']}, 状态: {milestone['status']})"
                        )

                if args.format == "json":
                    import json

                    roadmap_data = {
                        "roadmap": roadmap,
                        "epics": epics,
                        "milestones": milestones,
                        "stories": stories,
                        "tasks": tasks,
                    }
                    print("\nJSON数据:")
                    print(json.dumps(roadmap_data, indent=2, ensure_ascii=False))

            return 0

        # 否则列出所有路线图
        roadmaps = db_service.list_roadmaps()

        if not roadmaps:
            print("没有找到任何路线图")
            return 1

        # 获取当前活动路线图
        active_roadmap = db_service.get_active_roadmap()
        active_id = active_roadmap["id"] if active_roadmap else None

        if args.format == "table":
            # 表格格式显示
            print("\n可用的路线图:")
            print("=" * 80)
            print(f"{'ID':<10} | {'名称':<20} | {'状态':<10} | {'活动':<5} | {'描述':<30}")
            print("-" * 80)

            for roadmap in roadmaps:
                is_active = "是" if roadmap["is_active"] else "否"
                # 截断过长的描述
                description = (
                    roadmap["description"][:27] + "..."
                    if len(roadmap["description"]) > 30
                    else roadmap["description"]
                )
                print(
                    f"{roadmap['id']:<10} | {roadmap['name']:<20} | {roadmap['status']:<10} | {is_active:<5} | {description:<30}"
                )

            print("=" * 80)

            if active_id:
                print(f"\n当前活动路线图: {active_roadmap['name']} (ID: {active_id})")

        elif args.format == "json":
            # JSON格式显示
            import json

            result = {"roadmaps": roadmaps, "active_roadmap": active_id}
            print(json.dumps(result, indent=2, ensure_ascii=False))

        # 如果需要详细信息
        if args.details and args.format != "json":
            print("\n路线图统计:")
            for roadmap in roadmaps:
                epics = db_service.list_epics(roadmap["id"])
                milestones = db_service.list_milestones(roadmap["id"])
                stories = db_service.list_stories(roadmap["id"])
                tasks = db_service.list_tasks(roadmap["id"])

                print(f"\n{roadmap['name']} (ID: {roadmap['id']}):")
                print(f"  - Epic数量: {len(epics)}")
                print(f"  - 里程碑数量: {len(milestones)}")
                print(f"  - 故事数量: {len(stories)}")
                print(f"  - 任务数量: {len(tasks)}")

        print("\n提示:")
        print("- 使用 'roadmap switch <ID>' 切换活动路线图")
        print("- 使用 'roadmap list --roadmap <ID> --details' 查看特定路线图的详细信息")

        return 0


def main():
    """主函数"""
    command = RoadmapListCommand()
    parser = argparse.ArgumentParser(description=command.description)
    command.configure_parser(parser)
    args = parser.parse_args()
    return command.run(args)


if __name__ == "__main__":
    sys.exit(main())

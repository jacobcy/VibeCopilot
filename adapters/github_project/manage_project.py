#!/usr/bin/env python
"""
GitHub项目管理脚本

这个脚本提供了一个交互式界面，用于管理GitHub项目和路线图。
它是基于命令处理系统实现的，展示了如何在实际应用中使用命令系统。
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 移到顶部
from src.cursor.command_handler import CursorCommandHandler

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_environment():
    """设置环境变量"""
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["ROADMAP_FILE"] = str(project_root / ".ai/roadmap/current.yaml")
    return {"PROJECT_ROOT": str(project_root), "ROADMAP_FILE": os.environ["ROADMAP_FILE"]}


def format_output(result):
    """格式化输出结果"""
    return json.dumps(result, indent=2, ensure_ascii=False)


class GitHubManager:
    """GitHub项目管理器"""

    def __init__(self):
        """初始化项目管理器"""
        # 设置环境
        self.env = setup_environment()
        print(f"项目根目录: {self.env['PROJECT_ROOT']}")

        # 初始化命令处理器
        self.cmd_handler = CursorCommandHandler()

    def get_available_commands(self):
        """获取可用命令列表"""
        return self.cmd_handler.get_available_commands()

    def get_command_help(self, command_name):
        """获取命令帮助信息"""
        return self.cmd_handler.get_command_help(command_name)

    def execute_command(self, command_str):
        """执行命令"""
        return self.cmd_handler.handle_command(command_str)

    def check_roadmap(self):
        """检查路线图状态"""
        return self.execute_command("/github --action=check --type=roadmap")

    def list_tasks(self, milestone="M2"):
        """列出特定里程碑的任务"""
        return self.execute_command(f"/github --action=list --type=task --milestone={milestone}")

    def update_task_status(self, task_id, status, sync=True):
        """更新任务状态"""
        sync_str = "true" if sync else "false"
        return self.execute_command(f"/github --action=update --type=task --id={task_id} --status={status} --sync={sync_str}")

    def create_task(self, title, milestone, priority="P1", description=None):
        """创建新任务"""
        cmd = f'/github --action=story --type=task --title="{title}" --milestone={milestone} --priority={priority}'
        if description:
            cmd += f' --desc="{description}"'
        return self.execute_command(cmd)

    def sync_data(self, direction="from-github"):
        """同步数据"""
        return self.execute_command(f"/github --action=sync --direction={direction}")


def run_interactive():
    """运行交互式模式"""
    manager = GitHubManager()

    print("\n===== GitHub项目管理 =====\n")
    print("可用命令:")
    for cmd in manager.get_available_commands():
        print(f"  - {cmd['name']}: {cmd['description']}")

    print("\n1. 查看路线图状态")
    result = manager.check_roadmap()
    if result["success"]:
        data = result["data"]["result"]
        print(f"  路线图包含 {data['milestones']} 个里程碑和 {data['tasks']} 个任务")
        print(f"  当前活跃里程碑: {data['active_milestone']}")

    print("\n2. 查看当前里程碑任务")
    active_milestone = result["data"]["result"]["active_milestone"] if result["success"] else "M2"
    list_result = manager.list_tasks(active_milestone)
    if list_result["success"]:
        tasks = list_result["data"]["result"]["items"]
        print(f"  {active_milestone} 包含 {len(tasks)} 个任务:")
        for task in tasks:
            print(f"    - {task['id']}: {task['title']} ({task['status']})")

    # 选择一个任务进行更新
    task_id = None
    if list_result["success"] and tasks:
        print("\n3. 选择一个任务更新状态")

        # 列出未完成的任务
        todo_tasks = [t for t in tasks if t["status"] != "completed"]
        if todo_tasks:
            for i, task in enumerate(todo_tasks):
                print(f"  {i+1}. {task['id']}: {task['title']} ({task['status']})")

            try:
                choice = int(input("\n请选择要更新的任务编号 (输入0跳过): "))
                if 1 <= choice <= len(todo_tasks):
                    task_id = todo_tasks[choice - 1]["id"]
                    new_status = input(f"请输入新状态 (completed/in_progress/blocked): ")
                    if new_status:
                        update_result = manager.update_task_status(task_id, new_status)
                        if update_result["success"]:
                            print(f"  ✅ {update_result['data']['result']['message']}")
                        else:
                            print(f"  ❌ 更新失败: {update_result['error']}")
            except (ValueError, IndexError):
                print("  已跳过任务更新")
        else:
            print("  没有待完成的任务")

    # 创建新任务
    print("\n4. 是否创建新任务? (y/n)")
    if input().lower() == "y":
        title = input("  任务标题: ")
        milestone = input(f"  所属里程碑 (默认 {active_milestone}): ") or active_milestone
        priority = input("  优先级 (P0/P1/P2, 默认 P1): ") or "P1"
        description = input("  任务描述 (可选): ")

        if title:
            create_result = manager.create_task(title, milestone, priority, description)
            if create_result["success"]:
                print(f"  ✅ {create_result['data']['result']['message']}")
            else:
                print(f"  ❌ 创建失败: {create_result['error']}")

    # 执行同步
    print("\n5. 是否同步数据到GitHub? (y/n)")
    if input().lower() == "y":
        sync_result = manager.sync_data("to-github")
        if sync_result["success"]:
            print(f"  ✅ {sync_result['data']['result']['message']}")
            print(f"  创建: {sync_result['data']['result']['created']}, 更新: {sync_result['data']['result']['updated']}")
        else:
            print(f"  ❌ 同步失败: {sync_result['error']}")

    print("\n项目管理操作完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GitHub项目管理工具")
    parser.add_argument("--check", action="store_true", help="检查路线图状态")
    parser.add_argument("--list", metavar="MILESTONE", help="列出指定里程碑的任务")
    parser.add_argument("--update", nargs=2, metavar=("TASK_ID", "STATUS"), help="更新任务状态")
    parser.add_argument("--create", nargs=4, metavar=("TITLE", "MILESTONE", "PRIORITY", "DESCRIPTION"), help="创建新任务")
    parser.add_argument("--sync", choices=["to-github", "from-github"], help="同步数据")
    parser.add_argument("--interactive", action="store_true", help="交互式模式")

    args = parser.parse_args()

    # 初始化管理器
    manager = GitHubManager()

    # 解析命令行参数
    if args.check:
        result = manager.check_roadmap()
        print(format_output(result))
    elif args.list:
        result = manager.list_tasks(args.list)
        print(format_output(result))
    elif args.update:
        result = manager.update_task_status(args.update[0], args.update[1])
        print(format_output(result))
    elif args.create:
        result = manager.create_task(*args.create)
        print(format_output(result))
    elif args.sync:
        result = manager.sync_data(args.sync)
        print(format_output(result))
    elif args.interactive or not any(vars(args).values()):
        run_interactive()
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback

        traceback.print_exc()

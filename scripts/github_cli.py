#!/usr/bin/env python
"""
GitHub CLI工具

提供命令行接口，用于执行GitHub相关操作。
简化与GitHub项目管理系统交互的过程。
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cursor.command_handler import CursorCommandHandler


def setup_environment():
    """设置环境变量"""
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["ROADMAP_FILE"] = str(project_root / ".ai/roadmap/current.yaml")


def main():
    """主函数"""
    # 设置环境
    setup_environment()

    # 初始化命令处理器
    cmd_handler = CursorCommandHandler()

    # 如果没有参数，打印帮助信息
    if len(sys.argv) == 1:
        print("GitHub命令行工具")
        print("\n可用命令:")
        for cmd in cmd_handler.get_available_commands():
            print(f"  - {cmd['name']}: {cmd['description']}")
        print("\nGitHub命令帮助:")
        help_result = cmd_handler.get_command_help("github")
        if isinstance(help_result, dict) and help_result.get("success"):
            print(help_result["data"])
        return 0

    # 构建命令字符串
    command_str = "/github " + " ".join(sys.argv[1:])

    # 执行命令
    result = cmd_handler.handle_command(command_str)

    # 输出结果
    if result["success"]:
        if "result" in result["data"]:
            # 格式化输出消息
            message = result["data"]["result"].get("message", "操作成功")
            print(f"✅ {message}")

            # 输出数据细节
            if "items" in result["data"]["result"]:
                items = result["data"]["result"]["items"]
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            print(
                                f"  - {item.get('id', 'unknown')}: {item.get('title', 'unknown')} ({item.get('status', 'unknown')})"
                            )
                        else:
                            print(f"  - {item}")
            elif "milestones" in result["data"]["result"]:
                data = result["data"]["result"]
                print(f"  里程碑数量: {data['milestones']}")
                print(f"  任务数量: {data['tasks']}")
                print(f"  活跃里程碑: {data.get('active_milestone', 'unknown')}")
                print(f"  完成任务: {data.get('completed_tasks', 0)}")
        else:
            print(f"✅ 操作成功: {result['data']}")
        return 0
    else:
        print(f"❌ 错误: {result['error']}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

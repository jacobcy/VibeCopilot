"""
命令系统测试脚本

测试VibeCopilot命令处理系统的功能
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cursor.command_handler import CursorCommandHandler


def test_github_command():
    """测试GitHub命令"""
    print("\n==== 测试GitHub命令 ====")

    # 初始化命令处理器
    cmd_handler = CursorCommandHandler()

    # 测试检查命令
    print("\n1. 测试路线图检查命令")
    result = cmd_handler.handle_command("/github --action=check --type=roadmap")
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试更新命令
    print("\n2. 测试任务更新命令")
    result = cmd_handler.handle_command(
        "/github --action=update --type=task --id=T2.1 --status=completed --sync=true"
    )
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试列表命令
    print("\n3. 测试任务列表命令")
    result = cmd_handler.handle_command("/github --action=list --type=task --milestone=M2")
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试同步命令
    print("\n4. 测试同步命令")
    result = cmd_handler.handle_command("/github --action=sync --direction=from-github")
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试帮助命令
    print("\n5. 测试命令帮助")
    result = cmd_handler.get_command_help("github")
    print(f"GitHub命令帮助: {json.dumps(result, indent=2)}")


def test_available_commands():
    """测试获取可用命令列表"""
    print("\n==== 测试获取可用命令 ====")

    # 初始化命令处理器
    cmd_handler = CursorCommandHandler()

    # 获取可用命令
    commands = cmd_handler.get_available_commands()
    print(f"可用命令: {json.dumps(commands, indent=2)}")


def test_error_handling():
    """测试错误处理"""
    print("\n==== 测试错误处理 ====")

    # 初始化命令处理器
    cmd_handler = CursorCommandHandler()

    # 测试未知命令
    print("\n1. 测试未知命令")
    result = cmd_handler.handle_command("/unknown --param=value")
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试缺少参数
    print("\n2. 测试缺少必需参数")
    result = cmd_handler.handle_command("/github --type=roadmap")  # 缺少action参数
    print(f"结果: {json.dumps(result, indent=2)}")

    # 测试无效参数值
    print("\n3. 测试无效参数值")
    result = cmd_handler.handle_command("/github --action=check --type=invalid")
    print(f"结果: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)

    # 运行测试
    test_github_command()
    test_available_commands()
    test_error_handling()

    print("\n所有测试完成！")

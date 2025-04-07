#!/usr/bin/env python
"""
测试GitHub命令处理系统

这个脚本演示了如何使用命令处理系统来执行GitHub相关操作。
"""

import json
import os
import sys
from pathlib import Path

# 移到顶部
from src.cursor.command_handler import CursorCommandHandler

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def format_output(result):
    """格式化输出结果"""
    return json.dumps(result, indent=2, ensure_ascii=False)


def test_github_commands():
    """测试GitHub命令"""
    print("\n===== GitHub命令测试 =====\n")

    # 初始化命令处理器
    cmd_handler = CursorCommandHandler()

    # 显示GitHub命令帮助
    print("【1】获取GitHub命令帮助：")
    help_result = cmd_handler.get_command_help("github")
    print(f"结果: {format_output(help_result)}")
    print("\n" + "-" * 80)

    # 测试检查路线图
    print("\n【2】检查路线图：")
    check_result = cmd_handler.handle_command("/github --action=check --type=roadmap")
    print(f"结果: {format_output(check_result)}")
    print("\n" + "-" * 80)

    # 测试列出任务
    print("\n【3】查看里程碑任务：")
    list_result = cmd_handler.handle_command("/github --action=list --type=task --milestone=M2")
    print(f"结果: {format_output(list_result)}")
    print("\n" + "-" * 80)

    # 测试更新任务状态
    print("\n【4】更新任务状态：")
    update_result = cmd_handler.handle_command("/github --action=update --type=task --id=T2.1 --status=completed --sync=true")
    print(f"结果: {format_output(update_result)}")
    print("\n" + "-" * 80)

    # 测试添加新任务
    print("\n【5】创建新任务：")
    story_result = cmd_handler.handle_command('/github --action=story --type=task --title="实现命令系统" --milestone=M2 --priority=P0')
    print(f"结果: {format_output(story_result)}")
    print("\n" + "-" * 80)

    # 测试同步操作
    print("\n【6】同步数据：")
    sync_result = cmd_handler.handle_command("/github --action=sync --direction=from-github")
    print(f"结果: {format_output(sync_result)}")
    print("\n" + "-" * 80)


if __name__ == "__main__":
    try:
        test_github_commands()
        print("\n✅ 测试完成！\n")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}\n")
        import traceback

        traceback.print_exc()

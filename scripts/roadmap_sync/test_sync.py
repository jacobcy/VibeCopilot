#!/usr/bin/env python
"""
测试GitHub同步功能

此脚本用于测试从Markdown故事到GitHub的同步功能。
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.github_project.api import GitHubClient
from scripts.roadmap.connector import GitHubConnector
from scripts.roadmap.markdown_parser import read_all_stories


def test_read_stories():
    """测试读取所有故事"""
    stories = read_all_stories()
    print("== 读取到的故事数据 ==")
    print(f"找到 {len(stories.get('milestones', []))} 个里程碑")
    for milestone in stories.get("milestones", []):
        print(f"- [{milestone.get('id')}] {milestone.get('name')}: {milestone.get('progress')}% 完成")
        if milestone.get("end_date"):
            print(f"  到期日期: {milestone.get('end_date')}")

    print(f"\n找到 {len(stories.get('tasks', []))} 个任务")
    for task in stories.get("tasks", []):
        print(f"- [{task.get('id')}] {task.get('title')} (状态: {task.get('status')})")
        if task.get("epic"):
            print(f"  所属Epic: {task.get('epic')}")

    return stories


def test_sync_to_github(debug=False):
    """
    测试同步到GitHub

    Args:
        debug: 是否打印调试信息

    Returns:
        bool: 同步是否成功
    """
    print("\n== 测试同步到GitHub ==")

    # 初始化GitHub客户端
    client = GitHubClient()

    # 检查环境变量
    owner = os.environ.get("GITHUB_OWNER")
    repo = os.environ.get("GITHUB_REPO")

    if not owner or not repo:
        print("错误: 未设置GITHUB_OWNER或GITHUB_REPO环境变量")
        return False

    print(f"GitHub仓库: {owner}/{repo}")

    # 初始化连接器
    connector = GitHubConnector(github_client=client, owner=owner, repo=repo)

    # 执行同步
    milestone_count, task_count = connector.sync_to_github()

    print(f"成功同步 {milestone_count} 个里程碑和 {task_count} 个任务到GitHub")

    return milestone_count > 0 or task_count > 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试GitHub同步功能")
    parser.add_argument("--debug", action="store_true", help="启用调试输出")
    parser.add_argument("--skip-read", action="store_true", help="跳过读取故事数据")
    parser.add_argument("--auto-sync", action="store_true", help="自动同步而不询问")
    args = parser.parse_args()

    # 测试读取故事
    if not args.skip_read:
        stories = test_read_stories()

        # 如果找不到故事数据，退出
        if not stories.get("milestones") and not stories.get("tasks"):
            print("错误: 未找到任何故事数据")
            return 1

    # 同步到GitHub
    if args.auto_sync or input("\n是否要同步到GitHub? (y/n): ").lower() == "y":
        if not test_sync_to_github(args.debug):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

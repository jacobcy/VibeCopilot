"""
转换器命令行工具

提供命令行接口，用于roadmap.yaml和stories目录之间的转换。
"""

import argparse
import os
import sys
from pathlib import Path

from .markdown_to_yaml import convert_stories_to_roadmap
from .yaml_to_markdown import convert_roadmap_to_stories


def main():
    """命令行工具主函数"""
    parser = argparse.ArgumentParser(description="路线图格式转换工具 - 在YAML和Markdown之间转换")

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # yaml2md命令
    yaml2md_parser = subparsers.add_parser("yaml2md", help="将roadmap.yaml转换为标准化的stories目录结构")
    yaml2md_parser.add_argument(
        "--roadmap", default=".ai/roadmap/current.yaml", help="roadmap.yaml文件路径"
    )
    yaml2md_parser.add_argument("--output", default=".ai", help="输出目录")
    yaml2md_parser.add_argument("--clear", action="store_true", help="清除现有文件")
    yaml2md_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作，不提示")

    # md2yaml命令
    md2yaml_parser = subparsers.add_parser("md2yaml", help="将stories目录转换为roadmap.yaml")
    md2yaml_parser.add_argument("--stories", default=".ai/stories", help="stories目录路径")
    md2yaml_parser.add_argument("--output", default=".ai/roadmap/current.yaml", help="输出的YAML文件路径")
    md2yaml_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作，不提示")

    # direct-convert命令 - 直接将roadmap.yaml转换为tasks目录结构
    direct_parser = subparsers.add_parser(
        "direct-convert", help="直接将roadmap.yaml转换为标准任务目录结构，无需现有stories"
    )
    direct_parser.add_argument(
        "--roadmap", default=".ai/roadmap/current.yaml", help="roadmap.yaml文件路径"
    )
    direct_parser.add_argument("--output", default=".ai", help="输出目录")
    direct_parser.add_argument("--clear", action="store_true", help="清除现有文件")
    direct_parser.add_argument("--yes", "-y", action="store_true", help="自动确认所有操作，不提示")

    # 解析参数
    args = parser.parse_args()

    # 根据命令执行相应功能
    if args.command == "yaml2md":
        # 获取绝对路径
        roadmap_path = os.path.abspath(args.roadmap)
        output_dir = os.path.abspath(args.output)

        print(f"开始将 {roadmap_path} 转换为Markdown文件...")
        print(f"输出目录: {output_dir}")

        if args.clear and not args.yes:
            print("警告: 将清除目标目录中的现有文件!")
            confirm = input("确定要继续吗? (y/n): ")
            if confirm.lower() != "y":
                print("操作已取消")
                sys.exit(0)

        # 执行转换
        stats = convert_roadmap_to_stories(roadmap_path, output_dir, args.clear)

        # 输出统计信息
        print("\n转换完成!")
        print(f"创建了 {stats.get('epics', 0)} 个Epic")
        print(f"创建了 {stats.get('stories', 0)} 个Story")
        print(f"创建了 {stats.get('tasks', 0)} 个Task")
        print(f"基于 {stats.get('milestones', 0)} 个里程碑")

    elif args.command == "md2yaml":
        # 获取绝对路径
        stories_dir = os.path.abspath(args.stories)
        output_yaml = os.path.abspath(args.output)

        print(f"开始将 {stories_dir} 中的Markdown文件转换为YAML...")
        print(f"输出文件: {output_yaml}")

        # 检查输出文件是否存在
        if os.path.exists(output_yaml) and not args.yes:
            print(f"警告: 输出文件 {output_yaml} 已存在，将被覆盖!")
            confirm = input("确定要继续吗? (y/n): ")
            if confirm.lower() != "y":
                print("操作已取消")
                sys.exit(0)

        # 执行转换
        roadmap = convert_stories_to_roadmap(stories_dir, output_yaml)

        # 输出统计信息
        print("\n转换完成!")
        print(f"处理了 {len(roadmap['milestones'])} 个里程碑")
        print(f"处理了 {len(roadmap['tasks'])} 个任务")
        print(f"输出已保存到 {output_yaml}")

    elif args.command == "direct-convert":
        # 获取绝对路径
        roadmap_path = os.path.abspath(args.roadmap)
        output_dir = os.path.abspath(args.output)

        print(f"开始直接将 {roadmap_path} 转换为标准任务目录结构...")
        print(f"输出目录: {output_dir}")

        if args.clear and not args.yes:
            print("警告: 将清除目标目录中的现有文件!")
            confirm = input("确定要继续吗? (y/n): ")
            if confirm.lower() != "y":
                print("操作已取消")
                sys.exit(0)

        # 执行转换
        stats = convert_roadmap_to_stories(roadmap_path, output_dir, args.clear)

        # 输出统计信息
        print("\n转换完成!")
        print(f"创建了 {stats.get('epics', 0)} 个Epic")
        print(f"创建了 {stats.get('stories', 0)} 个Story")
        print(f"创建了 {stats.get('tasks', 0)} 个Task")
        print(f"基于 {stats.get('milestones', 0)} 个里程碑")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

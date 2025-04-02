"""
文档引擎命令行工具.

提供命令行接口，方便用户使用文档引擎功能.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .docs_engine import create_docs_engine


def main():
    """命令行工具入口函数."""
    parser = argparse.ArgumentParser(description="VibeCopilot文档引擎命令行工具")

    # 基本参数
    parser.add_argument("--base-dir", "-d", help="项目根目录", default=os.getcwd())

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # sync命令
    sync_parser = subparsers.add_parser("sync", help="同步文档")
    sync_parser.add_argument("--file", "-f", help="只同步特定文件")

    # create命令
    create_parser = subparsers.add_parser("create", help="创建新文档")
    create_parser.add_argument("--template", "-t", help="模板名称", default="default")
    create_parser.add_argument("--output", "-o", help="输出文件路径", required=True)
    create_parser.add_argument("--title", help="文档标题")
    create_parser.add_argument("--description", help="文档描述")
    create_parser.add_argument("--category", help="文档分类")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="验证文档链接")
    validate_parser.add_argument("--file", "-f", help="只验证特定文件")

    # sidebar命令
    sidebar_parser = subparsers.add_parser("sidebar", help="生成Docusaurus侧边栏")
    sidebar_parser.add_argument("--output", "-o", help="输出文件路径")

    # watch命令
    watch_parser = subparsers.add_parser("watch", help="监控文档变更")

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return

    # 创建文档引擎
    try:
        docs_engine = create_docs_engine(args.base_dir)

        # 根据命令执行操作
        if args.command == "sync":
            if args.file:
                # 同步单个文件
                success = docs_engine.sync_manager.sync_file(args.file)
                print(f"同步文件 {'成功' if success else '失败'}: {args.file}")
            else:
                # 同步所有文件
                stats = docs_engine.sync_all()
                print(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")

        elif args.command == "create":
            # 准备变量
            variables = {}
            if args.title:
                variables["title"] = args.title
            if args.description:
                variables["description"] = args.description
            if args.category:
                variables["category"] = args.category

            # 创建文档
            success = docs_engine.generate_new_document(
                template=args.template, output_path=args.output, variables=variables
            )

            print(f"创建文档 {'成功' if success else '失败'}: {args.output}")

        elif args.command == "validate":
            # 验证链接
            broken_links = docs_engine.validate_links(args.file)

            if broken_links:
                print(f"发现 {sum(len(links) for links in broken_links.values())} 个无效链接:")

                for file_path, links in broken_links.items():
                    print(f"\n文件: {file_path}")
                    for link in links:
                        print(f"  无效链接: {link['text']} (目标: {link['target']})")
            else:
                print("未发现无效链接")

        elif args.command == "sidebar":
            # 生成侧边栏
            sidebar_config = docs_engine.generate_docusaurus_sidebar()

            if args.output:
                # 写入文件
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(sidebar_config, f, indent=2, ensure_ascii=False)
                print(f"侧边栏配置已保存到: {args.output}")
            else:
                # 输出到控制台
                print(json.dumps(sidebar_config, indent=2, ensure_ascii=False))

        elif args.command == "watch":
            # 启动监控
            print("开始监控文档变更 (按Ctrl+C停止)...")
            try:
                # 如果文件监控器未启动，手动启动
                if (
                    not hasattr(docs_engine, "file_watcher")
                    or not docs_engine.file_watcher.is_running()
                ):
                    docs_engine._start_file_watcher()

                # 持续运行直到用户中断
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n停止监控")

        # 停止文档引擎
        docs_engine.stop()

    except Exception as e:
        print(f"错误: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

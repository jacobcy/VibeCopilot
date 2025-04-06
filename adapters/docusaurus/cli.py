"""
Docusaurus文档管理命令行工具

提供Docusaurus文档同步、校验和索引生成功能
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from adapters.docusaurus import DocusaurusSync, IndexGenerator


def main():
    """命令行工具入口函数"""
    parser = argparse.ArgumentParser(description="Docusaurus文档管理工具")

    # 基本参数
    parser.add_argument("--source", "-s", help="源目录", required=True)
    parser.add_argument("--target", "-t", help="目标Docusaurus目录", required=True)

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # sync命令 - 同步文档
    sync_parser = subparsers.add_parser("sync", help="同步文档")
    sync_parser.add_argument("--file", "-f", help="只同步特定文件")

    # index命令 - 生成索引
    index_parser = subparsers.add_parser("index", help="生成索引")
    index_parser.add_argument("--directory", "-d", help="为特定目录生成索引")

    # sidebar命令 - 生成侧边栏
    sidebar_parser = subparsers.add_parser("sidebar", help="生成侧边栏")
    sidebar_parser.add_argument("--output", "-o", help="输出文件路径")

    # check命令 - 检查链接
    check_parser = subparsers.add_parser("check", help="检查链接")
    check_parser.add_argument("--fix", action="store_true", help="自动修复链接")

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    try:
        # 根据命令执行操作
        if args.command == "sync":
            # 创建同步器
            sync = DocusaurusSync(args.source, args.target)

            if args.file:
                # 同步单个文件
                success = sync.sync_file(args.file)
                print(f"同步文件 {'成功' if success else '失败'}: {args.file}")
            else:
                # 同步所有文件
                stats = sync.sync_all()
                print(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")

        elif args.command == "index":
            # 创建索引生成器
            generator = IndexGenerator(args.target)

            if args.directory:
                # 为特定目录生成索引
                target_dir = Path(args.target) / args.directory
                generator.generate_index_for_directory(str(target_dir))
                print(f"已为目录生成索引: {target_dir}")
            else:
                # 为所有目录生成索引
                generator.generate_all_indices()
                print("已为所有目录生成索引")

        elif args.command == "sidebar":
            # 创建索引生成器
            generator = IndexGenerator(args.target)

            # 生成侧边栏配置
            sidebar = generator.generate_sidebar_config()

            if args.output:
                # 写入文件
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(sidebar, f, indent=2, ensure_ascii=False)
                print(f"侧边栏配置已保存到: {args.output}")
            else:
                # 输出到控制台
                print(json.dumps(sidebar, indent=2, ensure_ascii=False))

        elif args.command == "check":
            # 执行链接检查
            import subprocess

            # 确定脚本路径
            script_path = os.path.join(os.path.dirname(__file__), "check.js")

            # 执行检查脚本
            cmd = ["node", script_path, args.target]
            if args.fix:
                cmd.append("--fix")

            result = subprocess.run(cmd, capture_output=True, text=True)

            # 输出结果
            print(result.stdout)
            if result.stderr:
                print(f"错误: {result.stderr}", file=sys.stderr)
                return 1

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

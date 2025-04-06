"""
Obsidian知识库管理命令行工具

提供Obsidian知识库监控、校验和同步功能
"""

import argparse
import os
import sys
import time
from typing import Any, Dict

from adapters.obsidian import FileWatcher


def main():
    """命令行工具入口函数"""
    parser = argparse.ArgumentParser(description="Obsidian知识库管理工具")

    # 基本参数
    parser.add_argument("--vault", "-v", help="Obsidian知识库目录", required=True)

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # watch命令 - 监控知识库变更
    watch_parser = subparsers.add_parser("watch", help="监控知识库变更")
    watch_parser.add_argument("--callback", help="回调脚本路径")
    watch_parser.add_argument("--exclude", nargs="+", help="排除的文件模式")

    # check命令 - 检查语法
    check_parser = subparsers.add_parser("check", help="检查Obsidian语法")
    check_parser.add_argument("--file", "-f", help="要检查的文件")
    check_parser.add_argument("--output", "-o", help="输出报告文件路径")

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    try:
        # 根据命令执行操作
        if args.command == "watch":
            # 定义回调函数
            def callback(rel_path, event_type):
                print(f"检测到文件变更: {rel_path} ({event_type})")

                # 如果指定了回调脚本，执行它
                if args.callback:
                    import subprocess

                    subprocess.run(
                        ["python", args.callback, "--file", rel_path, "--event", event_type]
                    )

            # 创建文件监控器
            exclude_patterns = args.exclude or []
            watcher = FileWatcher(args.vault, callback, exclude_patterns)

            # 开始监控
            print(f"开始监控知识库: {args.vault}")
            print("按Ctrl+C停止...")

            watcher.start()

            try:
                # 持续运行直到用户中断
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n停止监控")
                watcher.stop()

        elif args.command == "check":
            # 导入语法检查器
            from adapters.obsidian.syntax_checker import check_syntax

            if args.file:
                # 检查单个文件
                with open(os.path.join(args.vault, args.file), "r", encoding="utf-8") as f:
                    content = f.read()

                # 执行语法检查
                issues = check_syntax(content)

                # 生成报告
                if issues:
                    print(f"文件 {args.file} 存在 {len(issues)} 个语法问题:")
                    for issue in issues:
                        print(f"行 {issue['line']}: {issue['message']}")
                else:
                    print(f"文件 {args.file} 语法检查通过")

                # 如果指定了输出文件，保存报告
                if args.output:
                    from src.docs_engine.utils import generate_html_report

                    report = generate_html_report(issues, args.output)
                    print(f"报告已保存到: {args.output}")
            else:
                print("错误: 必须指定要检查的文件")
                return 1

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

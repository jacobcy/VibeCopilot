#!/usr/bin/env python
"""
Pre-commit钩子：Obsidian语法检查

用于在提交前检查Obsidian文档的语法问题。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.docs.utils.obsidian.syntax_checker import ObsidianSyntaxChecker, generate_report
except ImportError as e:
    print(f"错误: 无法导入模块 - {e}")
    sys.exit(1)


def main():
    """主函数"""
    # 处理命令行参数
    staged_files = sys.argv[1:] if len(sys.argv) > 1 else []

    # 只检查Markdown文件
    md_files = [f for f in staged_files if f.endswith(".md")]
    if not md_files:
        print("没有Markdown文件需要检查")
        return 0

    print(f"检查 {len(md_files)} 个Markdown文件...")

    # 创建检查器
    checker = ObsidianSyntaxChecker(str(project_root))

    # 检查每个文件
    issues = {}
    for file_path in md_files:
        abs_path = (
            os.path.join(project_root, file_path) if not os.path.isabs(file_path) else file_path
        )
        if not os.path.exists(abs_path):
            print(f"警告: 文件不存在 {abs_path}")
            continue

        file_issues = checker.check_file(abs_path)
        if any(file_issues.values()):
            issues[file_path] = file_issues

    # 生成报告
    if issues:
        error_count = generate_report(issues, verbose=False)

        # 仅警告，不阻止提交
        if error_count > 0:
            print("\n警告：发现Obsidian语法错误。可以继续提交，但建议修复问题以避免同步失败。")
            print("运行 'python scripts/docs/utils/obsidian/syntax_checker.py <file>' 查看详细问题。")
            # 返回0表示通过检查，不阻止提交
            return 0
    else:
        print("语法检查通过，未发现问题。")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""
Obsidian 语法检查工具

专用于检查 Obsidian 特定的语法问题，如链接格式、嵌入语法等。
提供详细的警告和错误报告，帮助用户修复文档问题。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到模块搜索路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入重构后的模块
from scripts.docs.utils.obsidian.checker import (
    ObsidianSyntaxChecker,
    generate_report,
    setup_logging,
)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian语法检查工具")
    parser.add_argument("target", help="要检查的文件或目录路径")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归检查子目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("-b", "--base-dir", default=None, help="基础目录，用于相对路径显示")
    args = parser.parse_args()

    # 设置日志
    logger = setup_logging(args.verbose)

    # 确定目标路径
    target_path = Path(args.target)
    if not target_path.exists():
        logger.error(f"路径不存在: {target_path}")
        return 1

    # 确定基础目录
    base_dir = args.base_dir or (target_path if target_path.is_dir() else target_path.parent)

    # 初始化检查器
    checker = ObsidianSyntaxChecker(base_dir, logger)

    # 执行检查
    if target_path.is_dir():
        logger.info(f"检查目录: {target_path}")
        issues = checker.check_directory(target_path, args.recursive)
    else:
        logger.info(f"检查文件: {target_path}")
        file_issues = checker.check_file(target_path)
        # 将单文件结果格式化为与目录结果相同的格式
        issues = (
            {str(target_path.relative_to(base_dir)): file_issues}
            if any(file_issues.values())
            else {}
        )

    # 生成报告
    error_count = generate_report(issues, args.verbose)

    # 返回错误数量作为退出码（0表示没有错误）
    return min(error_count, 1)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库会话导入检查脚本

检查项目中是否有文件仍在导入src.db.session
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 需要检查的源代码目录
SOURCE_DIRS = ["src", "examples", "tests", "scripts"]

# 定义匹配模式
DB_SESSION_IMPORT_PATTERN = re.compile(r"from\s+src\.db\.session\s+import")


def find_python_files(directories: List[str]) -> List[Path]:
    """查找指定目录下的所有Python文件

    Args:
        directories: 要搜索的目录列表

    Returns:
        Python文件路径列表
    """
    python_files = []
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue

        for file_path in dir_path.glob("**/*.py"):
            python_files.append(file_path)

    return python_files


def check_file_for_imports(file_path: Path) -> Tuple[bool, List[str]]:
    """检查文件中是否包含需要迁移的导入语句

    Args:
        file_path: 文件路径

    Returns:
        包含(是否有问题导入, 问题导入行列表)
    """
    has_issues = False
    issue_lines = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if DB_SESSION_IMPORT_PATTERN.search(line):
                    has_issues = True
                    issue_lines.append(f"行 {i}: {line.strip()}")
    except Exception as e:
        print(f"读取文件 {file_path} 出错: {e}")
        return False, []

    return has_issues, issue_lines


def check_project() -> Dict[str, List[str]]:
    """检查整个项目中的导入问题

    Returns:
        存在问题的文件及其问题行的字典
    """
    files_with_issues = {}
    python_files = find_python_files(SOURCE_DIRS)

    for file_path in python_files:
        has_issues, issue_lines = check_file_for_imports(file_path)
        if has_issues:
            files_with_issues[str(file_path)] = issue_lines

    return files_with_issues


def main():
    """主函数"""
    print("检查项目中的数据库会话导入...")
    files_with_issues = check_project()

    if not files_with_issues:
        print("成功！项目中没有发现直接导入src.db.session的文件。")
        return 0

    print(f"发现 {len(files_with_issues)} 个文件仍在使用src.db.session导入:")
    for file_path, issues in files_with_issues.items():
        print(f"\n文件: {file_path}")
        for issue in issues:
            print(f"  {issue}")

    print("\n请将以上文件的导入修改为使用 'from src.db import ...' 的形式。")
    print("详情参考: docs/dev/db_session_migration_plan.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())

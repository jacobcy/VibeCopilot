#!/usr/bin/env python3
"""
批量修复任务文件中的空链接
"""
import glob
import os
from pathlib import Path


def fix_empty_links(task_file):
    """修复单个任务文件中的空链接"""
    with open(task_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 如果包含空链接，则替换
    if "[相关文档1](#)" in content:
        content = content.replace(
            "- [相关文档1](#)\n- [相关文档2](#)",
            "- [项目文档](../../../docs/README.md)\n- [开发指南](../../../docs/development.md)",
        )

        with open(task_file, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    return False


def main():
    """主函数，处理所有任务文件"""
    base_dir = Path(".ai/stories/tasks")

    if not base_dir.exists():
        print(f"无法找到目录: {base_dir}")
        return

    # 获取所有任务文件
    task_files = glob.glob(str(base_dir / "**/task.md"), recursive=True)

    fixed_count = 0
    for task_file in task_files:
        if fix_empty_links(task_file):
            print(f"已修复: {task_file}")
            fixed_count += 1

    print(f"\n总计修复了 {fixed_count} 个文件中的空链接")


if __name__ == "__main__":
    main()

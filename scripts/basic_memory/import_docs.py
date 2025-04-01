#!/usr/bin/env python3
"""
Basic Memory文档导入工具
将Markdown文档导入到Basic Memory数据库并导出到Obsidian
"""

import os
import sys

from scripts.basic_memory.importer import DocImporter


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python import_docs.py <source_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    if not os.path.isdir(source_dir):
        print(f"错误: 目录不存在: {source_dir}")
        sys.exit(1)

    try:
        importer = DocImporter(source_dir)
        importer.import_docs()
    except Exception as e:
        print(f"❌ 导入过程中出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

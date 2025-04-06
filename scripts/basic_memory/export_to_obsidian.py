#!/usr/bin/env python3
"""
从Basic Memory数据库导出到Obsidian
将实体关系数据转换为Obsidian友好的Markdown
使用模块化结构减少文件大小
"""

import argparse
import os
import sys
from pathlib import Path

from adapters.basic_memory.db.memory_store import MemoryStore
from adapters.basic_memory.exporters.obsidian_exporter import ObsidianExporter


def main():
    parser = argparse.ArgumentParser(description="从Basic Memory数据库导出到Obsidian")
    parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="Basic Memory数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )
    parser.add_argument(
        "--output",
        default="/Users/chenyi/basic-memory/obsidian_vault",
        help="Obsidian输出目录 (默认: /Users/chenyi/basic-memory/obsidian_vault)",
    )

    args = parser.parse_args()

    # 创建记忆存储
    memory_store = MemoryStore(args.db)

    # 创建Obsidian导出器
    exporter = ObsidianExporter(args.output)

    # 执行导出
    try:
        # 设置输出目录
        exporter.setup_output_dir()

        # 获取数据库中的所有实体
        print(f"正在从数据库 {args.db} 导出到 {args.output} ...")

        # 导出所有实体
        exporter.export_all(memory_store)

        print(f"\n导出完成! 文件已保存到: {args.output}")

    except Exception as e:
        print(f"导出过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

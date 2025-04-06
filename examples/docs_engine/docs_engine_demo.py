#!/usr/bin/env python3
"""
动态文档系统演示

展示动态文档系统的核心功能
"""

import os
import tempfile
from pathlib import Path

from examples.docs_engine.demo_operations import (
    demo_basic_operations,
    demo_content_handling,
    demo_markdown_import,
)
from examples.docs_engine.mock_models import SimpleDocument
from examples.docs_engine.mock_storage import SimpleStorageEngine
from src.docs_engine import BlockManager, DocumentEngine, LinkManager, MarkdownImporter


def setup_database():
    """设置临时数据库"""
    # 创建临时数据库文件（实际不使用）
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()

    # 创建模拟存储引擎
    storage = SimpleStorageEngine()

    # 返回存储引擎和文件路径
    return storage, db_file.name


def main():
    """主函数"""
    print("动态文档系统演示")
    print("=================")

    # 设置模拟数据库
    storage, db_file = setup_database()
    print(f"创建临时数据库: {db_file}")

    try:
        # 演示基本操作
        doc1_id, doc2_id = demo_basic_operations(storage)

        # 演示内容处理
        demo_content_handling(storage, doc1_id)

        # 演示Markdown导入
        demo_markdown_import(storage)

    finally:
        # 删除临时数据库文件
        try:
            os.unlink(db_file)
            print(f"\n已删除临时数据库: {db_file}")
        except Exception:
            pass


if __name__ == "__main__":
    main()

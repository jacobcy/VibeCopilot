#!/usr/bin/env python3
"""
动态文档系统演示操作

包含演示不同功能的操作函数
"""

import json
import tempfile
from pathlib import Path

from src.docs_engine import BlockManager, DocumentEngine, LinkManager
from src.models.db.docs_engine import BlockType


def demo_basic_operations(storage):
    """演示基本操作

    Args:
        storage: 存储引擎对象

    Returns:
        tuple: 包含第一个和第二个演示文档ID的元组
    """
    print("\n=== 演示基本操作 ===")

    # 创建 API 组件
    doc_engine = DocumentEngine(storage)
    block_manager = BlockManager(storage)
    link_manager = LinkManager(storage)

    # 创建文档
    print("创建文档...")
    doc1 = doc_engine.create_document(
        title="测试文档1", path="/test/doc1.md", metadata={"tags": ["test", "demo"]}
    )
    print(f"已创建文档: {doc1.id} - {doc1.title}")

    doc2 = doc_engine.create_document(
        title="测试文档2", path="/test/doc2.md", metadata={"tags": ["test", "reference"]}
    )
    print(f"已创建文档: {doc2.id} - {doc2.title}")

    # 创建块
    print("\n创建块...")
    block1 = block_manager.create_block(
        document_id=doc1.id, content="这是第一个文本块。", type=BlockType.TEXT, sequence=0
    )
    print(f"已创建块: {block1.id} - {block1.type}")

    block2 = block_manager.create_block(
        document_id=doc1.id,
        content="# 这是一个标题",
        type=BlockType.HEADING,
        metadata={"level": 1},  # Will be converted to block_metadata internally
        sequence=1,
    )
    print(f"已创建块: {block2.id} - {block2.type}")

    block3 = block_manager.create_block(
        document_id=doc1.id,
        content="print('Hello, World!')",
        type=BlockType.CODE,
        metadata={"language": "python"},  # Will be converted to block_metadata internally
        sequence=2,
    )
    print(f"已创建块: {block3.id} - {block3.type}")

    # 创建第二个文档中的块
    block4 = block_manager.create_block(
        document_id=doc2.id, content="这是第二个文档中的块，将链接到第一个文档。", type=BlockType.TEXT, sequence=0
    )
    print(f"已创建块: {block4.id} - {block4.type}")

    # 创建链接
    print("\n创建链接...")
    link1 = link_manager.create_link(source_doc_id=doc1.id, target_doc_id=doc2.id, text="参考资料")
    print(f"已创建链接: {link1.id} - {doc1.id} -> {doc2.id}")

    # 创建反向链接
    link2 = link_manager.create_link(source_doc_id=doc2.id, target_doc_id=doc1.id, text="返回主文档")
    print(f"已创建链接: {link2.id} - {doc2.id} -> {doc1.id}")

    # 获取文档
    print("\n获取文档...")
    retrieved_doc = doc_engine.get_document(doc1.id)
    print(f"获取到文档: {retrieved_doc.id} - {retrieved_doc.title}")

    # 获取块
    print("\n获取文档块...")
    blocks = block_manager.get_document_blocks(doc1.id)
    print(f"文档 {doc1.id} 有 {len(blocks)} 个块:")
    for block in blocks:
        print(f"  - {block.id} ({block.type}): {block.content[:30]}...")

    # 获取链接
    print("\n获取文档链接...")
    links1 = link_manager.get_document_links(doc1.id)
    print(f"文档 {doc1.id} 有 {len(links1['outgoing'])} 个出链:")
    for link in links1["outgoing"]:
        print(f"  - {link.id}: -> {link.target_doc_id} ({link.text or '无文本'})")

    print(f"文档 {doc1.id} 有 {len(links1['incoming'])} 个入链:")
    for link in links1["incoming"]:
        print(f"  - {link.id}: <- {link.source_doc_id} ({link.text or '无文本'})")

    # 获取第二个文档的链接
    links2 = link_manager.get_document_links(doc2.id)
    print(f"\n文档 {doc2.id} 有 {len(links2['outgoing'])} 个出链:")
    for link in links2["outgoing"]:
        print(f"  - {link.id}: -> {link.target_doc_id} ({link.text or '无文本'})")

    print(f"文档 {doc2.id} 有 {len(links2['incoming'])} 个入链:")
    for link in links2["incoming"]:
        print(f"  - {link.id}: <- {link.source_doc_id} ({link.text or '无文本'})")

    return doc1.id, doc2.id


def demo_content_handling(storage, doc_id):
    """演示内容处理

    Args:
        storage: 存储引擎对象
        doc_id: 文档ID
    """
    print("\n=== 演示内容处理 ===")

    # 创建组件
    doc_engine = DocumentEngine(storage)
    block_manager = BlockManager(storage)

    # 更新文档状态
    print("更新文档状态...")
    doc = doc_engine.publish_document(doc_id)
    print(f"文档 {doc.id} 状态更新为: {doc.status}")

    # 分割Markdown内容
    print("\n分割Markdown内容...")
    markdown_content = """# 示例文档

这是一个示例文档，用于演示内容分割功能。

## 第一部分

这是第一部分的内容。

```python
def hello():
    print("Hello, World!")
```

## 第二部分

这是第二部分的内容。
"""

    # 清空现有块
    existing_blocks = block_manager.get_document_blocks(doc_id)
    for block in existing_blocks:
        block_manager.delete_block(block.id)

    # 分割内容为块
    blocks = block_manager.split_markdown_content(doc_id, markdown_content)
    print(f"内容已分割为 {len(blocks)} 个块:")
    for block in blocks:
        print(f"  - {block.id} ({block.type}): {block.content[:30]}...")


class SimpleMarkdownImporter:
    """简单的Markdown导入工具"""

    def __init__(self, doc_engine, block_manager, link_manager):
        """初始化导入工具

        Args:
            doc_engine: 文档引擎
            block_manager: 块管理器
            link_manager: 链接管理器
        """
        self.doc_engine = doc_engine
        self.block_manager = block_manager
        self.link_manager = link_manager

    def import_directory(self, directory):
        """导入目录中的所有Markdown文件

        Args:
            directory: 目录路径

        Returns:
            dict: 导入统计信息
        """
        dir_path = Path(directory)
        md_files = list(dir_path.glob("*.md"))

        result = {
            "total": len(md_files),
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "links_created": 0,
        }

        for file_path in md_files:
            try:
                # Read file content
                with open(file_path, "r") as f:
                    content = f.read()

                # Create document
                doc = self.doc_engine.create_document(
                    title=file_path.stem,
                    path=str(file_path.relative_to(dir_path)),
                    content=content,
                )

                result["imported"] += 1
            except Exception as e:
                print(f"Failed to import {file_path}: {str(e)}")
                result["failed"] += 1

        return result


def demo_markdown_import(storage):
    """演示Markdown导入

    Args:
        storage: 存储引擎对象
    """
    print("\n=== 演示Markdown导入 ===")

    # 创建组件
    doc_engine = DocumentEngine(storage)
    block_manager = BlockManager(storage)
    link_manager = LinkManager(storage)

    # 创建导入器实例
    importer = SimpleMarkdownImporter(doc_engine, block_manager, link_manager)

    # 创建临时Markdown文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建一些示例文件
        base_dir = Path(temp_dir)

        # 文件1
        file1 = base_dir / "doc1.md"
        with open(file1, "w") as f:
            f.write(
                """---
title: 文档1
tags: [example, demo]
---

# 文档1

这是第一个示例文档。

## 链接示例

这是一个到[文档2](doc2.md)的链接。
"""
            )

        # 文件2
        file2 = base_dir / "doc2.md"
        with open(file2, "w") as f:
            f.write(
                """---
title: 文档2
tags: [example, reference]
---

# 文档2

这是第二个示例文档。

## 代码示例

```python
def hello():
    return "Hello from Document 2"
```

## 链接回去

这是一个回到[文档1](doc1.md)的链接。
"""
            )

        # 导入目录
        print(f"从 {temp_dir} 导入文档...")
        stats = importer.import_directory(temp_dir)

        print("导入统计:")
        print(f"  - 总文件数: {stats['total']}")
        print(f"  - 已导入: {stats['imported']}")
        print(f"  - 已跳过: {stats['skipped']}")
        print(f"  - 失败: {stats['failed']}")
        print(f"  - 创建的链接: {stats['links_created']}")

        # 列出导入的文档
        documents = doc_engine.list_documents()
        print("\n导入的文档:")
        for doc in documents:
            print(f"  - {doc.id} ({doc.title})")

            # 获取链接
            links = link_manager.get_document_links(doc.id)
            if links["outgoing"]:
                print(f"    出链 ({len(links['outgoing'])}):")
                for link in links["outgoing"]:
                    target_doc = doc_engine.get_document(link.target_doc_id)
                    print(f"      -> {target_doc.title} ({link.target_doc_id})")

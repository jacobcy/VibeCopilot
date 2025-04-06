#!/usr/bin/env python3
"""
动态文档系统演示

展示动态文档系统的核心功能
"""

import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.docs_engine import BlockManager, DocumentEngine, LinkManager, MarkdownImporter
from src.models.db.docs_engine import BlockType, DocumentStatus


# 创建模拟对象来置换真实的数据库模型
class SimpleDocument:
    def __init__(self, id, title, path, status="draft", metadata=None):
        self.id = id
        self.title = title
        self.path = path
        self.status = status
        self.doc_metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @staticmethod
    def generate_id():
        return f"doc-{uuid.uuid4()}"


class SimpleBlock:
    def __init__(self, id, document_id, type, content, order, metadata=None):
        self.id = id
        self.document_id = document_id
        self.type = type
        self.content = content
        self.order = order
        self.block_metadata = metadata or {}

    @staticmethod
    def generate_id():
        return f"blk-{uuid.uuid4()}"


class SimpleLink:
    def __init__(
        self,
        id,
        source_doc_id,
        target_doc_id,
        source_block_id=None,
        target_block_id=None,
        text=None,
    ):
        self.id = id
        self.source_doc_id = source_doc_id
        self.target_doc_id = target_doc_id
        self.source_block_id = source_block_id
        self.target_block_id = target_block_id
        self.text = text
        self.created_at = datetime.now()

    @staticmethod
    def generate_id():
        return f"lnk-{uuid.uuid4()}"


# 模拟存储引擎
class SimpleStorageEngine:
    def __init__(self):
        self.documents = {}
        self.blocks = {}
        self.links = {}

    def create_document(self, title, path=None, status="draft", metadata=None):
        doc_id = SimpleDocument.generate_id()
        doc = SimpleDocument(doc_id, title, path, status, metadata)
        self.documents[doc_id] = doc
        return doc

    def get_document(self, doc_id):
        return self.documents.get(doc_id)

    def update_document(self, doc_id, updates):
        doc = self.get_document(doc_id)
        if not doc:
            return None

        for key, value in updates.items():
            if key == "metadata":
                doc.doc_metadata = value
            else:
                setattr(doc, key, value)

        doc.updated_at = datetime.now()
        return doc

    def delete_document(self, doc_id):
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def list_documents(self, status=None):
        if status:
            return [doc for doc in self.documents.values() if doc.status == status]
        return list(self.documents.values())

    def create_block(
        self,
        document_id,
        content,
        type=None,
        block_type=None,
        metadata=None,
        sequence=None,
        order=None,
    ):
        # Handle type parameter
        if block_type is not None and type is None:
            type = block_type

        # Set order
        if sequence is not None:
            block_order = sequence
        elif order is not None:
            block_order = order
        else:
            block_order = len([b for b in self.blocks.values() if b.document_id == document_id])

        block_id = SimpleBlock.generate_id()
        block = SimpleBlock(block_id, document_id, type, content, block_order, metadata)
        self.blocks[block_id] = block
        return block

    def get_block(self, block_id):
        return self.blocks.get(block_id)

    def delete_block(self, block_id):
        if block_id in self.blocks:
            del self.blocks[block_id]
            return True
        return False

    def get_document_blocks(self, doc_id):
        return [block for block in self.blocks.values() if block.document_id == doc_id]

    def create_link(
        self, source_doc_id, target_doc_id, source_block_id=None, target_block_id=None, text=None
    ):
        link_id = SimpleLink.generate_id()
        link = SimpleLink(
            link_id, source_doc_id, target_doc_id, source_block_id, target_block_id, text
        )
        self.links[link_id] = link
        return link

    def get_document_links(self, doc_id):
        outgoing = [link for link in self.links.values() if link.source_doc_id == doc_id]
        incoming = [link for link in self.links.values() if link.target_doc_id == doc_id]
        return {"outgoing": outgoing, "incoming": incoming}

    def get_outgoing_links(self, doc_id):
        return [link for link in self.links.values() if link.source_doc_id == doc_id]

    def get_incoming_links(self, doc_id):
        return [link for link in self.links.values() if link.target_doc_id == doc_id]

    def split_markdown_content(self, doc_id, content):
        # 简单实现：按照行分割内容并创建不同类型的块
        lines = content.split("\n")
        blocks = []

        for i, line in enumerate(lines):
            if line.startswith("# "):
                # 创建标题块
                block = self.create_block(
                    document_id=doc_id,
                    content=line,
                    type=BlockType.HEADING,
                    metadata={"level": 1},
                    order=i,
                )
                blocks.append(block)
            elif line.startswith("```"):
                # 创建代码块
                lang = line[3:].strip() or "text"
                code_content = lines[i + 1] if i + 1 < len(lines) else ""
                block = self.create_block(
                    document_id=doc_id,
                    content=code_content,
                    type=BlockType.CODE,
                    metadata={"language": lang},
                    order=i,
                )
                blocks.append(block)
                i += 2  # 跳过代码块的内容和结束标记
            elif line.strip():
                # 创建文本块
                block = self.create_block(
                    document_id=doc_id, content=line, type=BlockType.TEXT, order=i
                )
                blocks.append(block)

        return blocks

    def find_by_path(self, path):
        """通过路径查找文档"""
        for doc in self.documents.values():
            if doc.path == path:
                return doc
        return None

    def search(self, query):
        """搜索文档"""
        # 简单实现：只搜索标题
        results = []
        for doc in self.documents.values():
            if query.lower() in doc.title.lower():
                results.append(doc)
        return results


def setup_database():
    """设置临时数据库"""
    # 创建临时数据库文件（实际不使用）
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()

    # 创建模拟存储引擎
    storage = SimpleStorageEngine()

    # 返回存储引擎和文件路径
    return storage, db_file.name


def demo_basic_operations(storage):
    """演示基本操作"""
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
    """演示内容处理"""
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


def demo_markdown_import(storage):
    """演示Markdown导入"""
    print("\n=== 演示Markdown导入 ===")

    # 创建组件
    doc_engine = DocumentEngine(storage)
    block_manager = BlockManager(storage)
    link_manager = LinkManager(storage)

    # 创建简单的Markdown导入工具
    class SimpleMarkdownImporter:
        def __init__(self, doc_engine, block_manager, link_manager):
            self.doc_engine = doc_engine
            self.block_manager = block_manager
            self.link_manager = link_manager

        def import_directory(self, directory):
            """Import all markdown files from a directory"""
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

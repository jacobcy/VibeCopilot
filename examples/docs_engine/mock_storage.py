#!/usr/bin/env python3
"""
动态文档系统模拟存储引擎

提供模拟存储引擎，用于演示和测试
"""

from datetime import datetime

from examples.docs_engine.mock_models import SimpleBlock, SimpleDocument, SimpleLink
from src.models.db.docs_engine import BlockType


class SimpleStorageEngine:
    """模拟存储引擎，用于演示和测试"""

    def __init__(self):
        """初始化存储引擎"""
        self.documents = {}
        self.blocks = {}
        self.links = {}

    def create_document(self, title, path=None, status="draft", metadata=None):
        """创建文档

        Args:
            title: 文档标题
            path: 文档路径，默认为None
            status: 文档状态，默认为draft
            metadata: 文档元数据，默认为None

        Returns:
            SimpleDocument: 创建的文档对象
        """
        doc_id = SimpleDocument.generate_id()
        doc = SimpleDocument(doc_id, title, path, status, metadata)
        self.documents[doc_id] = doc
        return doc

    def get_document(self, doc_id):
        """获取文档

        Args:
            doc_id: 文档ID

        Returns:
            SimpleDocument: 文档对象，不存在则返回None
        """
        return self.documents.get(doc_id)

    def update_document(self, doc_id, updates):
        """更新文档

        Args:
            doc_id: 文档ID
            updates: 更新数据，字典

        Returns:
            SimpleDocument: 更新后的文档对象，不存在则返回None
        """
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
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            bool: 删除成功返回True，不存在则返回False
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def list_documents(self, status=None):
        """列出文档

        Args:
            status: 文档状态，默认为None，表示所有状态

        Returns:
            list: 文档对象列表
        """
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
        """创建块

        Args:
            document_id: 文档ID
            content: 块内容
            type: 块类型，默认为None
            block_type: 块类型，默认为None，兼容老接口
            metadata: 块元数据，默认为None
            sequence: 序列号，默认为None
            order: 排序顺序，默认为None

        Returns:
            SimpleBlock: 创建的块对象
        """
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
        """获取块

        Args:
            block_id: 块ID

        Returns:
            SimpleBlock: 块对象，不存在则返回None
        """
        return self.blocks.get(block_id)

    def delete_block(self, block_id):
        """删除块

        Args:
            block_id: 块ID

        Returns:
            bool: 删除成功返回True，不存在则返回False
        """
        if block_id in self.blocks:
            del self.blocks[block_id]
            return True
        return False

    def get_document_blocks(self, doc_id):
        """获取文档的所有块

        Args:
            doc_id: 文档ID

        Returns:
            list: 块对象列表
        """
        return [block for block in self.blocks.values() if block.document_id == doc_id]

    def create_link(
        self, source_doc_id, target_doc_id, source_block_id=None, target_block_id=None, text=None
    ):
        """创建链接

        Args:
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID，默认为None
            target_block_id: 目标块ID，默认为None
            text: 链接文本，默认为None

        Returns:
            SimpleLink: 创建的链接对象
        """
        link_id = SimpleLink.generate_id()
        link = SimpleLink(
            link_id, source_doc_id, target_doc_id, source_block_id, target_block_id, text
        )
        self.links[link_id] = link
        return link

    def get_document_links(self, doc_id):
        """获取文档的所有链接

        Args:
            doc_id: 文档ID

        Returns:
            dict: 包含出链和入链的字典
        """
        outgoing = [link for link in self.links.values() if link.source_doc_id == doc_id]
        incoming = [link for link in self.links.values() if link.target_doc_id == doc_id]
        return {"outgoing": outgoing, "incoming": incoming}

    def get_outgoing_links(self, doc_id):
        """获取文档的出链

        Args:
            doc_id: 文档ID

        Returns:
            list: 链接对象列表
        """
        return [link for link in self.links.values() if link.source_doc_id == doc_id]

    def get_incoming_links(self, doc_id):
        """获取文档的入链

        Args:
            doc_id: 文档ID

        Returns:
            list: 链接对象列表
        """
        return [link for link in self.links.values() if link.target_doc_id == doc_id]

    def split_markdown_content(self, doc_id, content):
        """分割Markdown内容为块

        Args:
            doc_id: 文档ID
            content: Markdown内容

        Returns:
            list: 创建的块对象列表
        """
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
        """通过路径查找文档

        Args:
            path: 文档路径

        Returns:
            SimpleDocument: 文档对象，不存在则返回None
        """
        for doc in self.documents.values():
            if doc.path == path:
                return doc
        return None

    def search(self, query):
        """搜索文档

        Args:
            query: 搜索关键词

        Returns:
            list: 文档对象列表
        """
        # 简单实现：只搜索标题
        results = []
        for doc in self.documents.values():
            if query.lower() in doc.title.lower():
                results.append(doc)
        return results

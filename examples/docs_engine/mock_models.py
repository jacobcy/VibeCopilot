#!/usr/bin/env python3
"""
动态文档系统模拟模型

提供模拟数据模型，用于演示和测试
"""

import uuid
from datetime import datetime


class SimpleDocument:
    """简单文档模型，用于模拟真实数据库模型"""

    def __init__(self, id, title, path, status="draft", metadata=None):
        """初始化文档对象

        Args:
            id: 文档ID
            title: 文档标题
            path: 文档路径
            status: 文档状态，默认为draft
            metadata: 文档元数据，默认为None
        """
        self.id = id
        self.title = title
        self.path = path
        self.status = status
        self.doc_metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @staticmethod
    def generate_id():
        """生成唯一文档ID

        Returns:
            str: 唯一文档ID
        """
        return f"doc-{uuid.uuid4()}"


class SimpleBlock:
    """简单块模型，用于模拟真实数据库模型"""

    def __init__(self, id, document_id, type, content, order, metadata=None):
        """初始化块对象

        Args:
            id: 块ID
            document_id: 文档ID
            type: 块类型
            content: 块内容
            order: 排序顺序
            metadata: 块元数据，默认为None
        """
        self.id = id
        self.document_id = document_id
        self.type = type
        self.content = content
        self.order = order
        self.block_metadata = metadata or {}

    @staticmethod
    def generate_id():
        """生成唯一块ID

        Returns:
            str: 唯一块ID
        """
        return f"blk-{uuid.uuid4()}"


class SimpleLink:
    """简单链接模型，用于模拟真实数据库模型"""

    def __init__(
        self,
        id,
        source_doc_id,
        target_doc_id,
        source_block_id=None,
        target_block_id=None,
        text=None,
    ):
        """初始化链接对象

        Args:
            id: 链接ID
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID，默认为None
            target_block_id: 目标块ID，默认为None
            text: 链接文本，默认为None
        """
        self.id = id
        self.source_doc_id = source_doc_id
        self.target_doc_id = target_doc_id
        self.source_block_id = source_block_id
        self.target_block_id = target_block_id
        self.text = text
        self.created_at = datetime.now()

    @staticmethod
    def generate_id():
        """生成唯一链接ID

        Returns:
            str: 唯一链接ID
        """
        return f"lnk-{uuid.uuid4()}"

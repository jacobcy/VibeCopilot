"""
记忆管理器

整合文档解析和向量存储功能，提供简单的知识记忆管理。
"""

import logging
from typing import Any, Dict, List, Optional, Union

from src.db import get_session_factory
from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.db.vector.chroma_vector_store import ChromaVectorStore
from src.memory.entity_manager import EntityManager
from src.memory.memory_formatter import MemoryFormatter
from src.memory.memory_retrieval import MemoryRetrieval
from src.memory.memory_store import MemoryStore
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.parsing.processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器

    整合文档解析和向量存储功能，提供简单的知识记忆存取和召回功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化记忆管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 初始化文档处理器
        self.doc_processor = DocumentProcessor(backend=self.config.get("parser_backend", "openai"), config=self.config.get("parser_config", {}))

        # 初始化向量存储 - 使用单例模式避免创建多个实例
        vector_store_config = self.config.get("vector_store_config", {})
        # 添加一个标识前缀，避免与其他Chroma实例冲突
        instance_id = vector_store_config.get("instance_id", "memory_manager")
        vector_store_config["instance_id"] = instance_id

        self.vector_store = ChromaVectorStore(config=vector_store_config)

        # 初始化实体、关系和观察管理器
        self.entity_manager = EntityManager()
        self.relation_manager = RelationManager()
        self.observation_manager = ObservationManager()

        # 获取数据库会话工厂并创建会话
        session_factory = get_session_factory()
        self.session = session_factory()
        self.memory_item_repo = MemoryItemRepository(self.session)

        # 默认文件夹和标签
        self.default_folder = self.config.get("default_folder", "knowledge")
        self.default_tags = self.config.get("default_tags", "memory,knowledge")

        # 初始化格式化器
        self.memory_formatter = MemoryFormatter(self.memory_item_repo)

        # 初始化存储和检索组件
        self.store = MemoryStore(
            doc_processor=self.doc_processor,
            vector_store=self.vector_store,
            entity_manager=self.entity_manager,
            relation_manager=self.relation_manager,
            observation_manager=self.observation_manager,
            memory_item_repo=self.memory_item_repo,
            memory_formatter=self.memory_formatter,
            default_folder=self.default_folder,
            default_tags=self.default_tags,
        )

        self.retrieval = MemoryRetrieval(
            doc_processor=self.doc_processor,
            vector_store=self.vector_store,
            memory_item_repo=self.memory_item_repo,
            memory_formatter=self.memory_formatter,
            default_folder=self.default_folder,
        )

    async def store_memory(
        self, content: str, title: Optional[str] = None, tags: Optional[str] = None, folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        存储记忆

        解析内容并存储到向量库和结构化存储中

        Args:
            content: 要存储的内容
            title: 记忆标题
            tags: 标签，逗号分隔
            folder: 存储文件夹，如果不提供则使用默认文件夹

        Returns:
            存储结果
        """
        return await self.store.store_memory(content, title, tags, folder)

    async def retrieve_memory(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        召回记忆

        根据查询检索相关记忆

        Args:
            query: 查询文本
            limit: 返回结果数量

        Returns:
            检索结果
        """
        return await self.retrieval.retrieve_memory(query, limit)

    async def get_memory_by_id(self, permalink: str) -> Dict[str, Any]:
        """
        通过ID获取记忆

        Args:
            permalink: 记忆永久链接

        Returns:
            记忆内容
        """
        return await self.retrieval.get_memory_by_id(permalink)

    async def delete_memory(self, permalink: str) -> Dict[str, Any]:
        """
        删除记忆

        Args:
            permalink: 记忆永久链接

        Returns:
            删除结果
        """
        return await self.store.delete_memory(permalink)

    async def list_memories(self, folder: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        列出所有记忆

        Args:
            folder: 文件夹名称
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        return await self.retrieval.list_memories(folder, limit)

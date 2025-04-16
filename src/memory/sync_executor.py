"""
同步执行器

负责将处理后的内容存储到向量存储中。
"""

import logging
from typing import Any, Dict, List, Optional

from src.memory.vector.memory_adapter import BasicMemoryAdapter

logger = logging.getLogger(__name__)


class SyncExecutor:
    """
    同步执行器

    专注于执行存储操作，将处理好的文本和元数据存储到向量存储中。
    不再负责决定什么需要同步，也不关心如何处理文件。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化同步执行器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建向量存储适配器
        self.vector_store = BasicMemoryAdapter(self.config.get("vector_store"))

    async def execute_storage(self, texts: List[str], metadata_list: List[Dict[str, Any]], collection_name: str) -> List[str]:
        """
        执行存储操作

        将处理后的文本和元数据存储到指定的向量存储集合中。

        Args:
            texts: 文本内容列表
            metadata_list: 对应的元数据列表
            collection_name: 目标集合名称

        Returns:
            存储后的永久链接列表
        """
        if not texts:
            return []

        # 调用向量存储适配器的存储方法
        permalinks = await self.vector_store.store(texts, metadata_list, collection_name)

        logger.info(f"已将{len(texts)}个项目存储到集合'{collection_name}'中")

        return permalinks

    async def store_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], collection_name: str) -> List[str]:
        """
        存储文档（execute_storage的别名）

        将处理后的文本和元数据存储到指定的向量存储集合中。

        Args:
            texts: 文本内容列表
            metadatas: 对应的元数据列表
            collection_name: 目标集合名称

        Returns:
            存储后的永久链接列表
        """
        return await self.execute_storage(texts, metadatas, collection_name)

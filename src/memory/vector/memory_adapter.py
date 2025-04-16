"""
向量存储适配器

适配不同的向量存储实现，提供统一的接口。
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

from src.memory.vector.chroma_vector_store import ChromaVectorStore
from src.memory.vector.vector_store import VectorStore

logger = logging.getLogger(__name__)


class BasicMemoryAdapter(VectorStore):
    """
    基本向量存储适配器

    提供统一的向量存储接口，底层使用ChromaDB实现。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储适配器

        Args:
            config: 配置参数
        """
        super().__init__(config)

        # 默认配置
        self.default_config = {
            "data_dir": os.path.join(os.path.expanduser("~"), "Public", "VibeCopilot", "data", "chroma_db"),
            "default_folder": "vibecopilot",
            "default_tags": "vibecopilot",
        }

        # 合并配置
        if config:
            self.default_config.update(config)

        # 初始化ChromaDB向量存储
        self.vector_store = ChromaVectorStore(self.default_config)
        logger.info("初始化ChromaDB向量存储")

    async def store(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        folder: Optional[str] = None,
    ) -> List[str]:
        """
        存储文本及元数据到向量库

        Args:
            texts: 要存储的文本列表
            metadata: 每个文本对应的元数据
            folder: 存储文件夹

        Returns:
            存储后的永久链接列表
        """
        return await self.vector_store.store(texts, metadata, folder)

    async def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索向量库

        Args:
            query: 搜索查询
            limit: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        return await self.vector_store.search(query, limit, filter_dict)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            id: 永久链接

        Returns:
            文档内容和元数据
        """
        return await self.vector_store.get(id)

    async def update(self, id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        更新文档

        Args:
            id: 永久链接
            content: 新内容
            metadata: 新元数据

        Returns:
            更新是否成功
        """
        return await self.vector_store.update(id, content, metadata)

    async def delete(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 永久链接列表

        Returns:
            删除是否成功
        """
        return await self.vector_store.delete(ids)

    async def list_folders(self) -> List[str]:
        """
        列出所有文件夹

        Returns:
            文件夹列表
        """
        return await self.vector_store.list_folders()

    async def list_documents(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夹中的所有文档

        Args:
            folder: 文件夹名称，如果为None则列出所有文件夹中的文档

        Returns:
            文档列表
        """
        return await self.vector_store.list_documents(folder)

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接是否正常

        Returns:
            测试结果
        """
        try:
            result = await self.vector_store.test_connection()

            # 添加API可用性标记
            result["details"]["api_available"] = True

            return result
        except Exception as e:
            logger.error(f"ChromaDB向量存储连接测试失败: {e}")
            return {"success": False, "message": f"ChromaDB向量存储连接测试失败: {e}", "details": {"api_available": False, "error": str(e)}}

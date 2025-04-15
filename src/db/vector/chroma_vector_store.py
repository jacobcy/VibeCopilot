"""
基于ChromaDB的向量存储实现

使用ChromaDB作为后端的向量存储实现，专为存储开发资料设计。
"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document

from src.db.vector.chroma_batch import ChromaBatch
from src.db.vector.chroma_core import ChromaCore
from src.db.vector.chroma_search import ChromaSearch
from src.db.vector.chroma_utils import generate_permalink, logger
from src.db.vector.vector_store import VectorStore


class ChromaVectorStore(VectorStore):
    """
    基于ChromaDB的向量存储

    使用ChromaDB作为后端的向量存储实现，提供简单易用的接口存储和检索开发资料。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储

        Args:
            config: 配置参数
        """
        super().__init__(config)

        # 初始化各个功能模块
        self.core = ChromaCore(self.config)
        self.search = ChromaSearch(self.core)
        self.batch = ChromaBatch(self.core)

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
        if metadata is None:
            metadata = [{} for _ in texts]

        # 确保元数据列表长度与文本列表相同
        if len(metadata) != len(texts):
            raise ValueError("元数据列表长度必须与文本列表长度相同")

        target_folder = folder or self.core.default_folder
        vector_store = self.core.get_or_create_collection(target_folder)

        permalinks = []
        documents = []

        # 准备文档和元数据
        for i, text in enumerate(texts):
            # 生成文档ID
            doc_id = str(uuid.uuid4())

            # 从元数据获取标题，或使用默认标题
            title = metadata[i].get("title", f"Document {i+1}")

            # 构建完整元数据
            full_metadata = {
                "title": title,
                "doc_id": doc_id,
                "content": text,  # 在元数据中也存储内容，确保可以直接从元数据获取
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": metadata[i].get("tags", self.core.default_tags),
                "folder": target_folder,
                **{k: v for k, v in metadata[i].items() if k not in ["title", "tags", "content"]},
            }

            # 创建Document对象
            doc = Document(page_content=text, metadata=full_metadata)
            documents.append(doc)

            # 生成永久链接
            permalink = generate_permalink(target_folder, doc_id)
            permalinks.append(permalink)

        # 添加文档到向量库
        vector_store.add_documents(documents)

        return permalinks

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
        return await self.search.semantic_search(query, limit, filter_dict)

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            id: 永久链接

        Returns:
            文档内容和元数据
        """
        return await self.core.get_document(id)

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
        # 使用批量更新接口更新单个文档
        result = await self.batch.batch_update([{"id": id, "content": content, "metadata": metadata}])

        return result["success"] and result["updated"] > 0

    async def delete(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 永久链接列表

        Returns:
            删除是否成功
        """
        return await self.core.delete_documents(ids)

    async def list_folders(self) -> List[str]:
        """
        列出所有文件夹

        Returns:
            文件夹列表
        """
        return await self.core.list_all_folders()

    async def list_documents(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夹中的所有文档

        Args:
            folder: 文件夹名称，如果为None则列出所有文件夹中的文档

        Returns:
            文档列表
        """
        return await self.core.list_all_documents(folder)

    async def get_stats(self, folder: Optional[str] = None) -> Dict[str, Any]:
        """
        获取向量库统计信息

        Args:
            folder: 文件夹名称，如果为None则获取所有文件夹的统计信息

        Returns:
            统计信息
        """
        return await self.core.get_collection_stats(folder)

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接是否正常

        Returns:
            测试结果
        """
        try:
            # 创建测试文件夹
            test_folder = "test"

            # 存储测试文档
            test_content = "这是一个测试文档，用于测试ChromaDB向量存储的连接。"
            test_title = "测试文档"

            # 存储测试文档
            permalinks = await self.store([test_content], [{"title": test_title, "tags": "test,connection"}], test_folder)

            if not permalinks:
                return {"success": False, "message": "存储测试失败：未返回永久链接"}

            test_permalink = permalinks[0]

            # 获取测试文档
            document = await self.get(test_permalink)

            # 搜索测试文档
            search_results = await self.search("测试文档", limit=1)

            # 获取统计信息
            stats = await self.get_stats(test_folder)

            # 删除测试文档
            delete_success = await self.delete([test_permalink])

            return {
                "success": True,
                "message": "ChromaDB连接测试成功",
                "details": {
                    "write_success": bool(permalinks),
                    "read_success": bool(document),
                    "search_success": bool(search_results),
                    "stats_success": bool(stats),
                    "delete_success": delete_success,
                },
            }
        except Exception as e:
            logger.error(f"ChromaDB连接测试失败: {e}")
            return {"success": False, "message": f"ChromaDB连接测试失败: {e}"}

    async def batch_store(
        self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None, folder: Optional[str] = None, batch_size: int = 100
    ) -> List[str]:
        """
        批量存储文本及元数据到向量库，提高大批量数据处理效率

        Args:
            texts: 要存储的文本列表
            metadata: 每个文本对应的元数据
            folder: 存储文件夹
            batch_size: 每批处理的文档数量

        Returns:
            存储后的永久链接列表
        """
        return await self.batch.batch_store(texts, metadata, folder, batch_size)

    async def batch_update(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新文档，每个项目包含id、content和metadata

        Args:
            items: 要更新的项目列表，每项包含id、content和metadata

        Returns:
            更新结果统计
        """
        return await self.batch.batch_update(items)

    async def hybrid_search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        混合检索，结合语义搜索和关键词搜索

        Args:
            query: 搜索查询
            limit: 返回结果数量
            filter_dict: 过滤条件
            keyword_weight: 关键词搜索的权重
            semantic_weight: 语义搜索的权重

        Returns:
            搜索结果列表
        """
        return await self.search.hybrid_search(query, limit, filter_dict, keyword_weight, semantic_weight)

"""
ChromaDB核心功能实现

提供ChromaDB核心功能实现，包括集合管理和文档操作。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from src.db.vector.chroma_utils import DEFAULT_DATA_DIR, generate_permalink, logger, parse_permalink


class ChromaCore:
    """
    ChromaDB核心功能类

    提供ChromaDB集合管理和基础文档操作功能。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化ChromaCore

        Args:
            config: 配置参数
        """
        self.config = config

        # 配置参数
        self.default_folder = self.config.get("default_folder", "vibecopilot")
        self.default_tags = self.config.get("default_tags", "vibecopilot")

        # 设置数据目录
        self.data_dir = self.config.get("data_dir", DEFAULT_DATA_DIR)
        os.makedirs(self.data_dir, exist_ok=True)

        # 实例ID用于区分不同实例，避免冲突
        instance_id = self.config.get("instance_id", "default")
        # 针对不同实例，可以使用不同的子目录
        instance_dir = os.path.join(self.data_dir, instance_id)
        os.makedirs(instance_dir, exist_ok=True)

        # 初始化嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
            cache_folder=os.path.join(self.data_dir, "models"),
        )

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=instance_dir, settings=Settings(anonymized_telemetry=False))

        # 存储文件夹映射到向量库的字典
        self.vector_stores = {}

        # 加载所有现有集合
        self._load_collections()

    def _load_collections(self):
        """加载所有现有集合"""
        logger.info(f"加载ChromaDB集合，数据目录: {self.data_dir}")

        try:
            # 获取所有集合名称（适配ChromaDB v0.6.0+）
            collection_names = self.client.list_collections()

            for collection in collection_names:
                # 在ChromaDB v0.6.0+中，list_collections只返回名称字符串
                # 而不是集合对象，所以collection就是名称字符串
                collection_name = collection

                try:
                    # 获取特定集合
                    chroma_collection = self.client.get_collection(name=collection_name)

                    # 初始化Langchain的Chroma包装器
                    self.vector_stores[collection_name] = Chroma(
                        client=self.client, collection_name=collection_name, embedding_function=self.embedding_model
                    )

                    logger.info(f"成功加载集合: {collection_name}")
                except Exception as e:
                    logger.error(f"加载集合 {collection_name} 失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"加载ChromaDB集合失败: {e}")

    def get_or_create_collection(self, folder: str) -> Chroma:
        """
        获取或创建ChromaDB集合

        Args:
            folder: 文件夹名称

        Returns:
            Chroma向量存储实例
        """
        if folder in self.vector_stores:
            return self.vector_stores[folder]

        # 创建新的集合
        logger.info(f"创建新的ChromaDB集合: {folder}")

        try:
            # 先检查集合是否存在
            collection_names = self.client.list_collections()

            if folder in collection_names:
                # 获取现有集合
                chroma_collection = self.client.get_collection(name=folder)
            else:
                # 创建新集合
                chroma_collection = self.client.create_collection(name=folder)

            # 创建Langchain包装器
            vector_store = Chroma(client=self.client, collection_name=folder, embedding_function=self.embedding_model)

            # 添加到内存中的存储映射
            self.vector_stores[folder] = vector_store

            return vector_store
        except Exception as e:
            logger.error(f"创建集合 {folder} 失败: {e}")
            # 创建一个基本的Chroma实例作为备选
            vector_store = Chroma(collection_name=folder, embedding_function=self.embedding_model, persist_directory=self.data_dir)
            self.vector_stores[folder] = vector_store
            return vector_store

    async def get_document(self, permalink: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            permalink: 永久链接

        Returns:
            文档内容和元数据
        """
        # 解析永久链接
        parsed = parse_permalink(permalink)
        if not parsed:
            return None

        folder, doc_id = parsed["folder"], parsed["doc_id"]

        # 检查集合是否存在
        if folder not in self.vector_stores:
            return None

        vector_store = self.vector_stores[folder]
        collection = vector_store._collection

        # 查询ChromaDB获取文档
        try:
            # 获取文档的所有内容，包括元数据、文档内容和嵌入向量
            result = collection.get(ids=[doc_id], include=["metadatas", "documents", "embeddings"])

            if not result["ids"]:
                return None

            # 获取元数据和文档内容
            metadata = result["metadatas"][0] if "metadatas" in result and result["metadatas"] else {}
            document = result["documents"][0] if "documents" in result and result["documents"] else ""
            embedding = result["embeddings"][0] if "embeddings" in result and result["embeddings"] else []

            # 确保内容存在
            content = document or metadata.get("content", "")

            # 如果元数据中没有内容，更新它
            if not metadata.get("content") and content:
                metadata["content"] = content

            return {"permalink": permalink, "content": content, "metadata": metadata, "embedding": embedding}
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None

    async def delete_documents(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 永久链接列表

        Returns:
            删除是否成功
        """
        if not ids:
            return True

        success = True

        # 按集合分组要删除的ID
        ids_by_folder = {}

        for id in ids:
            # 解析永久链接
            parsed = parse_permalink(id)
            if not parsed:
                success = False
                continue

            folder, doc_id = parsed["folder"], parsed["doc_id"]

            if folder not in ids_by_folder:
                ids_by_folder[folder] = []

            ids_by_folder[folder].append(doc_id)

        # 从每个集合中删除文档
        for folder, doc_ids in ids_by_folder.items():
            if folder not in self.vector_stores:
                success = False
                continue

            vector_store = self.vector_stores[folder]
            collection = vector_store._collection

            try:
                collection.delete(ids=doc_ids)
            except Exception as e:
                logger.error(f"从集合 {folder} 删除文档失败: {e}")
                success = False

        return success

    async def list_all_folders(self) -> List[str]:
        """
        列出所有文件夹

        Returns:
            文件夹列表
        """
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []

    async def list_all_documents(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夹中的所有文档

        Args:
            folder: 文件夹名称，如果为None则列出所有文件夹中的文档

        Returns:
            文档列表
        """
        results = []

        folders_to_list = [folder] if folder else await self.list_all_folders()

        for folder_name in folders_to_list:
            if folder_name not in self.vector_stores:
                continue

            vector_store = self.vector_stores[folder_name]
            collection = vector_store._collection

            try:
                # 获取集合中的所有文档
                result = collection.get(include=["metadatas"])

                for i, doc_id in enumerate(result["ids"]):
                    metadata = result["metadatas"][i]
                    permalink = generate_permalink(folder_name, doc_id)

                    results.append(
                        {
                            "permalink": permalink,
                            "title": metadata.get("title", "Untitled"),
                            "created_at": metadata.get("created_at", ""),
                            "updated_at": metadata.get("updated_at", ""),
                            "tags": metadata.get("tags", ""),
                            "folder": folder_name,
                        }
                    )
            except Exception as e:
                logger.error(f"列出集合 {folder_name} 中的文档失败: {e}")

        # 按更新时间排序
        results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return results

    async def get_collection_stats(self, folder: Optional[str] = None) -> Dict[str, Any]:
        """
        获取向量库统计信息

        Args:
            folder: 文件夹名称，如果为None则获取所有文件夹的统计信息

        Returns:
            统计信息
        """
        stats = {}
        folders = [folder] if folder else await self.list_all_folders()

        for folder_name in folders:
            if folder_name not in self.vector_stores:
                continue

            vector_store = self.vector_stores[folder_name]
            collection = vector_store._collection

            try:
                # 获取集合中的文档数量
                count = collection.count()

                # 获取集合中的文档元数据
                result = collection.get(include=["metadatas"])

                # 计算统计信息
                stats[folder_name] = {
                    "document_count": count,
                    "last_updated": result["metadatas"][0].get("updated_at", "") if result["metadatas"] else "",
                    "size_bytes": sum(len(m.get("content", "")) for m in result["metadatas"]) if result["metadatas"] else 0,
                }
            except Exception as e:
                logger.error(f"获取集合 {folder_name} 统计信息失败: {e}")
                stats[folder_name] = {"error": str(e)}

        return stats

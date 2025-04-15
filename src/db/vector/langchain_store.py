"""
基于Langchain的向量存储实现

使用Langchain和FAISS作为后端的向量存储实现。
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import faiss
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.db.vector.vector_store import VectorStore

logger = logging.getLogger(__name__)

# 默认数据目录
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), "Public", "VibeCopilot", "data", "vector_db")


class LangchainVectorStore(VectorStore):
    """
    基于Langchain的向量存储

    使用Langchain和FAISS作为后端的向量存储实现。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储

        Args:
            config: 配置参数
        """
        super().__init__(config)

        # 配置参数
        self.default_folder = self.config.get("default_folder", "vibecopilot")
        self.default_tags = self.config.get("default_tags", "vibecopilot")

        # 设置数据目录
        self.data_dir = self.config.get("data_dir", DEFAULT_DATA_DIR)
        os.makedirs(self.data_dir, exist_ok=True)

        # 初始化嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
            cache_folder=os.path.join(self.data_dir, "models"),
        )

        # 存储文件夹映射到向量库的字典
        self.vector_stores = {}

        # 用于存储元数据的字典
        self.metadata_stores = {}

        # 加载所有现有向量库
        self._load_vector_stores()

    def _load_vector_stores(self):
        """加载所有现有向量库"""
        logger.info(f"加载向量库，数据目录: {self.data_dir}")
        if not os.path.exists(self.data_dir):
            logger.warning(f"向量库数据目录不存在: {self.data_dir}")
            return

        folders = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d)) and not d.startswith(".")]

        for folder in folders:
            try:
                folder_path = os.path.join(self.data_dir, folder)
                index_path = os.path.join(folder_path, "faiss_index")
                metadata_path = os.path.join(folder_path, "metadata.json")

                # 检查索引文件是否存在
                if not os.path.exists(index_path):
                    logger.warning(f"向量库索引文件不存在: {index_path}")
                    continue

                # 加载向量库
                self.vector_stores[folder] = FAISS.load_local(folder_path=folder_path, index_name="faiss_index", embeddings=self.embedding_model)

                # 加载元数据
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        self.metadata_stores[folder] = json.load(f)
                else:
                    self.metadata_stores[folder] = {}

                logger.info(f"成功加载向量库: {folder}")
            except Exception as e:
                logger.error(f"加载向量库 {folder} 失败: {e}")

    def _get_or_create_vector_store(self, folder: str) -> FAISS:
        """获取或创建向量库"""
        if folder in self.vector_stores:
            return self.vector_stores[folder]

        # 创建新的向量库
        logger.info(f"创建新的向量库: {folder}")
        vector_store = FAISS.from_texts(texts=["初始化文档"], embedding=self.embedding_model)  # 需要至少一个文档

        # 保存向量库
        folder_path = os.path.join(self.data_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        vector_store.save_local(folder_path=folder_path, index_name="faiss_index")

        # 初始化元数据存储
        metadata_path = os.path.join(folder_path, "metadata.json")
        if not os.path.exists(metadata_path):
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

        # 添加到内存中的存储映射
        self.vector_stores[folder] = vector_store
        self.metadata_stores[folder] = {}

        return vector_store

    def _save_metadata(self, folder: str):
        """保存元数据到磁盘"""
        if folder not in self.metadata_stores:
            return

        folder_path = os.path.join(self.data_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        metadata_path = os.path.join(folder_path, "metadata.json")

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata_stores[folder], f, ensure_ascii=False, indent=2)

    def _generate_permalink(self, folder: str, doc_id: str) -> str:
        """生成永久链接"""
        return f"memory://{folder}/{doc_id}"

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

        target_folder = folder or self.default_folder
        vector_store = self._get_or_create_vector_store(target_folder)

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
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": metadata[i].get("tags", self.default_tags),
                "folder": target_folder,
                **metadata[i],
            }

            # 创建Document对象
            doc = Document(page_content=text, metadata=full_metadata)
            documents.append(doc)

            # 将文档元数据存储到元数据存储
            permalink = self._generate_permalink(target_folder, doc_id)
            self.metadata_stores.setdefault(target_folder, {})[doc_id] = {
                "content": text,
                "metadata": full_metadata,
                "permalink": permalink,
            }

            permalinks.append(permalink)

        # 添加文档到向量库
        vector_store.add_documents(documents)

        # 保存向量库
        folder_path = os.path.join(self.data_dir, target_folder)
        os.makedirs(folder_path, exist_ok=True)
        vector_store.save_local(folder_path=folder_path, index_name="faiss_index")

        # 保存元数据
        self._save_metadata(target_folder)

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
        results = []
        folders_to_search = []

        # 确定要搜索的文件夹
        if filter_dict and "folder" in filter_dict:
            folders_to_search = [filter_dict["folder"]]
        else:
            folders_to_search = list(self.vector_stores.keys())

        # 对每个文件夹进行搜索
        for folder in folders_to_search:
            if folder not in self.vector_stores:
                continue

            vector_store = self.vector_stores[folder]

            # 准备过滤器
            filter_func = None
            if filter_dict:

                def filter_func(doc):
                    for key, value in filter_dict.items():
                        if key == "folder":
                            continue  # 已经处理过
                        if key not in doc.metadata or doc.metadata[key] != value:
                            return False
                    return True

            # 执行搜索
            try:
                docs_with_scores = vector_store.similarity_search_with_score(query=query, k=limit, filter=filter_func)

                # 处理搜索结果
                for doc, score in docs_with_scores:
                    doc_id = doc.metadata.get("doc_id")
                    if not doc_id:
                        continue

                    permalink = self._generate_permalink(folder, doc_id)

                    # 将分数转换为0-1范围
                    normalized_score = 1.0 - min(score / 2.0, 1.0)  # FAISS返回的是距离，需要转换为相似性分数

                    results.append({"permalink": permalink, "content": doc.page_content, "metadata": {**doc.metadata, "score": normalized_score}})
            except Exception as e:
                logger.error(f"搜索向量库 {folder} 失败: {e}")

        # 按相似度得分排序
        results.sort(key=lambda x: x["metadata"].get("score", 0), reverse=True)

        # 限制结果数量
        if limit > 0:
            results = results[:limit]

        return results

    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            id: 永久链接

        Returns:
            文档内容和元数据
        """
        # 解析永久链接
        if not id.startswith("memory://"):
            return None

        parts = id[len("memory://") :].split("/", 1)
        if len(parts) != 2:
            return None

        folder, doc_id = parts

        # 检查文件夹是否存在
        if folder not in self.metadata_stores:
            return None

        # 从元数据存储中获取文档
        if doc_id not in self.metadata_stores[folder]:
            return None

        doc_data = self.metadata_stores[folder][doc_id]

        return {"permalink": id, "content": doc_data["content"], "metadata": doc_data["metadata"]}

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
        # 解析永久链接
        if not id.startswith("memory://"):
            return False

        parts = id[len("memory://") :].split("/", 1)
        if len(parts) != 2:
            return False

        folder, doc_id = parts

        # 检查文件夹是否存在
        if folder not in self.metadata_stores or folder not in self.vector_stores:
            return False

        # 从元数据存储中获取文档
        if doc_id not in self.metadata_stores[folder]:
            return False

        # 获取原始元数据
        original_metadata = self.metadata_stores[folder][doc_id]["metadata"]

        # 更新元数据
        updated_metadata = {**original_metadata, **metadata}
        updated_metadata["updated_at"] = datetime.now().isoformat()

        # 创建新的Document对象
        doc = Document(page_content=content, metadata=updated_metadata)

        # 更新向量库
        # 注意：FAISS不支持直接更新，需要先删除再插入
        vector_store = self.vector_stores[folder]

        # 由于FAISS没有提供删除单个文档的方法，我们需要重建向量库
        # 获取所有文档
        all_docs = []
        for doc_key, doc_data in self.metadata_stores[folder].items():
            if doc_key == doc_id:
                continue  # 跳过要更新的文档

            d = Document(page_content=doc_data["content"], metadata=doc_data["metadata"])
            all_docs.append(d)

        # 添加更新后的文档
        all_docs.append(doc)

        # 重建向量库
        new_vector_store = FAISS.from_documents(documents=all_docs, embedding=self.embedding_model)

        # 替换旧的向量库
        self.vector_stores[folder] = new_vector_store

        # 更新元数据存储
        self.metadata_stores[folder][doc_id] = {"content": content, "metadata": updated_metadata, "permalink": id}

        # 保存向量库
        folder_path = os.path.join(self.data_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        new_vector_store.save_local(folder_path=folder_path, index_name="faiss_index")

        # 保存元数据
        self._save_metadata(folder)

        return True

    async def delete(self, ids: List[str]) -> bool:
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
        folders_to_update = set()

        for id in ids:
            # 解析永久链接
            if not id.startswith("memory://"):
                success = False
                continue

            parts = id[len("memory://") :].split("/", 1)
            if len(parts) != 2:
                success = False
                continue

            folder, doc_id = parts

            # 检查文件夹是否存在
            if folder not in self.metadata_stores or folder not in self.vector_stores:
                success = False
                continue

            # 从元数据存储中删除文档
            if doc_id in self.metadata_stores[folder]:
                del self.metadata_stores[folder][doc_id]
                folders_to_update.add(folder)

        # 更新受影响的向量库
        for folder in folders_to_update:
            # 获取所有文档
            all_docs = []
            for doc_data in self.metadata_stores[folder].values():
                doc = Document(page_content=doc_data["content"], metadata=doc_data["metadata"])
                all_docs.append(doc)

            # 如果没有文档，创建一个空的向量库
            if not all_docs:
                all_docs = [Document(page_content="初始化文档", metadata={"title": "初始化文档"})]

            # 重建向量库
            new_vector_store = FAISS.from_documents(documents=all_docs, embedding=self.embedding_model)

            # 替换旧的向量库
            self.vector_stores[folder] = new_vector_store

            # 保存向量库
            folder_path = os.path.join(self.data_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            new_vector_store.save_local(folder_path=folder_path, index_name="faiss_index")

            # 保存元数据
            self._save_metadata(folder)

        return success

    async def list_folders(self) -> List[str]:
        """
        列出所有文件夹

        Returns:
            文件夹列表
        """
        return list(self.vector_stores.keys())

    async def list_documents(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夹中的所有文档

        Args:
            folder: 文件夹名称，如果为None则列出所有文件夹中的文档

        Returns:
            文档列表
        """
        results = []

        folders_to_list = [folder] if folder else list(self.metadata_stores.keys())

        for folder_name in folders_to_list:
            if folder_name not in self.metadata_stores:
                continue

            for doc_id, doc_data in self.metadata_stores[folder_name].items():
                permalink = self._generate_permalink(folder_name, doc_id)
                results.append(
                    {
                        "permalink": permalink,
                        "title": doc_data["metadata"].get("title", "Untitled"),
                        "created_at": doc_data["metadata"].get("created_at", ""),
                        "updated_at": doc_data["metadata"].get("updated_at", ""),
                        "tags": doc_data["metadata"].get("tags", ""),
                        "folder": folder_name,
                    }
                )

        # 按更新时间排序
        results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return results

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
            test_content = "这是一个测试文档，用于测试向量存储的连接。"
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

            # 删除测试文档
            delete_success = await self.delete([test_permalink])

            return {
                "success": True,
                "message": "连接测试成功",
                "details": {
                    "write_success": bool(permalinks),
                    "read_success": bool(document),
                    "search_success": bool(search_results),
                    "delete_success": delete_success,
                },
            }
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return {"success": False, "message": f"连接测试失败: {e}"}

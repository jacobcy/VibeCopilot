#!/usr/bin/env python3
"""
向量存储管理模块
管理文档的向量化和检索
"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Union

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from adapters.basic_memory.utils.api_utils import get_openai_api_key


class VectorManager:
    """向量存储管理器

    负责文档的向量化存储和检索
    """

    def __init__(self, index_path: Union[str, Path], model: str = "gpt-4o-mini"):
        """初始化向量管理器

        Args:
            index_path: 向量索引保存路径
            model: 使用的模型名称
        """
        self.index_path = Path(index_path) if isinstance(index_path, str) else index_path
        self.model = model

        # 确保API密钥已设置
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("错误: 未设置OPENAI_API_KEY环境变量")

        # 创建嵌入模型
        self.embeddings = OpenAIEmbeddings()

        # 创建索引目录（如果不存在）
        os.makedirs(self.index_path, exist_ok=True)

    def create_vector_store(self, chunks: List[str]) -> FAISS:
        """创建向量存储

        Args:
            chunks: 文本块列表

        Returns:
            FAISS: 向量存储对象
        """
        print(f"创建向量存储，处理 {len(chunks)} 个文本块")

        if not chunks:
            raise ValueError("错误: 没有提供文本块")

        # 创建向量存储
        vector_store = FAISS.from_texts(chunks, self.embeddings)
        return vector_store

    def save_vector_store(self, vector_store: FAISS, name: str = "index") -> str:
        """保存向量存储

        Args:
            vector_store: 向量存储对象
            name: 索引名称

        Returns:
            str: 保存路径
        """
        save_path = self.index_path
        print(f"保存向量存储到: {save_path}")

        # 确保目录存在
        os.makedirs(save_path, exist_ok=True)

        # 保存向量存储
        vector_store.save_local(str(save_path))

        # 创建元数据文件
        metadata = {
            "chunks_count": len(vector_store.index_to_docstore_id),
            "model": self.model,
            "created_at": os.path.getmtime(save_path / "index.faiss")
            if (save_path / "index.faiss").exists()
            else None,
        }

        metadata_path = save_path / "metadata.pkl"
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)

        return str(save_path)

    def load_vector_store(self, path: Optional[str] = None) -> FAISS:
        """加载向量存储

        Args:
            path: 向量存储路径，默认使用初始化时的路径

        Returns:
            FAISS: 向量存储对象
        """
        load_path = Path(path) if path else self.index_path
        print(f"加载向量存储: {load_path}")

        if not (load_path / "index.faiss").exists():
            raise FileNotFoundError(f"向量索引文件不存在: {load_path / 'index.faiss'}")

        # 加载向量存储
        vector_store = FAISS.load_local(
            str(load_path), self.embeddings, allow_dangerous_deserialization=True
        )

        # 尝试加载元数据
        try:
            metadata_path = load_path / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, "rb") as f:
                    metadata = pickle.load(f)
                print(
                    f"向量存储信息: {metadata.get('chunks_count', '未知')} 个块, "
                    f"模型: {metadata.get('model', '未知')}"
                )
        except Exception as e:
            print(f"读取元数据失败: {e}")

        return vector_store

    def similarity_search(self, query: str, k: int = 5) -> List[str]:
        """相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            List[str]: 相似文本列表
        """
        # 加载向量存储
        vector_store = self.load_vector_store()

        # 执行搜索
        results = vector_store.similarity_search(query, k=k)

        # 提取文本
        texts = [doc.page_content for doc in results]
        return texts

    def get_vector_store_stats(self) -> Dict:
        """获取向量存储统计信息

        Returns:
            Dict: 统计信息
        """
        stats = {
            "exists": False,
            "chunks_count": 0,
            "model": self.model,
            "size_mb": 0,
            "created_at": None,
        }

        index_file = self.index_path / "index.faiss"
        if not index_file.exists():
            return stats

        stats["exists"] = True
        stats["size_mb"] = index_file.stat().st_size / (1024 * 1024)
        stats["created_at"] = os.path.getmtime(index_file)

        # 尝试加载元数据
        try:
            metadata_path = self.index_path / "metadata.pkl"
            if metadata_path.exists():
                with open(metadata_path, "rb") as f:
                    metadata = pickle.load(f)
                stats.update(metadata)
        except Exception:
            pass

        return stats

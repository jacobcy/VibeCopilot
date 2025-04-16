"""
ChromaDB搜索功能实现

提供ChromaDB搜索功能实现，包括基础搜索和混合搜索。
"""

import logging
from typing import Any, Dict, List, Optional

from src.memory.vector.chroma_utils import create_chroma_filter, generate_permalink, logger


class ChromaSearch:
    """
    ChromaDB搜索功能类

    提供ChromaDB搜索功能，包括语义搜索和混合搜索。
    """

    def __init__(self, chroma_core):
        """
        初始化ChromaSearch

        Args:
            chroma_core: ChromaCore实例
        """
        self.core = chroma_core

    async def semantic_search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索向量库

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
            folders_to_search = list(self.core.vector_stores.keys())

        # 准备ChromaDB格式的过滤器
        chroma_filter = create_chroma_filter(filter_dict)

        # 对每个文件夹进行搜索
        for folder in folders_to_search:
            if folder not in self.core.vector_stores:
                continue

            vector_store = self.core.vector_stores[folder]

            try:
                # 执行搜索
                docs_with_scores = vector_store.similarity_search_with_relevance_scores(query=query, k=limit, filter=chroma_filter)

                # 处理搜索结果
                for doc, score in docs_with_scores:
                    doc_id = doc.metadata.get("doc_id")
                    if not doc_id:
                        continue

                    permalink = generate_permalink(folder, doc_id)

                    results.append({"permalink": permalink, "content": doc.page_content, "metadata": {**doc.metadata, "score": score}})
            except Exception as e:
                logger.error(f"搜索集合 {folder} 失败: {e}")

        # 按相似度得分排序
        results.sort(key=lambda x: x["metadata"].get("score", 0), reverse=True)

        # 限制结果数量
        if limit > 0:
            results = results[:limit]

        return results

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
        # 参数验证
        if keyword_weight + semantic_weight != 1.0:
            logger.warning("权重和不为1.0，已自动归一化")
            total = keyword_weight + semantic_weight
            keyword_weight /= total
            semantic_weight /= total

        # 确定要搜索的文件夹
        folders_to_search = []
        if filter_dict and "folder" in filter_dict:
            folders_to_search = [filter_dict["folder"]]
        else:
            folders_to_search = await self.core.list_all_folders()

        # 准备ChromaDB格式的过滤器
        chroma_filter = create_chroma_filter(filter_dict)

        all_results = {}

        # 对每个文件夹进行搜索
        for folder in folders_to_search:
            if folder not in self.core.vector_stores:
                continue

            vector_store = self.core.vector_stores[folder]
            collection = vector_store._collection

            try:
                # 1. 语义搜索
                semantic_results = collection.query(
                    query_texts=[query], n_results=limit * 2, where=chroma_filter, include=["metadatas", "documents", "distances"]  # 获取更多结果，稍后会合并
                )

                # 2. 关键词搜索（使用文本相似度作为替代）
                # 获取所有文档，然后在Python中进行关键词匹配
                all_docs = collection.get(where=chroma_filter, include=["metadatas", "documents", "ids"])

                # 计算关键词匹配分数
                keyword_scores = {}
                keywords = set(query.lower().split())

                for i, doc in enumerate(all_docs["documents"]):
                    if not doc:
                        continue

                    doc_id = all_docs["ids"][i]

                    # 简单的TF-IDF启发式计算
                    doc_text = doc.lower()
                    score = 0

                    for keyword in keywords:
                        if keyword in doc_text:
                            # 计算词频
                            count = doc_text.count(keyword)
                            # 这里可以更复杂，但简单起见，我们只计算出现次数
                            score += count

                    if score > 0:
                        keyword_scores[doc_id] = score

                # 获取关键词得分排序后的ID列表
                sorted_keyword_ids = sorted(keyword_scores.keys(), key=lambda k: keyword_scores[k], reverse=True)[: limit * 2]

                # 3. 合并两种搜索结果
                for i, doc_id in enumerate(semantic_results["ids"][0]):
                    if i >= len(semantic_results["metadatas"][0]):
                        continue

                    metadata = semantic_results["metadatas"][0][i]
                    document = semantic_results["documents"][0][i]
                    distance = semantic_results["distances"][0][i]

                    # 计算语义相似度得分
                    semantic_score = 1.0 - min(distance, 1.0)  # 转换距离为相似度

                    # 计算关键词得分（归一化）
                    keyword_score = 0
                    if doc_id in keyword_scores:
                        max_keyword_score = max(keyword_scores.values()) if keyword_scores else 1
                        keyword_score = keyword_scores[doc_id] / max_keyword_score

                    # 计算混合得分
                    hybrid_score = (keyword_weight * keyword_score) + (semantic_weight * semantic_score)

                    # 生成永久链接
                    permalink = generate_permalink(folder, doc_id)

                    # 添加到结果中
                    all_results[permalink] = {
                        "permalink": permalink,
                        "content": document,
                        "metadata": {**metadata, "hybrid_score": hybrid_score, "semantic_score": semantic_score, "keyword_score": keyword_score},
                    }

                # 处理仅在关键词搜索中找到的结果
                for doc_id in sorted_keyword_ids:
                    permalink = generate_permalink(folder, doc_id)

                    # 避免重复添加
                    if permalink in all_results:
                        continue

                    # 找到原始文档数据
                    doc_index = all_docs["ids"].index(doc_id)
                    document = all_docs["documents"][doc_index]
                    metadata = all_docs["metadatas"][doc_index]

                    # 计算混合得分
                    max_keyword_score = max(keyword_scores.values()) if keyword_scores else 1
                    keyword_score = keyword_scores[doc_id] / max_keyword_score

                    # 关键词搜索结果没有语义得分，只使用关键词得分
                    hybrid_score = keyword_weight * keyword_score

                    all_results[permalink] = {
                        "permalink": permalink,
                        "content": document,
                        "metadata": {**metadata, "hybrid_score": hybrid_score, "semantic_score": 0.0, "keyword_score": keyword_score},
                    }
            except Exception as e:
                logger.error(f"混合搜索集合 {folder} 失败: {e}")

        # 按混合得分排序
        sorted_results = sorted(all_results.values(), key=lambda x: x["metadata"].get("hybrid_score", 0), reverse=True)

        # 限制结果数量
        if limit > 0:
            sorted_results = sorted_results[:limit]

        return sorted_results

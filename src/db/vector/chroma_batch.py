"""
ChromaDB批量操作功能实现

提供ChromaDB批量存储和更新功能实现。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from src.db.vector.chroma_utils import generate_permalink, logger, parse_permalink


class ChromaBatch:
    """
    ChromaDB批量操作功能类

    提供ChromaDB批量存储和更新功能。
    """

    def __init__(self, chroma_core):
        """
        初始化ChromaBatch

        Args:
            chroma_core: ChromaCore实例
        """
        self.core = chroma_core

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
        if not texts:
            return []

        if metadata is None:
            metadata = [{} for _ in texts]

        # 确保元数据列表长度与文本列表相同
        if len(metadata) != len(texts):
            raise ValueError("元数据列表长度必须与文本列表长度相同")

        target_folder = folder or self.core.default_folder
        vector_store = self.core.get_or_create_collection(target_folder)

        all_permalinks = []

        # 按批次处理文档
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_metadata = metadata[i : i + batch_size]

            batch_permalinks = []
            batch_documents = []
            batch_ids = []
            batch_metadata_list = []

            # 准备批量文档数据
            for j, text in enumerate(batch_texts):
                # 生成文档ID
                doc_id = str(uuid.uuid4())
                batch_ids.append(doc_id)

                # 从元数据获取标题，或使用默认标题
                title = batch_metadata[j].get("title", f"Document {i+j+1}")

                # 构建完整元数据
                full_metadata = {
                    "title": title,
                    "doc_id": doc_id,
                    "content": text,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": batch_metadata[j].get("tags", self.core.default_tags),
                    "folder": target_folder,
                    **{k: v for k, v in batch_metadata[j].items() if k not in ["title", "tags", "content"]},
                }

                batch_metadata_list.append(full_metadata)

                # 创建Document对象供Langchain使用
                doc = Document(page_content=text, metadata=full_metadata)
                batch_documents.append(doc)

                # 生成永久链接
                permalink = generate_permalink(target_folder, doc_id)
                batch_permalinks.append(permalink)

            # 添加批量文档到向量库
            try:
                logger.info(f"批量添加 {len(batch_texts)} 个文档到集合 {target_folder}")

                # 使用原始ChromaDB集合进行批量添加
                collection = vector_store._collection
                collection.add(ids=batch_ids, documents=batch_texts, metadatas=batch_metadata_list)

                all_permalinks.extend(batch_permalinks)
            except Exception as e:
                logger.error(f"批量添加文档失败: {e}")
                # 发生错误时回退到常规添加方式
                vector_store.add_documents(batch_documents)
                all_permalinks.extend(batch_permalinks)

        return all_permalinks

    async def batch_update(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新文档，每个项目包含id、content和metadata

        Args:
            items: 要更新的项目列表，每项包含id、content和metadata

        Returns:
            更新结果统计
        """
        if not items:
            return {"success": True, "total": 0, "updated": 0, "failed": 0}

        # 按文件夹分组
        updates_by_folder = {}

        for item in items:
            id = item.get("id")
            content = item.get("content", "")
            metadata = item.get("metadata", {})

            # 解析永久链接
            parsed = parse_permalink(id)
            if not parsed:
                continue

            folder, doc_id = parsed["folder"], parsed["doc_id"]

            if folder not in updates_by_folder:
                updates_by_folder[folder] = []

            updates_by_folder[folder].append({"doc_id": doc_id, "content": content, "metadata": metadata})

        total_count = len(items)
        updated_count = 0
        failed_count = 0

        # 按文件夹批量更新
        for folder, updates in updates_by_folder.items():
            if folder not in self.core.vector_stores:
                failed_count += len(updates)
                continue

            vector_store = self.core.vector_stores[folder]
            collection = vector_store._collection

            try:
                # 准备批量更新数据
                ids = [update["doc_id"] for update in updates]
                documents = [update["content"] for update in updates]

                # 获取现有元数据
                existing_result = collection.get(ids=ids, include=["metadatas"])

                # 准备更新后的元数据
                metadatas = []
                for i, update in enumerate(updates):
                    if i < len(existing_result["metadatas"]):
                        # 更新现有元数据
                        original_metadata = existing_result["metadatas"][i]
                        updated_metadata = {**original_metadata, **update["metadata"]}
                        updated_metadata["updated_at"] = datetime.now().isoformat()
                        updated_metadata["content"] = update["content"]
                        metadatas.append(updated_metadata)
                    else:
                        # 没有找到现有元数据，使用新提供的
                        metadata = {**update["metadata"]}
                        metadata["updated_at"] = datetime.now().isoformat()
                        metadata["content"] = update["content"]
                        metadatas.append(metadata)

                # 批量更新
                collection.update(ids=ids, documents=documents, metadatas=metadatas)

                updated_count += len(updates)
            except Exception as e:
                logger.error(f"批量更新文档失败: {e}")
                failed_count += len(updates)

        return {"success": failed_count == 0, "total": total_count, "updated": updated_count, "failed": failed_count}

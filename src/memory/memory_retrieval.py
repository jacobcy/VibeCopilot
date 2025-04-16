"""
记忆检索模块

提供基于向量搜索的记忆检索功能
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.memory_formatter import MemoryFormatter
from src.memory.memory_utils import extract_original_content, format_error_response, format_success_response
from src.memory.vector.chroma_vector_store import ChromaVectorStore
from src.parsing.processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """记忆检索类"""

    def __init__(
        self,
        doc_processor: DocumentProcessor,
        vector_store: ChromaVectorStore,
        memory_item_repo: MemoryItemRepository,
        memory_formatter: MemoryFormatter,
        default_folder: str = "knowledge",
    ):
        """
        初始化记忆检索

        Args:
            doc_processor: 文档处理器
            vector_store: 向量存储
            memory_item_repo: 记忆项仓库
            memory_formatter: 记忆格式化工具
            default_folder: 默认文件夹
        """
        self.doc_processor = doc_processor
        self.vector_store = vector_store
        self.memory_item_repo = memory_item_repo
        self.memory_formatter = memory_formatter
        self.default_folder = default_folder

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
        try:
            # 使用混合搜索 - 修复过滤条件格式
            results = await self.vector_store.hybrid_search(
                query=query, limit=limit, filter_dict={"$eq": {"content_type": "memory"}}, keyword_weight=0.3, semantic_weight=0.7
            )

            # 格式化结果
            memories = []
            for result in results:
                memory_data = self.memory_formatter.format_search_result(result)
                memories.append(memory_data)

            # 如果没有找到结果，尝试使用实体搜索
            if not memories:
                memories = await self._fallback_entity_search(query, limit)

            return format_success_response(f"找到 {len(memories)} 条相关记忆", {"memories": memories, "query": query})

        except Exception as e:
            logger.error(f"召回记忆失败: {e}")
            return format_error_response(f"召回记忆失败: {str(e)}")

    async def _fallback_entity_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        实体回退搜索

        当向量搜索失败时，尝试使用实体进行搜索

        Args:
            query: 查询文本
            limit: 返回结果数量

        Returns:
            记忆列表
        """
        # 解析查询中的实体
        parse_result = self.doc_processor.process_document_text(query)
        entities = parse_result.get("entities", [])

        memories = []

        if entities:
            # 使用实体查询
            entity_names = [e.get("name", "") for e in entities if e.get("name")]
            entity_query = ", ".join(entity_names)

            # 如果存在实体，进行搜索 - 修复过滤条件格式
            if entity_query:
                results = await self.vector_store.search(query=entity_query, limit=limit, filter_dict={"$eq": {"content_type": "memory"}})

                # 处理结果
                for result in results:
                    memory_data = self.memory_formatter.format_search_result(result)
                    memories.append(memory_data)

        return memories

    async def get_memory_by_id(self, permalink: str) -> Dict[str, Any]:
        """
        通过ID获取记忆

        Args:
            permalink: 记忆永久链接

        Returns:
            记忆内容
        """
        try:
            logger.info(f"获取记忆: {permalink}")

            # 先尝试从MemoryItem中获取
            memory_item = self.memory_item_repo.find_by_permalink(permalink)

            if memory_item:
                logger.info(f"从SQLite找到记忆: {permalink}")
                memory = self.memory_formatter.format_memory_from_item(memory_item)

                return format_success_response("成功获取记忆", {"memory": memory})

            # 如果SQLite中没有，则从向量库获取
            doc = await self.vector_store.get(permalink)

            if not doc:
                logger.error(f"未找到记忆: {permalink}")
                return format_error_response(f"未找到记忆: {permalink}")

            # 记录更多信息以进行诊断
            logger.info(f"成功获取记忆: {permalink}")
            logger.info(f"记忆元数据: {doc.get('metadata', {})}")

            # 格式化记忆数据
            memory = self.memory_formatter.format_memory_from_vector(doc, permalink)

            # 尝试创建MemoryItem记录（如果不存在）
            memory_item_id = memory.get("memory_item_id")
            if not memory_item_id:
                # 创建新的MemoryItem记录
                await self._create_missing_memory_item(doc, permalink, memory)

            return format_success_response("成功获取记忆", {"memory": memory})

        except Exception as e:
            error_msg = f"获取记忆失败: {e}"
            logger.error(error_msg, exc_info=True)
            return format_error_response(error_msg)

    async def _create_missing_memory_item(self, doc: Dict[str, Any], permalink: str, memory: Dict[str, Any]) -> None:
        """
        创建缺失的记忆项

        当向量库中找到记忆但SQLite中没有对应记录时，创建新记录

        Args:
            doc: 向量库文档
            permalink: 永久链接
            memory: 记忆数据
        """
        content = memory.get("content", "")
        title = memory.get("title", "未命名记忆")
        metadata = doc.get("metadata", {})

        # 创建新的MemoryItem
        tags = metadata.get("tags", "")
        folder = metadata.get("folder", self.default_folder)
        entity_count = metadata.get("entity_count", 0)
        relation_count = metadata.get("relation_count", 0)
        observation_count = metadata.get("observation_count", 0)

        new_memory_item = self.memory_item_repo.create_item(
            title=title,
            content=content,
            content_type="memory",
            tags=tags,
            source="vector_store",
            permalink=permalink,
            folder=folder,
        )

        # 更新记忆数据和向量库元数据
        memory["memory_item_id"] = new_memory_item.id
        metadata["memory_item_id"] = new_memory_item.id
        await self.vector_store.update_metadata(permalink, metadata)

    async def list_memories(self, folder: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """
        列出所有记忆

        Args:
            folder: 文件夹名称
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        try:
            target_folder = folder or self.default_folder

            # 首先从SQLite获取记忆列表
            memory_items = self.memory_item_repo.find_by_folder(target_folder, limit)

            # 如果SQLite中有足够的记录，直接返回
            if memory_items and len(memory_items) > 0:
                memories = []
                for item in memory_items:
                    memory_data = self.memory_formatter.format_list_item(item)
                    memories.append(memory_data)

                return format_success_response(f"找到 {len(memories)} 条记忆", {"memories": memories, "folder": target_folder, "source": "sqlite"})

            # 如果SQLite中没有足够的记录，从向量库获取
            all_docs = await self.vector_store.list_documents(target_folder)

            memories = []
            for doc in all_docs:
                if doc.get("metadata", {}).get("content_type") == "memory":
                    memory_data = self.memory_formatter.format_list_item(doc)
                    memories.append(memory_data)

                    # 同步创建MemoryItem记录
                    await self._sync_missing_memory_item(doc, target_folder)

                    if len(memories) >= limit:
                        break

            return format_success_response(f"找到 {len(memories)} 条记忆", {"memories": memories, "folder": target_folder, "source": "vector_store"})

        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            return format_error_response(f"列出记忆失败: {str(e)}")

    async def _sync_missing_memory_item(self, doc: Dict[str, Any], folder: str) -> None:
        """
        同步缺失的记忆项

        当列出记忆时，如果发现向量库中存在但SQLite中没有的记录，创建新记录

        Args:
            doc: 向量库文档
            folder: 文件夹
        """
        permalink = doc.get("permalink", "")
        metadata = doc.get("metadata", {})
        memory_item_id = metadata.get("memory_item_id")

        # 如果没有memory_item_id或找不到对应记录，创建新的MemoryItem
        if not memory_item_id:
            # 检查是否存在相同permalink的记录
            existing_item = self.memory_item_repo.find_by_permalink(permalink)
            if not existing_item:
                # 创建新的MemoryItem
                title = doc.get("title", "未命名记忆")
                content = ""  # 需要单独获取内容
                tags = doc.get("tags", "")
                entity_count = metadata.get("entity_count", 0)
                relation_count = metadata.get("relation_count", 0)
                observation_count = metadata.get("observation_count", 0)

                self.memory_item_repo.create_item(
                    title=title,
                    content=content,  # 暂时为空，需要单独获取
                    content_type="memory",
                    tags=tags,
                    source="vector_store",
                    permalink=permalink,
                    folder=folder,
                )

    async def _search_memory(self, query: str, limit: int = 5, filter_content_type: bool = True) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            limit: 返回结果数量
            filter_content_type: 是否按内容类型过滤

        Returns:
            记忆列表
        """
        if not query:
            return []

        try:
            # 构建过滤条件
            filter_dict = {}
            if filter_content_type:
                # 正确使用$eq格式来设置content_type过滤条件
                filter_dict = {"$eq": {"content_type": "memory"}}

            # 执行混合搜索
            results = await self.vector_store.hybrid_search(
                query=query, limit=limit, filter_dict=filter_dict, keyword_weight=0.3, semantic_weight=0.7
            )

            if not results:
                return []

            # 转换结果格式
            memories = []
            for item in results:
                permalink = item.get("permalink", "")
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                score = metadata.get("hybrid_score", 0)

                # 创建Memory对象
                memory = {
                    "permalink": permalink,
                    "content": content,
                    "metadata": metadata,
                    "score": score,
                }

                memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []

    async def search_entity(self, entity_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索实体

        Args:
            entity_query: 实体搜索查询
            limit: 返回结果数量

        Returns:
            实体列表
        """
        if not entity_query:
            return []

        try:
            # 构建过滤条件 - 正确使用$eq格式
            filter_dict = {"$eq": {"content_type": "memory"}}

            # 执行检索
            results = await self.vector_store.search(query=entity_query, limit=limit, filter_dict=filter_dict)

            if not results:
                return []

            # 转换结果格式
            entities = []
            for item in results:
                permalink = item.get("permalink", "")
                content = item.get("content", "")
                metadata = item.get("metadata", {})

                # 创建Entity对象
                entity = {
                    "permalink": permalink,
                    "content": content,
                    "metadata": metadata,
                }

                entities.append(entity)

            return entities
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return []

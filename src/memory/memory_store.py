"""
记忆存储模块

提供记忆存储和删除功能
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.chroma_vector_store import ChromaVectorStore
from src.memory.entity_manager import EntityManager
from src.memory.memory_formatter import MemoryFormatter
from src.memory.memory_utils import create_enhanced_text, create_memory_metadata, format_error_response, format_success_response
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.parsing.processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class MemoryStore:
    """记忆存储类"""

    def __init__(
        self,
        doc_processor: DocumentProcessor,
        vector_store: ChromaVectorStore,
        entity_manager: EntityManager,
        relation_manager: RelationManager,
        observation_manager: ObservationManager,
        memory_item_repo: MemoryItemRepository,
        memory_formatter: MemoryFormatter,
        default_folder: str = "knowledge",
        default_tags: str = "memory,knowledge",
    ):
        """
        初始化记忆存储

        Args:
            doc_processor: 文档处理器
            vector_store: 向量存储
            entity_manager: 实体管理器
            relation_manager: 关系管理器
            observation_manager: 观察管理器
            memory_item_repo: 记忆项仓库
            memory_formatter: 记忆格式化工具
            default_folder: 默认文件夹
            default_tags: 默认标签
        """
        self.doc_processor = doc_processor
        self.vector_store = vector_store
        self.entity_manager = entity_manager
        self.relation_manager = relation_manager
        self.observation_manager = observation_manager
        self.memory_item_repo = memory_item_repo
        self.memory_formatter = memory_formatter
        self.default_folder = default_folder
        self.default_tags = default_tags

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
        try:
            # 使用指定的文件夹或默认文件夹
            target_folder = folder or self.default_folder

            # 1. 解析文档内容
            parse_result = self.doc_processor.process_document_text(content)

            if not parse_result.get("success", False):
                return format_error_response(f"解析内容失败: {parse_result.get('error', '未知错误')}", None)

            # 获取解析结果的标题或使用提供的标题
            memory_title = title or parse_result.get("title", "未命名记忆")
            memory_tags = tags or self.default_tags

            # 2. 提取实体、关系和观察
            entities = parse_result.get("entities", [])
            relations = parse_result.get("relations", [])
            observations = parse_result.get("observations", [])

            # 3. 创建增强文本
            enhanced_text = create_enhanced_text(memory_title, entities, relations, content)

            # 4. 先创建MemoryItem记录
            memory_item = self.memory_item_repo.create(
                title=memory_title,
                content=content,
                content_type="memory",
                tags=memory_tags,
                source="vector_store",
                # 向量库字段暂时为空，稍后更新
                folder=target_folder,
                entity_count=len(entities),
                relation_count=len(relations),
                observation_count=len(observations),
            )

            # 5. 存储到向量库
            metadata = create_memory_metadata(memory_title, memory_tags, entities, relations, observations, target_folder, memory_item.id)

            permalinks = await self.vector_store.store(texts=[enhanced_text], metadata=[metadata], folder=target_folder)

            if not permalinks:
                return format_error_response("存储到向量库失败", None)

            permalink = permalinks[0]

            # 6. 更新MemoryItem的向量库信息
            self.memory_item_repo.update_vector_info(
                memory_item_id=memory_item.id,
                permalink=permalink,
                folder=target_folder,
                entity_count=len(entities),
                relation_count=len(relations),
                observation_count=len(observations),
            )

            # 7. 存储实体、关系和观察
            await self._store_related_items(entities, relations, observations, permalink, memory_title)

            return format_success_response(
                f"成功存储记忆: {memory_title}",
                {
                    "permalink": permalink,
                    "memory_item_id": memory_item.id,
                    "entity_count": len(entities),
                    "relation_count": len(relations),
                    "observation_count": len(observations),
                    "folder": target_folder,
                },
            )

        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            return format_error_response(f"存储记忆失败: {str(e)}", None)

    async def _store_related_items(self, entities: list, relations: list, observations: list, permalink: str, context: str):
        """
        存储相关项（实体、关系、观察）

        Args:
            entities: 实体列表
            relations: 关系列表
            observations: 观察列表
            permalink: 永久链接
            context: 上下文（一般为记忆标题）
        """
        # 存储实体
        for entity in entities:
            # 添加源信息
            entity["source"] = permalink
            entity["context"] = context
            await self.entity_manager.create_entity(entity)

        # 存储关系
        for relation in relations:
            # 添加源信息
            relation["source"] = permalink
            relation["context"] = context
            await self.relation_manager.create_relation(relation)

        # 存储观察
        for observation in observations:
            # 添加源信息
            observation["source"] = permalink
            observation["context"] = context
            await self.observation_manager.create_observation(observation)

    async def delete_memory(self, permalink: str) -> Dict[str, Any]:
        """
        删除记忆

        Args:
            permalink: 记忆永久链接

        Returns:
            删除结果
        """
        try:
            # 先查找相关的MemoryItem
            memory_item = self.memory_item_repo.find_by_permalink(permalink)
            title = "未知记忆"

            if memory_item:
                title = memory_item.title

            # 删除向量库中的记忆
            success = await self.vector_store.delete([permalink])

            if not success:
                return format_error_response(f"删除向量库记忆失败: {permalink}")

            # 删除关联的MemoryItem
            if memory_item:
                success = self.memory_item_repo.delete(memory_item.id)
                if not success:
                    logger.warning(f"删除MemoryItem失败: ID={memory_item.id}")

            return format_success_response(f"成功删除记忆: {title}", {"permalink": permalink})

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return format_error_response(f"删除记忆失败: {str(e)}")

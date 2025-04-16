"""
记忆存储模块

提供记忆存储和删除功能
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.entity_manager import EntityManager
from src.memory.memory_formatter import MemoryFormatter
from src.memory.memory_utils import create_enhanced_text, create_memory_metadata, format_error_response, format_success_response
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.vector.chroma_vector_store import ChromaVectorStore
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
            # 使用 MemoryItemRepository 的 create_item 方法创建记录
            # 注意：entity_count 等信息将在后续步骤通过 update_vector_info 更新
            memory_item = self.memory_item_repo.create_item(
                title=memory_title,
                content=content,
                content_type="memory",
                tags=memory_tags,
                source="vector_store",  # 指明来源是向量存储流程创建的
                folder=target_folder,
                # permalink 和 sync_status 使用默认值
            )

            # 5. 存储到向量库
            metadata = create_memory_metadata(memory_title, memory_tags, entities, relations, observations, target_folder, memory_item.id)

            permalinks = await self.vector_store.store(texts=[enhanced_text], metadata=[metadata], folder=target_folder)

            if not permalinks:
                return format_error_response("存储到向量库失败", None)

            permalink = permalinks[0]

            # 6. 更新MemoryItem的向量库信息
            self.memory_item_repo.update_item(
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
                success = self.memory_item_repo.delete_item(memory_item.id)
                if not success:
                    logger.warning(f"删除MemoryItem失败: ID={memory_item.id}")

            return format_success_response(f"成功删除记忆: {title}", {"permalink": permalink})

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return format_error_response(f"删除记忆失败: {str(e)}")

    async def update_memory(self, permalink: str, content: Optional[str] = None, tags: Optional[str] = None) -> Dict[str, Any]:
        """
        更新记忆

        Args:
            permalink: 记忆永久链接
            content: 新内容，如果提供
            tags: 新标签，如果提供

        Returns:
            更新结果
        """
        try:
            # 1. 获取向量库中的现有记忆
            existing_vector_data = await self.vector_store.get(permalink)
            if not existing_vector_data:
                return format_error_response(f"未找到要更新的记忆: {permalink}")

            # 2. 获取关联的MemoryItem
            memory_item = self.memory_item_repo.find_by_permalink(permalink)
            if not memory_item:
                logger.warning(f"向量库存在但未找到关联的MemoryItem: {permalink}")
                # 可以考虑创建一个新的MemoryItem或返回错误
                return format_error_response(f"未找到关联的数据库记录: {permalink}")

            # 3. 准备更新内容和元数据
            current_content = existing_vector_data.get("content", "")
            current_metadata = existing_vector_data.get("metadata", {})
            new_content = content if content is not None else memory_item.content  # 使用数据库内容作为备选
            new_tags = tags if tags is not None else memory_item.tags

            # 4. 如果内容变化，重新解析
            enhanced_text = current_content  # 默认使用旧的增强文本
            entities, relations, observations = [], [], []
            if content is not None and content != memory_item.content:
                parse_result = self.doc_processor.process_document_text(new_content)
                if not parse_result.get("success", False):
                    return format_error_response(f"解析新内容失败: {parse_result.get('error', '未知错误')}")

                entities = parse_result.get("entities", [])
                relations = parse_result.get("relations", [])
                observations = parse_result.get("observations", [])
                enhanced_text = create_enhanced_text(memory_item.title, entities, relations, new_content)
                # 注意：这里没有更新实体、关系、观察的存储，只更新了文本和元数据
                # 完整的更新可能需要删除旧的关联项并创建新的
                logger.warning("更新记忆时未处理实体/关系/观察的更新，可能导致不一致")

            # 5. 更新元数据
            updated_metadata = create_memory_metadata(
                memory_item.title,
                new_tags,
                entities,
                relations,
                observations,
                memory_item.folder,
                memory_item.id,
                existing_metadata=current_metadata,  # 保留未更改的元数据
            )

            # 6. 更新向量库
            update_success = await self.vector_store.update(permalink=permalink, text=enhanced_text, metadata=updated_metadata)

            if not update_success:
                return format_error_response("更新向量库失败")

            # 7. 更新MemoryItem记录
            update_data = {
                "content": new_content,
                "tags": new_tags,
                "entity_count": len(entities) if entities else memory_item.entity_count,  # 只有内容更新时才更新计数
                "relation_count": len(relations) if relations else memory_item.relation_count,
                "observation_count": len(observations) if observations else memory_item.observation_count,
            }
            updated_item = self.memory_item_repo.update_item(memory_item.id, **update_data)

            if not updated_item:
                # 即使数据库更新失败，向量库可能已更新，需要考虑回滚或记录
                logger.error(f"更新MemoryItem失败: ID={memory_item.id}")
                return format_error_response("更新数据库记录失败")

            return format_success_response(
                f"成功更新记忆: {memory_item.title}",
                {
                    "permalink": permalink,
                    "memory_item_id": memory_item.id,
                },
            )

        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return format_error_response(f"更新记忆失败: {str(e)}")

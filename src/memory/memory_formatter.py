"""
记忆管理器格式化工具

提供记忆数据的格式化和转换功能
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.memory_utils import extract_original_content

logger = logging.getLogger(__name__)


class MemoryFormatter:
    """
    记忆格式化工具

    提供记忆数据的格式化和转换功能
    """

    def __init__(self, memory_item_repo: MemoryItemRepository):
        """
        初始化记忆格式化工具

        Args:
            memory_item_repo: 记忆项仓库
        """
        self.memory_item_repo = memory_item_repo

    def format_search_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化搜索结果

        Args:
            result: 搜索结果

        Returns:
            格式化后的记忆数据
        """
        permalink = result.get("permalink", "")
        content = result.get("content", "")
        metadata = result.get("metadata", {})
        score = metadata.get("hybrid_score", 0) or metadata.get("score", 0)

        # 获取关联的MemoryItem记录
        memory_item_id = metadata.get("memory_item_id")
        memory_item = None
        if memory_item_id:
            memory_item = self.memory_item_repo.get_by_id(memory_item_id)

        # 如果没有找到关联的MemoryItem，尝试通过permalink查找
        if not memory_item:
            memory_item = self.memory_item_repo.find_by_permalink(permalink)

        # 分离增强文本中的部分
        title = metadata.get("title", "未命名记忆")

        # 只获取原文部分，跳过增强文本部分
        original_content = extract_original_content(content)

        memory_data = {"title": title, "content": original_content, "permalink": permalink, "score": score, "metadata": metadata}

        # 如果有关联的MemoryItem，添加ID和其他信息
        if memory_item:
            memory_data["memory_item_id"] = memory_item.id
            # 使用MemoryItem中的数据补充
            if not original_content and memory_item.content:
                memory_data["content"] = memory_item.content

        return memory_data

    def format_memory_from_item(self, memory_item) -> Dict[str, Any]:
        """
        从MemoryItem创建记忆数据

        Args:
            memory_item: 记忆项对象

        Returns:
            格式化后的记忆数据
        """
        memory = {
            "title": memory_item.title,
            "content": memory_item.content,
            "permalink": memory_item.permalink,
            "memory_item_id": memory_item.id,
            "metadata": {
                "title": memory_item.title,
                "tags": memory_item.tags,
                "entity_count": memory_item.entity_count,
                "relation_count": memory_item.relation_count,
                "observation_count": memory_item.observation_count,
                "folder": memory_item.folder,
                "created_at": memory_item.created_at.isoformat() if memory_item.created_at else None,
                "updated_at": memory_item.updated_at.isoformat() if memory_item.updated_at else None,
            },
        }

        return memory

    def format_memory_from_vector(self, doc: Dict[str, Any], permalink: str) -> Dict[str, Any]:
        """
        从向量库文档创建记忆数据

        Args:
            doc: 向量库文档
            permalink: 记忆永久链接

        Returns:
            格式化后的记忆数据
        """
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})

        # 分离增强文本中的部分
        title = metadata.get("title", "未命名记忆")

        # 获取原文部分
        original_content = extract_original_content(content)

        # 获取关联的MemoryItem ID
        memory_item_id = metadata.get("memory_item_id")

        memory = {"title": title, "content": original_content, "permalink": permalink, "metadata": metadata}

        if memory_item_id:
            memory["memory_item_id"] = memory_item_id

        return memory

    def format_list_item(self, item) -> Dict[str, Any]:
        """
        格式化列表项

        Args:
            item: 记忆项对象或文档

        Returns:
            格式化后的列表项
        """
        # 处理记忆项对象
        if hasattr(item, "id"):
            return {
                "title": item.title,
                "permalink": item.permalink,
                "memory_item_id": item.id,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "tags": item.tags,
                "entity_count": item.entity_count,
                "relation_count": item.relation_count,
                "observation_count": item.observation_count,
            }

        # 处理向量库文档
        permalink = item.get("permalink", "")
        metadata = item.get("metadata", {})
        memory_item_id = metadata.get("memory_item_id")

        memory_data = {
            "title": item.get("title", "未命名记忆"),
            "permalink": permalink,
            "updated_at": item.get("updated_at", ""),
            "tags": item.get("tags", ""),
        }

        if memory_item_id:
            memory_data["memory_item_id"] = memory_item_id

        return memory_data

"""
记忆项仓库模块

提供记忆项的存储和检索功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import MemoryItem


class MemoryItemRepository(Repository[MemoryItem]):
    """记忆项索引仓库类"""

    def __init__(self, session: Session):
        """初始化仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, MemoryItem)

    def create(
        self,
        title: str,
        content: str,
        content_type: str,
        tags: Optional[str] = None,
        source: Optional[str] = None,
    ) -> MemoryItem:
        """创建新的记忆项

        Args:
            title: 标题
            content: 内容
            content_type: 内容类型
            tags: 标签（逗号分隔）
            source: 来源

        Returns:
            MemoryItem: 创建的记忆项
        """
        data = {
            "title": title,
            "content": content,
            "content_type": content_type,
            "tags": tags,
            "source": source,
        }
        return super().create(data)

    def search_by_content(self, query: str) -> List[MemoryItem]:
        """通过内容搜索记忆项

        Args:
            query: 搜索关键词

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        return (
            self.session.query(MemoryItem)
            .filter(or_(MemoryItem.title.ilike(f"%{query}%"), MemoryItem.content.ilike(f"%{query}%"), MemoryItem.tags.ilike(f"%{query}%")))
            .all()
        )

    def find_by_category(self, category: str) -> List[MemoryItem]:
        """按分类查找记忆项

        Args:
            category: 分类名称

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        return self.session.query(MemoryItem).filter(MemoryItem.category == category).all()

    def find_by_storage_type(self, storage_type: str) -> List[MemoryItem]:
        """按存储类型查找记忆项

        Args:
            storage_type: 存储类型('local'或'basic_memory')

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        return self.session.query(MemoryItem).filter(MemoryItem.storage_type == storage_type).all()

    def find_by_refs(
        self, entity_id: Optional[str] = None, observation_id: Optional[str] = None, relation_id: Optional[str] = None
    ) -> List[MemoryItem]:
        """通过引用ID查找记忆项

        Args:
            entity_id: 实体ID
            observation_id: 观察ID
            relation_id: 关系ID

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        query = self.session.query(MemoryItem)
        if entity_id:
            query = query.filter(MemoryItem.entity_refs.contains([entity_id]))
        if observation_id:
            query = query.filter(MemoryItem.observation_refs.contains([observation_id]))
        if relation_id:
            query = query.filter(MemoryItem.relation_refs.contains([relation_id]))
        return query.all()

    def update_refs(
        self,
        item_id: int,
        entity_refs: Optional[List[str]] = None,
        observation_refs: Optional[List[str]] = None,
        relation_refs: Optional[List[str]] = None,
    ) -> Optional[MemoryItem]:
        """更新记忆项的引用关系

        Args:
            item_id: 记忆项ID
            entity_refs: 新的实体引用列表
            observation_refs: 新的观察引用列表
            relation_refs: 新的关系引用列表

        Returns:
            Optional[MemoryItem]: 更新后的记忆项，如果不存在则返回None
        """
        item = self.get_by_id(item_id)
        if not item:
            return None

        update_data = {}
        if entity_refs is not None:
            update_data["entity_refs"] = entity_refs
        if observation_refs is not None:
            update_data["observation_refs"] = observation_refs
        if relation_refs is not None:
            update_data["relation_refs"] = relation_refs

        if update_data:
            return self.update(item_id, update_data)
        return item

    def get_by_id(self, memory_item_id: int) -> Optional[MemoryItem]:
        """
        根据ID获取记忆项

        Args:
            memory_item_id: 记忆项ID

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        return self.session.query(MemoryItem).filter(MemoryItem.id == memory_item_id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """
        获取所有记忆项

        Args:
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            List[MemoryItem]: 记忆项列表
        """
        return self.session.query(MemoryItem).order_by(desc(MemoryItem.created_at)).limit(limit).offset(offset).all()

    def search_by_title(self, title: str, limit: int = 10) -> List[MemoryItem]:
        """
        根据标题搜索记忆项

        Args:
            title: 要搜索的标题
            limit: 限制返回数量

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        return self.session.query(MemoryItem).filter(MemoryItem.title.ilike(f"%{title}%")).limit(limit).all()

    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryItem]:
        """
        根据标签搜索记忆项

        Args:
            tags: 标签列表
            limit: 限制返回数量

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        # 构建标签搜索条件
        conditions = []
        for tag in tags:
            conditions.append(MemoryItem.tags.ilike(f"%{tag}%"))

        return self.session.query(MemoryItem).filter(*conditions).limit(limit).all()

    def update(self, memory_item_id: int, **kwargs) -> Optional[MemoryItem]:
        """
        更新记忆项

        Args:
            memory_item_id: 记忆项ID
            **kwargs: 要更新的字段

        Returns:
            Optional[MemoryItem]: 更新后的记忆项，如果不存在则返回None
        """
        memory_item = self.get_by_id(memory_item_id)
        if memory_item:
            for key, value in kwargs.items():
                if hasattr(memory_item, key):
                    setattr(memory_item, key, value)
            self.session.commit()
        return memory_item

    def delete(self, memory_item_id: int) -> bool:
        """
        删除记忆项

        Args:
            memory_item_id: 记忆项ID

        Returns:
            bool: 是否删除成功
        """
        memory_item = self.get_by_id(memory_item_id)
        if memory_item:
            self.session.delete(memory_item)
            self.session.commit()
            return True
        return False

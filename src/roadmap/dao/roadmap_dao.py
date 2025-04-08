#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roadmap数据访问对象

提供路线图数据的访问接口，与Repository模式的实现适配。
"""

import uuid
from typing import Any, Dict, List, Optional

from src.db import get_session_factory
from src.models.db import Roadmap


class RoadmapDAO:
    """Roadmap数据访问对象"""

    def get_roadmap(self, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """获取路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            路线图数据字典或None
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            roadmap = session.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
            if roadmap:
                return roadmap.to_dict()
            return None

    def get_all_roadmaps(self) -> List[Dict[str, Any]]:
        """获取所有路线图

        Returns:
            路线图数据字典列表
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            roadmaps = session.query(Roadmap).all()
            return [roadmap.to_dict() for roadmap in roadmaps]

    def create_roadmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建路线图

        Args:
            data: 路线图数据

        Returns:
            创建的路线图数据字典
        """
        roadmap_id = f"roadmap_{uuid.uuid4().hex[:8]}"

        # 创建新的Roadmap实例
        roadmap = Roadmap(id=roadmap_id, title=data.get("name"), description=data.get("description"))

        session_factory = get_session_factory()
        with session_factory() as session:
            session.add(roadmap)
            session.commit()
            return roadmap.to_dict()

    def update_roadmap(self, roadmap_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新路线图

        Args:
            roadmap_id: 路线图ID
            data: 需要更新的数据

        Returns:
            更新后的路线图数据字典或None
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            roadmap = session.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
            if not roadmap:
                return None

            # 更新字段
            for key, value in data.items():
                if hasattr(roadmap, key):
                    setattr(roadmap, key, value)

            session.commit()
            return roadmap.to_dict()

    def delete_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """删除路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            删除操作结果
        """
        session_factory = get_session_factory()
        with session_factory() as session:
            roadmap = session.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
            if not roadmap:
                return {"success": False, "error": "Roadmap not found"}

            session.delete(roadmap)
            session.commit()
            return {"success": True, "roadmap_id": roadmap_id}

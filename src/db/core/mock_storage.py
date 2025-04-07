"""
模拟存储模块

提供实体的模拟存储功能。
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockStorage:
    """模拟存储

    用于模拟存储实体的数据。
    """

    def __init__(self, storage_path: Optional[str] = None):
        """初始化模拟存储

        Args:
            storage_path: 存储路径
        """
        # 使用模拟数据来处理无法存储到数据库的实体类型
        self._storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".vibecopilot", "mock_data"
        )
        if not os.path.exists(self._storage_path):
            os.makedirs(self._storage_path)

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """从模拟存储获取实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        file_path = os.path.join(self._storage_path, f"{entity_type}_{entity_id}.json")
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取模拟实体失败: {e}")
            return None

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """从模拟存储获取实体列表

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        result = []
        prefix = f"{entity_type}_"

        try:
            for filename in os.listdir(self._storage_path):
                if filename.startswith(prefix) and filename.endswith(".json"):
                    file_path = os.path.join(self._storage_path, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        entity = json.load(f)
                        result.append(entity)
            return result
        except Exception as e:
            logger.error(f"读取模拟实体列表失败: {e}")
            return []

    def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模拟实体

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        # 确保有ID
        if "id" not in data:
            entity_prefix = entity_type[0].upper()
            data["id"] = f"{entity_prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 添加时间戳
        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()
        if "updated_at" not in data:
            data["updated_at"] = data["created_at"]

        # 保存到文件
        file_path = os.path.join(self._storage_path, f"{entity_type}_{data['id']}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            logger.error(f"创建模拟实体失败: {e}")
            raise RuntimeError(f"创建模拟实体失败: {e}") from e

    def update_entity(
        self, entity_type: str, entity_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新模拟实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        # 获取现有实体
        entity = self.get_entity(entity_type, entity_id)
        if not entity:
            return None

        # 更新数据
        entity.update(data)
        entity["updated_at"] = datetime.now().isoformat()

        # 保存到文件
        file_path = os.path.join(self._storage_path, f"{entity_type}_{entity_id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entity, f, ensure_ascii=False, indent=2)
            return entity
        except Exception as e:
            logger.error(f"更新模拟实体失败: {e}")
            raise RuntimeError(f"更新模拟实体失败: {e}") from e

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """删除模拟实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        file_path = os.path.join(self._storage_path, f"{entity_type}_{entity_id}.json")
        if not os.path.exists(file_path):
            return False

        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除模拟实体失败: {e}")
            return False

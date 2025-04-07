"""
观察管理器

管理观察（事实、事件、状态）的记录和检索。
"""

import datetime
from typing import Any, Dict, List, Optional

from src.db.vector.memory_adapter import BasicMemoryAdapter


class ObservationManager:
    """
    观察管理器

    提供记录和检索观察的功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化观察管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建向量存储适配器
        vector_config = self.config.get("vector_store", {})
        vector_config["default_folder"] = vector_config.get("default_folder", "observations")
        vector_config["default_tags"] = vector_config.get("default_tags", "observation")
        self.vector_store = BasicMemoryAdapter(vector_config)

    async def record_observation(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        related_entities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        记录观察

        Args:
            content: 观察内容
            metadata: 元数据（类型、标题等）
            related_entities: 相关实体ID列表

        Returns:
            记录的观察
        """
        metadata = metadata or {}
        related_entities = related_entities or []

        # 准备观察元数据
        observation_type = metadata.get("type", "generic")
        observation_title = metadata.get("title", "Observation")
        observation_tags = metadata.get("tags", "")

        # 获取当前时间
        timestamp = datetime.datetime.now().isoformat()

        # 准备完整元数据
        full_metadata = {
            "title": observation_title,
            "type": observation_type,
            "tags": f"observation,{observation_type},{observation_tags}",
            "timestamp": timestamp,
            "related_entities": ",".join(related_entities),
            **metadata,
        }

        # 准备观察内容（添加标题和时间戳）
        full_content = f"# {observation_title}\n\n{content}\n\n## Metadata\n\n- **Timestamp**: {timestamp}\n- **Type**: {observation_type}"

        if related_entities:
            full_content += f"\n- **Related Entities**: {', '.join(related_entities)}"

        # 存储观察
        folder = f"observations/{observation_type}"
        permalinks = await self.vector_store.store([full_content], [full_metadata], folder)

        if not permalinks:
            raise RuntimeError("Failed to store observation")

        # 返回观察信息
        observation_id = permalinks[0].split("/")[-1]

        return {
            "id": observation_id,
            "permalink": permalinks[0],
            "type": observation_type,
            "title": observation_title,
            "content": content,
            "timestamp": timestamp,
            "related_entities": related_entities,
            "metadata": metadata,
        }

    async def get_observation(self, observation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取观察

        Args:
            observation_id: 观察ID或永久链接

        Returns:
            观察信息
        """
        # 如果提供的不是完整永久链接，构造永久链接
        if not observation_id.startswith("memory://"):
            # 尝试查找观察
            results = await self.vector_store.search(observation_id, limit=1)
            if not results:
                return None

            observation_data = await self.vector_store.get(results[0]["permalink"])
        else:
            # 直接获取观察
            observation_data = await self.vector_store.get(observation_id)

        if not observation_data:
            return None

        # 提取观察信息
        metadata = observation_data.get("metadata", {})
        observation_type = metadata.get("type", "generic")
        observation_title = metadata.get("title", "Unnamed Observation")
        timestamp = metadata.get("timestamp", "")
        related_entities = (
            metadata.get("related_entities", "").split(",")
            if metadata.get("related_entities")
            else []
        )

        # 去除一些内部元数据字段
        clean_metadata = {
            k: v
            for k, v in metadata.items()
            if k not in ["title", "type", "tags", "score", "timestamp", "related_entities"]
        }

        return {
            "id": observation_id,
            "permalink": observation_data.get("permalink", ""),
            "type": observation_type,
            "title": observation_title,
            "content": observation_data.get("content", ""),
            "timestamp": timestamp,
            "related_entities": related_entities,
            "metadata": clean_metadata,
        }

    async def search_observations(
        self, query: str, observation_type: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索观察

        Args:
            query: 搜索查询
            observation_type: 观察类型过滤
            limit: 返回结果数量

        Returns:
            观察列表
        """
        # 准备过滤条件
        filter_dict = {}
        if observation_type:
            filter_dict["type"] = observation_type

        # 搜索观察
        results = await self.vector_store.search(query, limit, filter_dict)

        # 转换结果
        observations = []
        for result in results:
            metadata = result.get("metadata", {})
            observation_type = metadata.get("type", "generic")
            observation_title = metadata.get("title", "Unnamed Observation")
            timestamp = metadata.get("timestamp", "")
            related_entities = (
                metadata.get("related_entities", "").split(",")
                if metadata.get("related_entities")
                else []
            )

            # 去除一些内部元数据字段
            clean_metadata = {
                k: v
                for k, v in metadata.items()
                if k not in ["title", "type", "tags", "score", "timestamp", "related_entities"]
            }

            observations.append(
                {
                    "id": result["permalink"].split("/")[-1],
                    "permalink": result["permalink"],
                    "type": observation_type,
                    "title": observation_title,
                    "content": result.get("content", ""),
                    "timestamp": timestamp,
                    "related_entities": related_entities,
                    "metadata": clean_metadata,
                    "score": metadata.get("score", 0),
                }
            )

        return observations

    async def get_recent_observations(
        self, observation_type: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取最近的观察

        Args:
            observation_type: 观察类型过滤
            limit: 返回结果数量

        Returns:
            观察列表
        """
        # 准备查询
        query = "observation"
        if observation_type:
            query += f" {observation_type}"

        # 准备过滤条件
        filter_dict = {}
        if observation_type:
            filter_dict["type"] = observation_type

        # 使用搜索API
        return await self.search_observations(query, observation_type, limit)

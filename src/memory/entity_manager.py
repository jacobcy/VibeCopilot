"""
实体管理器

管理知识实体及其属性。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# from src.db.vector.memory_adapter import BasicMemoryAdapter # 错误路径
from src.memory.vector.memory_adapter import BasicMemoryAdapter  # 正确路径
from src.memory.vector.vector_store import VectorStore


class EntityManager:
    """
    实体管理器

    提供创建、更新、查询和删除知识实体的功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化实体管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建向量存储适配器
        vector_config = self.config.get("vector_store", {})
        vector_config["default_folder"] = vector_config.get("default_folder", "entities")
        vector_config["default_tags"] = vector_config.get("default_tags", "entity")
        self.vector_store = BasicMemoryAdapter(vector_config)

    async def create_entity(self, entity_type: str, properties: Dict[str, Any], content: Optional[str] = None) -> Dict[str, Any]:
        """
        创建实体

        Args:
            entity_type: 实体类型
            properties: 实体属性
            content: 实体详细内容

        Returns:
            创建的实体
        """
        # 检查必要的属性
        if "name" not in properties:
            raise ValueError("Entity must have a 'name' property")

        # 准备实体内容
        entity_name = properties["name"]

        if content is None:
            # 如果没有提供内容，根据属性生成内容
            content_lines = [f"# {entity_name}"]

            if "description" in properties:
                content_lines.append("\n" + properties["description"])

            content_lines.append("\n## Properties")
            for key, value in properties.items():
                if key != "name" and key != "description":
                    content_lines.append(f"- **{key}**: {value}")

            content = "\n".join(content_lines)

        # 准备元数据
        metadata = {
            "title": entity_name,
            "type": entity_type,
            "tags": f"entity,{entity_type}",
            **properties,
        }

        # 存储实体
        folder = f"entities/{entity_type}"
        permalinks = await self.vector_store.store([content], [metadata], folder)

        if not permalinks:
            raise RuntimeError("Failed to store entity")

        # 返回实体信息
        entity_id = permalinks[0].split("/")[-1]

        return {
            "id": entity_id,
            "permalink": permalinks[0],
            "type": entity_type,
            "name": entity_name,
            "properties": properties,
        }

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实体

        Args:
            entity_id: 实体ID或永久链接

        Returns:
            实体信息
        """
        # 如果提供的不是完整永久链接，构造永久链接
        if not entity_id.startswith("memory://"):
            # 尝试查找实体
            results = await self.vector_store.search(entity_id, limit=1)
            if not results:
                return None

            entity_data = await self.vector_store.get(results[0]["permalink"])
        else:
            # 直接获取实体
            entity_data = await self.vector_store.get(entity_id)

        if not entity_data:
            return None

        # 提取实体信息
        metadata = entity_data.get("metadata", {})
        entity_type = metadata.get("type", "unknown")
        entity_name = metadata.get("title", "Unnamed Entity")

        # 提取属性（排除一些元数据字段）
        properties = {k: v for k, v in metadata.items() if k not in ["title", "type", "tags", "score"]}

        return {
            "id": entity_id,
            "permalink": entity_data.get("permalink", ""),
            "type": entity_type,
            "name": entity_name,
            "properties": properties,
            "content": entity_data.get("content", ""),
        }

    async def update_entity(self, entity_id: str, properties: Dict[str, Any], content: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        更新实体

        Args:
            entity_id: 实体ID或永久链接
            properties: 新属性（只更新提供的属性）
            content: 新内容（如果提供）

        Returns:
            更新后的实体
        """
        # 获取现有实体
        entity = await self.get_entity(entity_id)
        if not entity:
            return None

        # 更新属性
        updated_properties = {**entity["properties"], **properties}
        entity_name = updated_properties.get("name", entity["name"])

        # 准备更新内容
        if content is None and entity["content"]:
            # 如果没有提供新内容，保留旧内容
            content = entity["content"]
        elif content is None:
            # 如果没有提供新内容且没有旧内容，根据属性生成内容
            content_lines = [f"# {entity_name}"]

            if "description" in updated_properties:
                content_lines.append("\n" + updated_properties["description"])

            content_lines.append("\n## Properties")
            for key, value in updated_properties.items():
                if key != "name" and key != "description":
                    content_lines.append(f"- **{key}**: {value}")

            content = "\n".join(content_lines)

        # 准备元数据
        metadata = {
            "title": entity_name,
            "type": entity["type"],
            "tags": f"entity,{entity['type']}",
            **updated_properties,
        }

        # 更新实体
        success = await self.vector_store.update(entity["permalink"], content, metadata)

        if not success:
            raise RuntimeError("Failed to update entity")

        # 返回更新后的实体
        return {
            "id": entity_id,
            "permalink": entity["permalink"],
            "type": entity["type"],
            "name": entity_name,
            "properties": updated_properties,
            "content": content,
        }

    async def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体

        Args:
            entity_id: 实体ID或永久链接

        Returns:
            删除是否成功
        """
        # 获取实体
        entity = await self.get_entity(entity_id)
        if not entity:
            return False

        # 删除实体
        return await self.vector_store.delete([entity["permalink"]])

    async def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索实体

        Args:
            query: 搜索查询
            entity_type: 实体类型过滤
            limit: 返回结果数量

        Returns:
            实体列表
        """
        # 准备过滤条件
        filter_dict = {}
        if entity_type:
            filter_dict["type"] = entity_type

        # 搜索实体
        results = await self.vector_store.search(query, limit, filter_dict)

        # 转换结果
        entities = []
        for result in results:
            metadata = result.get("metadata", {})
            entity_type = metadata.get("type", "unknown")
            entity_name = metadata.get("title", "Unnamed Entity")

            # 提取属性（排除一些元数据字段）
            properties = {k: v for k, v in metadata.items() if k not in ["title", "type", "tags", "score"]}

            entities.append(
                {
                    "id": result["permalink"].split("/")[-1],
                    "permalink": result["permalink"],
                    "type": entity_type,
                    "name": entity_name,
                    "properties": properties,
                    "score": metadata.get("score", 0),
                }
            )

        return entities

    async def get_entity_stats(self) -> Dict[str, Any]:
        """
        获取实体统计信息

        Returns:
            统计信息字典
        """
        try:
            # 使用向量存储获取实体的统计信息
            # 注意: 这依赖于BasicMemoryAdapter/ChromaVectorStore是否能区分实体
            # 假设实体存储在名为"entities"的父文件夹下
            entity_stats = await self.vector_store.get_stats(folder="entities")

            # 可以进一步按实体类型细分统计，如果需要
            # total_count = entity_stats.get("total_documents", 0)
            # type_counts = {}
            # # 需要额外查询来按类型分组，这里简化处理

            return {"total_entities": entity_stats.get("total_documents", 0), "details": entity_stats}
        except Exception as e:
            logger.error(f"获取实体统计失败: {e}")
            return {"status": "error", "message": str(e)}

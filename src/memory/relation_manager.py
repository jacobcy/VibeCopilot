"""
关系管理器

管理实体之间的关系。
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from src.memory.memory_adapter import BasicMemoryAdapter


class RelationManager:
    """
    关系管理器

    提供创建和查询实体之间关系的功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化关系管理器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建向量存储适配器
        vector_config = self.config.get("vector_store", {})
        vector_config["default_folder"] = vector_config.get("default_folder", "relations")
        vector_config["default_tags"] = vector_config.get("default_tags", "relation")
        self.vector_store = BasicMemoryAdapter(vector_config)

    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性

        Returns:
            创建的关系
        """
        properties = properties or {}

        # 构造关系ID
        relation_id = f"{source_id}_{relation_type}_{target_id}"

        # 准备关系内容
        content = f"# Relation: {source_id} {relation_type} {target_id}\n\n"

        if properties:
            content += "## Properties\n\n"
            for key, value in properties.items():
                content += f"- **{key}**: {value}\n"

        # 准备元数据
        metadata = {
            "title": f"{source_id} {relation_type} {target_id}",
            "type": relation_type,
            "tags": f"relation,{relation_type}",
            "source_id": source_id,
            "target_id": target_id,
            **properties,
        }

        # 存储关系
        folder = "relations"
        permalinks = await self.vector_store.store([content], [metadata], folder)

        if not permalinks:
            raise RuntimeError("Failed to store relation")

        # 返回关系信息
        return {
            "id": relation_id,
            "permalink": permalinks[0],
            "type": relation_type,
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties,
        }

    async def get_relations(
        self, entity_id: str, relation_type: Optional[str] = None, direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        获取实体的关系

        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤
            direction: 关系方向，可选值: 'outgoing', 'incoming', 'both'

        Returns:
            关系列表
        """
        # 准备查询
        query = f"relation {entity_id}"
        if relation_type:
            query += f" {relation_type}"

        # 搜索关系
        results = await self.vector_store.search(query, limit=50)  # 使用较大的限制

        # 过滤结果
        relations = []
        for result in results:
            metadata = result.get("metadata", {})
            source_id = metadata.get("source_id", "")
            target_id = metadata.get("target_id", "")
            rel_type = metadata.get("type", "")

            # 根据方向过滤
            if direction == "outgoing" and source_id != entity_id:
                continue
            elif direction == "incoming" and target_id != entity_id:
                continue
            elif direction == "both" and source_id != entity_id and target_id != entity_id:
                continue

            # 根据类型过滤
            if relation_type and rel_type != relation_type:
                continue

            # 提取属性（排除一些元数据字段）
            properties = {
                k: v
                for k, v in metadata.items()
                if k not in ["title", "type", "tags", "score", "source_id", "target_id"]
            }

            relations.append(
                {
                    "id": f"{source_id}_{rel_type}_{target_id}",
                    "permalink": result["permalink"],
                    "type": rel_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "properties": properties,
                }
            )

        return relations

    async def find_path(
        self, source_id: str, target_id: str, max_depth: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        查找从源实体到目标实体的路径

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            max_depth: 最大搜索深度

        Returns:
            找到的路径列表，每个路径是关系字典的列表
        """
        # 使用BFS算法查找路径
        visited: Set[str] = set()
        queue: List[Tuple[str, List[Dict[str, Any]]]] = [(source_id, [])]
        all_paths: List[List[Dict[str, Any]]] = []

        while queue and max_depth > 0:
            next_queue: List[Tuple[str, List[Dict[str, Any]]]] = []

            for current_id, path in queue:
                # 如果已访问过，跳过
                if current_id in visited:
                    continue

                # 标记为已访问
                visited.add(current_id)

                # 获取所有关系
                relations = await self.get_relations(current_id, direction="outgoing")

                for relation in relations:
                    next_id = relation["target_id"]

                    # 如果找到目标，添加路径
                    if next_id == target_id:
                        all_paths.append(path + [relation])
                    else:
                        # 否则将其加入队列
                        next_queue.append((next_id, path + [relation]))

            # 更新队列和深度
            queue = next_queue
            max_depth -= 1

        return all_paths

    async def find_common_connections(self, entity_id1: str, entity_id2: str) -> List[str]:
        """
        查找两个实体的共同连接

        Args:
            entity_id1: 第一个实体ID
            entity_id2: 第二个实体ID

        Returns:
            共同连接的实体ID列表
        """
        # 获取两个实体的所有关系
        relations1 = await self.get_relations(entity_id1)
        relations2 = await self.get_relations(entity_id2)

        # 提取连接的实体ID
        connections1 = set()
        for relation in relations1:
            if relation["source_id"] == entity_id1:
                connections1.add(relation["target_id"])
            else:
                connections1.add(relation["source_id"])

        connections2 = set()
        for relation in relations2:
            if relation["source_id"] == entity_id2:
                connections2.add(relation["target_id"])
            else:
                connections2.add(relation["source_id"])

        # 找到共同连接
        common_connections = connections1.intersection(connections2)

        return list(common_connections)

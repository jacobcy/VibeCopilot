"""
实体处理器

用于从内容中提取实体和关系的处理器。
"""

from typing import Any, Dict, List, Optional

from src.core.parsing.parser_factory import create_parser


class EntityProcessor:
    """
    实体处理器

    提供从内容中提取实体和关系的功能。
    """

    def __init__(self, backend="openai", config=None):
        """
        初始化实体处理器

        Args:
            backend: 解析后端，如'openai'、'ollama'、'regex'
            config: 配置参数
        """
        self.backend = backend
        self.config = config or {}

        # 创建解析器
        self.parser = create_parser("generic", backend, config)

    def process_content(self, content: str) -> Dict[str, Any]:
        """
        处理内容，提取实体和关系

        Args:
            content: 文本内容

        Returns:
            处理结果，包含提取的实体和关系
        """
        # 解析内容
        parse_result = self.parser.parse_text(content, "generic")

        # 提取实体和关系
        entities = self._extract_entities(content, parse_result)
        relationships = self._extract_relationships(entities, content)

        return {
            "success": True,
            "entities": entities,
            "relationships": relationships,
            "content": content,
            "metadata": {"entity_count": len(entities), "relationship_count": len(relationships)},
        }

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理文件，提取实体和关系

        Args:
            file_path: 文件路径

        Returns:
            处理结果，包含提取的实体和关系
        """
        # 使用解析器读取文件
        parse_result = self.parser.parse_file(file_path)

        # 提取内容
        content = parse_result.get("content", "")

        # 提取实体和关系
        entities = self._extract_entities(content, parse_result)
        relationships = self._extract_relationships(entities, content)

        return {
            "success": True,
            "entities": entities,
            "relationships": relationships,
            "content": content,
            "file_path": file_path,
            "metadata": {"entity_count": len(entities), "relationship_count": len(relationships)},
        }

    def _extract_entities(self, content: str, parse_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从内容中提取实体

        Args:
            content: 文本内容
            parse_result: 解析结果

        Returns:
            提取的实体列表
        """
        # 这里简化实现，实际可能需要更复杂的逻辑或调用NLP服务
        entities = []

        # 提取标题作为实体（如果有）
        title = parse_result.get("title")
        if title:
            entities.append({"type": "title", "name": title, "properties": {"text": title}})

        # 简单的规则匹配识别技术名称
        tech_keywords = [
            "Python",
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Angular",
            "CSS",
            "HTML",
            "Git",
        ]
        for keyword in tech_keywords:
            if keyword in content:
                entities.append(
                    {
                        "type": "technology",
                        "name": keyword,
                        "properties": {"mentions": content.count(keyword)},
                    }
                )

        # 识别组织名称
        org_keywords = ["VibeCopilot", "GitHub", "Microsoft", "Google", "OpenAI"]
        for keyword in org_keywords:
            if keyword in content:
                entities.append(
                    {
                        "type": "organization",
                        "name": keyword,
                        "properties": {"mentions": content.count(keyword)},
                    }
                )

        return entities

    def _extract_relationships(
        self, entities: List[Dict[str, Any]], content: str
    ) -> List[Dict[str, Any]]:
        """
        提取实体之间的关系

        Args:
            entities: 实体列表
            content: 文本内容

        Returns:
            关系列表
        """
        # 这里简化实现，实际可能需要更复杂的逻辑
        relationships = []

        # 如果有2个以上实体，尝试建立关系
        if len(entities) < 2:
            return relationships

        # 遍历实体对，寻找关系
        for i, entity1 in enumerate(entities):
            for entity2 in enumerate(entities[i + 1 :], i + 1):
                idx2, entity2 = entity2

                # 避免自关联
                if i == idx2:
                    continue

                # 检查两个实体是否出现在同一个句子中
                entity1_name = entity1["name"]
                entity2_name = entity2["name"]

                # 简单地分割句子
                sentences = content.split(". ")

                for sentence in sentences:
                    if entity1_name in sentence and entity2_name in sentence:
                        # 找到了关系
                        relationship_type = "relates_to"  # 默认关系类型

                        # 根据实体类型确定更具体的关系
                        if entity1["type"] == "organization" and entity2["type"] == "technology":
                            relationship_type = "uses"
                        elif entity1["type"] == "technology" and entity2["type"] == "technology":
                            relationship_type = "works_with"

                        relationships.append(
                            {
                                "source": entity1["name"],
                                "target": entity2["name"],
                                "type": relationship_type,
                                "properties": {"sentence": sentence},
                            }
                        )

                        # 每对实体只添加一个关系
                        break

        return relationships

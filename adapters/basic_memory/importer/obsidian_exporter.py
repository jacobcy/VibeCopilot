"""
Obsidian导出模块
提供将实体导出到Obsidian vault的功能
这是为了向后兼容而保留的接口，实际使用exporters目录中的实现
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from adapters.basic_memory.exporters.obsidian_exporter import (
    ObsidianExporter as NewObsidianExporter,
)


class ObsidianExporter:
    """
    Obsidian导出器，提供导出到Obsidian vault的功能
    这是为了向后兼容保留的类，实际调用exporters/obsidian_exporter.py中的实现
    """

    def __init__(self, vault_path: str):
        """初始化导出器

        Args:
            vault_path: Obsidian vault路径
        """
        self.vault_path = os.path.expanduser(vault_path)
        self.new_exporter = NewObsidianExporter(self.vault_path)
        self.setup_vault()

    def setup_vault(self) -> None:
        """设置Obsidian vault目录"""
        self.new_exporter.setup_output_dir()

    def export_document(
        self,
        original_path: Path,
        source_dir: Path,
        metadata: Dict,
        observations: List[Tuple[str, str]],
        relations: List[Tuple[str, str]],
    ) -> None:
        """导出文档到Obsidian

        Args:
            original_path: 原始文件路径
            source_dir: 源目录
            metadata: 元数据
            observations: 观察列表，每个观察为(内容, 类型)
            relations: 关系列表，每个关系为(目标标题, 关系类型)
        """
        try:
            # 转换为新API所需的格式
            entity = self._convert_to_entity_format(
                original_path, source_dir, metadata, observations, relations
            )

            # 使用新的导出器导出文档
            self.new_exporter.export_document(entity)

        except Exception as e:
            print(f"警告: 导出文件时出错: {str(e)}")

    def _convert_to_entity_format(
        self,
        original_path: Path,
        source_dir: Path,
        metadata: Dict,
        observations: List[Tuple[str, str]],
        relations: List[Tuple[str, str]],
    ) -> Dict[str, Any]:
        """将旧格式转换为实体格式，以兼容新的API

        Returns:
            Dict: 实体格式的文档数据
        """
        # 构建基本实体数据
        entity = {
            "id": metadata.get("id", ""),
            "title": original_path.stem,
            "type": "document",
            "metadata": metadata,
            "observations": [],
            "outgoing_relations": [],
            "incoming_relations": [],
        }

        # 添加观察
        for content, obs_type in observations:
            entity["observations"].append({"content": content, "type": obs_type})

        # 添加关系
        for target_title, rel_type in relations:
            entity["outgoing_relations"].append({"target_title": target_title, "type": rel_type})

        return entity

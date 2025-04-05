"""
路线图转换模块

提供将路线图数据转换为不同格式的功能。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml


class RoadmapConverter:
    """路线图格式转换器"""

    @staticmethod
    def to_yaml(roadmap_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        将路线图数据转换为YAML格式

        Args:
            roadmap_data: 路线图数据
            output_path: 可选的输出文件路径

        Returns:
            str: YAML格式的路线图数据
        """
        # 创建可序列化的副本
        serializable_data = RoadmapConverter._prepare_for_serialization(roadmap_data)

        # 转换为YAML
        yaml_str = yaml.dump(
            serializable_data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

        # 如果提供了输出路径，则写入文件
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(yaml_str)

        return yaml_str

    @staticmethod
    def to_json(
        roadmap_data: Dict[str, Any], output_path: Optional[str] = None, pretty: bool = True
    ) -> str:
        """
        将路线图数据转换为JSON格式

        Args:
            roadmap_data: 路线图数据
            output_path: 可选的输出文件路径
            pretty: 是否美化输出

        Returns:
            str: JSON格式的路线图数据
        """
        # 创建可序列化的副本
        serializable_data = RoadmapConverter._prepare_for_serialization(roadmap_data)

        # 转换为JSON
        indent = 2 if pretty else None
        json_str = json.dumps(serializable_data, indent=indent, ensure_ascii=False)

        # 如果提供了输出路径，则写入文件
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    @staticmethod
    def from_yaml(yaml_str: str) -> Dict[str, Any]:
        """
        从YAML字符串加载路线图数据

        Args:
            yaml_str: YAML格式的路线图数据

        Returns:
            Dict[str, Any]: 路线图数据
        """
        return yaml.safe_load(yaml_str)

    @staticmethod
    def from_json(json_str: str) -> Dict[str, Any]:
        """
        从JSON字符串加载路线图数据

        Args:
            json_str: JSON格式的路线图数据

        Returns:
            Dict[str, Any]: 路线图数据
        """
        return json.loads(json_str)

    @staticmethod
    def from_file(file_path: str) -> Dict[str, Any]:
        """
        从文件加载路线图数据

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, Any]: 路线图数据
        """
        ext = os.path.splitext(file_path)[1].lower()

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if ext in [".yml", ".yaml"]:
            return RoadmapConverter.from_yaml(content)
        elif ext == ".json":
            return RoadmapConverter.from_json(content)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    @staticmethod
    def _prepare_for_serialization(data: Any) -> Any:
        """
        准备数据以便序列化

        Args:
            data: 需要序列化的数据

        Returns:
            Any: 可序列化的数据
        """
        if isinstance(data, dict):
            return {k: RoadmapConverter._prepare_for_serialization(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [RoadmapConverter._prepare_for_serialization(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

"""
解析器基类
提供内容解析的抽象基类和共用方法
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import frontmatter


class BaseContentParser(ABC):
    """内容解析器基类"""

    def __init__(self, model: str, content_type: str = "generic"):
        """初始化解析器

        Args:
            model: 使用的模型名称
            content_type: 内容类型 ("rule", "document", "generic")
        """
        self.model = model
        self.content_type = content_type

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析文件

        Args:
            file_path: 文件路径

        Returns:
            Dict: 解析后的结构
        """
        # 读取文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 优先尝试解析Front Matter
            try:
                post = frontmatter.loads(content)
                metadata = post.metadata

                # 如果有有效的Front Matter数据，直接返回
                if metadata and self._is_valid_metadata(metadata):
                    metadata["content"] = post.content
                    metadata["id"] = metadata.get("id", Path(file_path).stem)
                    metadata["path"] = file_path
                    return metadata
            except Exception as e:
                print(f"解析Front Matter失败: {e}")
                pass

            # 如果没有有效的Front Matter，使用自定义解析
            return self.parse_content(content, file_path)

        except Exception as e:
            print(f"读取文件失败: {e}")
            return self._get_default_result(file_path)

    @abstractmethod
    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析内容

        Args:
            content: 文本内容
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析后的结构
        """
        pass

    def _get_default_result(self, file_path: str) -> Dict[str, Any]:
        """当解析失败时返回默认结果

        Args:
            file_path: 文件路径

        Returns:
            Dict: 默认的结构
        """
        filename = Path(file_path).stem if file_path else "unknown"

        if self.content_type == "rule":
            return {
                "id": filename,
                "name": filename,
                "type": "manual",
                "description": "无法解析的规则文件",
                "globs": [],
                "always_apply": False,
                "items": [],
                "examples": [],
                "content": "",
                "path": file_path,
            }
        elif self.content_type == "document":
            return {
                "id": filename,
                "title": filename,
                "description": "无法解析的文档",
                "content": "",
                "blocks": [],
                "path": file_path,
            }
        else:
            return {"id": filename, "title": filename, "content": "", "path": file_path}

    def _is_valid_metadata(self, metadata: Dict[str, Any]) -> bool:
        """检查元数据是否有效

        Args:
            metadata: Front Matter元数据

        Returns:
            bool: 是否有效
        """
        if self.content_type == "rule":
            # 规则至少应包含name或id字段
            return bool(metadata.get("name")) or bool(metadata.get("id"))
        elif self.content_type == "document":
            # 文档至少应包含title字段
            return bool(metadata.get("title"))
        else:
            # 通用类型只需要有任何元数据即可
            return bool(metadata)


class ParsingMixin:
    """解析混合类，提供通用解析方法"""

    def add_metadata(self, result: Dict[str, Any], content: str, context: str) -> Dict[str, Any]:
        """添加元数据到结果

        Args:
            result: 解析结果
            content: 原始内容
            context: 上下文信息

        Returns:
            Dict: 添加元数据后的结果
        """
        # 添加路径信息
        if context and "path" not in result:
            result["path"] = context

        # 确保内容字段存在
        if "content" not in result:
            result["content"] = content

        return result

"""
解析器基类定义

提供所有解析器必须实现的基本接口。
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseParser(ABC):
    """
    解析器基类

    定义了所有解析器必须实现的基本接口。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化解析器

        Args:
            config: 配置参数
        """
        self.config = config or {}

    @abstractmethod
    def parse_text(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        解析文本内容

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如'rule'、'document'等

        Returns:
            解析结果
        """
        pass

    def parse_file(self, file_path: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        解析文件内容

        Args:
            file_path: 文件路径
            content_type: 内容类型，如'rule'、'document'等。如果为None，将尝试自动检测

        Returns:
            解析结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 如果没有指定内容类型，尝试根据文件扩展名检测
        if content_type is None:
            content_type = self._detect_content_type(file_path)

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析内容
        result = self.parse_text(content, content_type)

        # 添加文件信息
        result["_file_info"] = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1],
            "directory": os.path.dirname(file_path),
        }

        return result

    def _detect_content_type(self, file_path: str) -> str:
        """
        根据文件扩展名检测内容类型

        Args:
            file_path: 文件路径

        Returns:
            内容类型
        """
        extension = os.path.splitext(file_path)[1].lower()

        # 简单的映射表
        type_mapping = {
            ".mdc": "rule",
            ".md": "document",
            ".txt": "generic",
            ".py": "code",
            ".js": "code",
            ".ts": "code",
            ".html": "markup",
            ".css": "style",
            ".json": "data",
            ".yaml": "data",
            ".yml": "data",
        }

        return type_mapping.get(extension, "generic")

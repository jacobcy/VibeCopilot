"""
统一内容解析器入口
为各种解析器提供统一的接口
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from adapters.content_parser.openai import (
    OpenAIDocumentParser,
    OpenAIGenericParser,
    OpenAIRuleParser,
)

logger = logging.getLogger(__name__)


class ContentParser:
    """内容解析器入口，提供统一的解析接口"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化内容解析器

        Args:
            model: 使用的模型名称，默认为gpt-4o-mini
        """
        self.model = model
        self.parsers = {
            "rule": OpenAIRuleParser(model),
            "document": OpenAIDocumentParser(model),
            "generic": OpenAIGenericParser(model),
        }

    def parse_file(self, file_path: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """解析文件内容

        Args:
            file_path: 文件路径
            content_type: 内容类型，如果为None则自动推断

        Returns:
            Dict: 解析结果
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return {"error": "文件不存在"}

        # 推断内容类型
        if content_type is None:
            content_type = self._infer_content_type(file_path)

        # 获取对应的解析器
        parser = self.parsers.get(content_type, self.parsers["generic"])

        try:
            # 使用解析器解析文件
            return parser.parse_file(file_path)
        except Exception as e:
            logger.error(f"解析文件失败: {file_path}, 错误: {e}")
            return {"error": f"解析文件失败: {str(e)}"}

    def parse_content(
        self, content: str, content_type: str = "generic", context: str = ""
    ) -> Dict[str, Any]:
        """解析文本内容

        Args:
            content: 文本内容
            content_type: 内容类型
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析结果
        """
        parser = self.parsers.get(content_type, self.parsers["generic"])

        try:
            return parser.parse_content(content, context)
        except Exception as e:
            logger.error(f"解析内容失败, 错误: {e}")
            return {"error": f"解析内容失败: {str(e)}"}

    def parse_directory(
        self, directory: str, pattern: str = "*.md", content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """解析目录下的所有匹配文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式，默认为*.md
            content_type: 内容类型，如果为None则自动推断

        Returns:
            List[Dict]: 解析结果列表
        """
        if not os.path.isdir(directory):
            logger.error(f"目录不存在: {directory}")
            return [{"error": "目录不存在"}]

        results = []
        path = Path(directory)

        try:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # 为每个文件自动推断类型
                    file_type = content_type or self._infer_content_type(str(file_path))
                    result = self.parse_file(str(file_path), file_type)
                    results.append(result)

            return results
        except Exception as e:
            logger.error(f"解析目录失败: {directory}, 错误: {e}")
            return [{"error": f"解析目录失败: {str(e)}"}]

    def _infer_content_type(self, file_path: str) -> str:
        """根据文件路径和内容推断内容类型

        Args:
            file_path: 文件路径

        Returns:
            str: 推断的内容类型
        """
        # 检查路径中的关键字
        path_lower = file_path.lower()

        # 规则类型检测
        if any(
            keyword in path_lower
            for keyword in ["-rule", "/rule", "_rule", "-rules", "/rules", "_rules"]
        ):
            return "rule"

        # 文档类型检测
        if any(
            keyword in path_lower for keyword in ["/doc", "-doc", "_doc", "/docs", "-docs", "_docs"]
        ):
            return "document"

        # 根据文件内容推断
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(1000)  # 读取前1000个字符即可

            # 检查是否包含规则相关标记
            if "<rule>" in content or "# Rule:" in content or "## 规则项:" in content:
                return "rule"

            # 检查是否包含文档相关标记
            if "# Document:" in content or "## Table of Contents" in content:
                return "document"
        except Exception as e:
            logger.warning(f"读取文件内容失败，无法根据内容推断类型: {e}")

        # 默认为通用类型
        return "generic"

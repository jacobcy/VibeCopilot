"""
OpenAI通用内容解析器
专门用于解析通用内容
"""

import logging
from typing import Any, Dict

from adapters.content_parser.openai.api_client import OpenAIClient
from adapters.content_parser.utils.parser_base import BaseContentParser, ParsingMixin
from adapters.content_parser.utils.parser_mixins import GenericParsingMixin

logger = logging.getLogger(__name__)


class OpenAIGenericParser(BaseContentParser, ParsingMixin, GenericParsingMixin):
    """OpenAI通用内容解析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化通用内容解析器

        Args:
            model: 使用的OpenAI模型名称
        """
        super().__init__(model, "generic")

        # 初始化OpenAI客户端
        self.api_client = OpenAIClient(model)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析通用内容

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        logger.info(f"使用OpenAI解析通用内容: {context}")

        try:
            # 优先使用API完整解析
            result = self.api_client.parse_generic(content, context)

            # 简单验证
            if not result.get("title") and not result.get("id"):
                # API解析失败，使用本地解析
                logger.info("API解析失败或结构无效，使用本地解析方法")
                result = self._parse_generic_locally(content, context)

            # 如果关键点为空，尝试提取
            if not result.get("key_points"):
                result["key_points"] = self.extract_key_points(content)

            # 如果摘要为空，生成摘要
            if not result.get("summary"):
                result["summary"] = self.generate_summary(content)

            # 添加元数据
            return self.add_metadata(result, content, context)

        except Exception as e:
            logger.error(f"解析通用内容失败: {e}")
            return self._get_default_result(context)

    def _parse_generic_locally(self, content: str, context: str = "") -> Dict[str, Any]:
        """本地解析通用内容（不使用API）

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        # 提取基本元数据
        metadata = self.extract_generic_metadata(content)

        # 如果没有ID，使用文件名
        if "id" not in metadata and context:
            from pathlib import Path

            metadata["id"] = Path(context).stem

        # 提取关键点
        key_points = self.extract_key_points(content)

        # 生成摘要
        summary = self.generate_summary(content)

        # 构建完整结构
        result = {
            "id": metadata.get("id", "unknown"),
            "title": metadata.get("title", metadata.get("id", "未命名内容")),
            "description": metadata.get("description", ""),
            "type": metadata.get("type", "generic"),
            "key_points": key_points,
            "summary": summary,
        }

        return result

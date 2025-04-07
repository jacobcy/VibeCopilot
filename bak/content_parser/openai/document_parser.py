"""
OpenAI文档解析器
专门用于解析文档内容
"""

import logging
from typing import Any, Dict

from adapters.content_parser.openai.api_client import OpenAIClient
from adapters.content_parser.utils.parser_base import BaseContentParser, ParsingMixin
from adapters.content_parser.utils.parser_mixins import DocumentParsingMixin

logger = logging.getLogger(__name__)


class OpenAIDocumentParser(BaseContentParser, ParsingMixin, DocumentParsingMixin):
    """OpenAI文档解析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化文档解析器

        Args:
            model: 使用的OpenAI模型名称
        """
        super().__init__(model, "document")

        # 初始化OpenAI客户端
        self.api_client = OpenAIClient(model)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析文档内容

        Args:
            content: 文档文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的文档结构
        """
        logger.info(f"使用OpenAI解析文档内容: {context}")

        try:
            # 优先使用API完整解析
            result = self.api_client.parse_document(content, context)

            # 验证结果
            from adapters.content_parser.utils.content_template import validate_document_structure

            if not validate_document_structure(result):
                # API解析失败，使用本地解析
                logger.info("API解析失败或结构无效，使用本地解析方法")
                result = self._parse_document_locally(content, context)

            # 如果块为空，尝试从内容中提取块
            if not result.get("blocks"):
                result["blocks"] = self.extract_document_blocks(content)

            # 添加元数据
            return self.add_metadata(result, content, context)

        except Exception as e:
            logger.error(f"解析文档内容失败: {e}")
            return self._get_default_result(context)

    def _parse_document_locally(self, content: str, context: str = "") -> Dict[str, Any]:
        """本地解析文档内容（不使用API）

        Args:
            content: 文档文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的文档结构
        """
        # 提取基本元数据
        metadata = self.extract_document_metadata(content)

        # 如果没有ID，使用文件名
        if "id" not in metadata and context:
            from pathlib import Path

            metadata["id"] = Path(context).stem

        # 提取文档块
        blocks = self.extract_document_blocks(content)

        # 构建完整结构
        result = {
            "id": metadata.get("id", "unknown"),
            "title": metadata.get("title", metadata.get("id", "未命名文档")),
            "description": metadata.get("description", ""),
            "blocks": blocks,
        }

        return result

"""
OpenAI内容解析器
使用OpenAI API解析各种内容
"""

import logging
from typing import Any, Dict

from adapters.content_parser.openai.api_client import OpenAIClient
from adapters.content_parser.utils.parser_base import BaseContentParser, ParsingMixin

logger = logging.getLogger(__name__)


class OpenAIParser(BaseContentParser, ParsingMixin):
    """OpenAI内容解析器"""

    def __init__(self, model: str = "gpt-4o-mini", content_type: str = "generic"):
        """初始化解析器

        Args:
            model: 使用的OpenAI模型名称
            content_type: 内容类型 ("rule", "document", "generic")
        """
        super().__init__(model, content_type)

        # 初始化OpenAI客户端
        self.api_client = OpenAIClient(model)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """使用OpenAI解析内容

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        try:
            # 根据内容类型选择不同的解析方法
            if self.content_type == "rule":
                result = self._parse_rule(content, context)
            elif self.content_type == "document":
                result = self._parse_document(content, context)
            else:
                result = self._parse_generic(content, context)

            # 添加元数据
            return self.add_metadata(result, content, context)

        except Exception as e:
            logger.error(f"解析内容失败: {e}")
            return self._get_default_result(context)

    def _parse_rule(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析规则内容

        Args:
            content: 规则文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的规则结构
        """
        logger.info(f"使用OpenAI解析规则内容: {context}")

        try:
            # 使用API客户端解析规则
            result = self.api_client.parse_rule(content, context)

            # 验证结果
            from adapters.content_parser.utils.content_template import validate_rule_structure

            if validate_rule_structure(result):
                # 如果规则项为空，尝试从内容中提取块
                if not result.get("items"):
                    from adapters.content_parser.utils.content_template import (
                        extract_blocks_from_content,
                    )

                    blocks = extract_blocks_from_content(content)
                    if blocks:
                        result["items"] = [
                            {
                                "content": block["content"],
                                "category": block["type"],
                                "id": block.get("id", f"block_{i}"),
                            }
                            for i, block in enumerate(blocks)
                        ]

                return result
            else:
                logger.warning("OpenAI返回的规则结构无效")
                return self._get_default_result(context)

        except Exception as e:
            logger.error(f"OpenAI解析规则失败: {e}")
            return self._get_default_result(context)

    def _parse_document(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析文档内容

        Args:
            content: 文档文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的文档结构
        """
        logger.info(f"使用OpenAI解析文档内容: {context}")

        try:
            # 使用API客户端解析文档
            result = self.api_client.parse_document(content, context)
            return result

        except Exception as e:
            logger.error(f"OpenAI解析文档失败: {e}")
            return self._get_default_result(context)

    def _parse_generic(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析通用内容

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        logger.info(f"使用OpenAI解析通用内容: {context}")

        try:
            # 使用API客户端解析通用内容
            result = self.api_client.parse_generic(content, context)
            return result

        except Exception as e:
            logger.error(f"OpenAI解析通用内容失败: {e}")
            return self._get_default_result(context)

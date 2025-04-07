"""
OpenAI规则解析器
专门用于解析规则内容
"""

import logging
from typing import Any, Dict

from adapters.content_parser.openai.api_client import OpenAIClient
from adapters.content_parser.utils.parser_base import BaseContentParser, ParsingMixin
from adapters.content_parser.utils.parser_mixins import RuleParsingMixin

logger = logging.getLogger(__name__)


class OpenAIRuleParser(BaseContentParser, ParsingMixin, RuleParsingMixin):
    """OpenAI规则解析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化规则解析器

        Args:
            model: 使用的OpenAI模型名称
        """
        super().__init__(model, "rule")

        # 初始化OpenAI客户端
        self.api_client = OpenAIClient(model)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析规则内容

        Args:
            content: 规则文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的规则结构
        """
        logger.info(f"使用OpenAI解析规则内容: {context}")

        try:
            # 优先使用API完整解析
            result = self.api_client.parse_rule(content, context)

            # 验证结果
            from adapters.content_parser.utils.content_template import validate_rule_structure

            if validate_rule_structure(result):
                # API解析成功，继续处理
                pass
            else:
                # API解析失败，使用本地解析
                logger.info("API解析失败，使用本地解析方法")
                result = self._parse_rule_locally(content, context)

            # 如果规则项为空，尝试从内容中提取块
            if not result.get("items"):
                from adapters.content_parser.utils.content_template import extract_blocks_from_content

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

            # 添加元数据
            return self.add_metadata(result, content, context)

        except Exception as e:
            logger.error(f"解析规则内容失败: {e}")
            return self._get_default_result(context)

    def _parse_rule_locally(self, content: str, context: str = "") -> Dict[str, Any]:
        """本地解析规则内容（不使用API）

        Args:
            content: 规则文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的规则结构
        """
        # 提取基本元数据
        metadata = self.extract_rule_metadata(content)

        # 如果没有ID，使用文件名
        if "id" not in metadata and context:
            from pathlib import Path

            metadata["id"] = Path(context).stem

        # 提取规则条目
        items = self.extract_rule_items(content)

        # 提取示例
        examples = self.extract_rule_examples(content)

        # 构建完整结构
        result = {
            "id": metadata.get("id", "unknown"),
            "name": metadata.get("name", metadata.get("id", "未命名规则")),
            "type": metadata.get("type", "manual"),
            "description": metadata.get("description", ""),
            "globs": [],
            "always_apply": False,
            "items": items,
            "examples": examples,
        }

        return result

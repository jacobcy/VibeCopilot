"""
OpenAI内容解析器
使用OpenAI API解析Markdown文档和规则文件
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.content_parser.base_parser import ContentParser

logger = logging.getLogger(__name__)


class OpenAIParser(ContentParser):
    """OpenAI内容解析器"""

    def __init__(self, model: str = "gpt-4o-mini", content_type: str = "generic"):
        """初始化解析器

        Args:
            model: 使用的OpenAI模型名称
            content_type: 内容类型 ("rule", "document", "generic")
        """
        super().__init__(model, content_type)

        # 初始化OpenAI客户端
        from adapters.content_parser.lib.openai_api import OpenAIClient

        self.openai_client = OpenAIClient(model)

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

            # 添加路径信息
            if context and "path" not in result:
                result["path"] = context

            # 确保内容字段存在
            if "content" not in result:
                result["content"] = content

            return result

        except Exception as e:
            logger.error(f"解析内容失败: {e}")
            print(f"解析内容失败: {e}")
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

        # 构建系统提示词
        system_prompt = """
        你是一个专业的规则解析器。你的任务是分析Markdown格式的规则文件，提取其结构和组成部分，并输出为结构化JSON。

        请分析规则文件并提取以下信息:
        1. 规则ID（如文件名，除非明确定义）
        2. 规则名称（通常在标题中）
        3. 规则类型（可以是agent、auto、manual、always等）
        4. 规则描述（概述规则的目的）
        5. 适用的文件模式（globs）
        6. 是否总是应用
        7. 规则条目列表（内容、优先级和分类）
        8. 示例列表（如果有）

        使用以下JSON格式（必须严格遵守）:
        {
          "id": "规则ID",
          "name": "规则名称",
          "type": "规则类型",
          "description": "规则描述",
          "globs": ["适用的文件模式1", "适用的文件模式2"],
          "always_apply": true或false,
          "items": [
            {
              "content": "规则条目内容",
              "priority": 优先级数值,
              "category": "条目分类"
            }
          ],
          "examples": [
            {
              "content": "示例内容",
              "is_valid": true或false,
              "description": "示例描述"
            }
          ]
        }
        """

        # 构建用户提示词
        user_prompt = f"规则文件路径: {context}\n\n规则内容:\n{content}"

        # 请求OpenAI解析
        try:
            result = self.openai_client.parse_content(
                system_prompt=system_prompt, user_prompt=user_prompt
            )

            # 处理结果
            if "content" not in result:
                result["content"] = content

            # 验证规则结构
            from adapters.content_parser.lib.content_template import validate_rule_structure

            if validate_rule_structure(result):
                # 如果规则项为空，尝试从内容中提取块
                if not result.get("items"):
                    from adapters.content_parser.lib.content_template import (
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
                logger.warning(f"OpenAI返回的规则结构无效")
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

        # 构建系统提示词
        system_prompt = """
        你是一个专业的文档解析器。你的任务是分析Markdown格式的文档，提取其结构和组成部分，并输出为结构化JSON。

        请分析文档并提取以下信息:
        1. 文档ID（如文件名，除非明确定义）
        2. 文档标题（通常在一级标题中）
        3. 文档描述（概述文档的目的）
        4. 文档分块（基于标题层级）

        使用以下JSON格式（必须严格遵守）:
        {
          "id": "文档ID",
          "title": "文档标题",
          "description": "文档描述",
          "blocks": [
            {
              "id": "块ID",
              "type": "heading|text|code|list|quote",
              "level": 1-6,  // 仅用于heading类型
              "content": "块内容",
              "language": "编程语言"  // 仅用于code类型
            }
          ]
        }
        """

        # 构建用户提示词
        user_prompt = f"文档文件路径: {context}\n\n文档内容:\n{content}"

        # 请求OpenAI解析
        try:
            result = self.openai_client.parse_content(
                system_prompt=system_prompt, user_prompt=user_prompt
            )

            # 处理结果
            if "content" not in result:
                result["content"] = content

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

        # 构建系统提示词
        system_prompt = """
        你是一个专业的内容解析器。你的任务是分析Markdown格式的内容，提取其结构和关键信息，并输出为结构化JSON。

        请分析内容并提取以下信息:
        1. 内容ID（如文件名，除非明确定义）
        2. 内容标题（通常在一级标题中）
        3. 内容描述（如果有）
        4. 内容类型（如果可以确定）
        5. 关键点或摘要

        使用以下JSON格式（必须严格遵守）:
        {
          "id": "内容ID",
          "title": "内容标题",
          "description": "内容描述",
          "type": "内容类型",
          "key_points": [
            "关键点1",
            "关键点2"
          ],
          "summary": "内容摘要"
        }
        """

        # 构建用户提示词
        user_prompt = f"文件路径: {context}\n\n内容:\n{content}"

        # 请求OpenAI解析
        try:
            result = self.openai_client.parse_content(
                system_prompt=system_prompt, user_prompt=user_prompt
            )

            # 处理结果
            if "content" not in result:
                result["content"] = content

            return result

        except Exception as e:
            logger.error(f"OpenAI解析通用内容失败: {e}")
            return self._get_default_result(context)

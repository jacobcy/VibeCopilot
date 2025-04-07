"""
API客户端基类
提供API接口调用的抽象基类和共用方法
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """API客户端基类"""

    def __init__(self, model: str):
        """初始化API客户端

        Args:
            model: 使用的模型名称
        """
        self.model = model

    def parse_content(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """解析内容（抽象方法）

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            Dict: 解析结果
        """
        raise NotImplementedError("子类必须实现parse_content方法")

    def parse_rule(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析规则内容

        Args:
            content: 规则内容
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析后的规则结构
        """
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

        # 调用parse_content方法（由子类实现）
        return self.parse_content(system_prompt, user_prompt)

    def parse_document(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析文档内容

        Args:
            content: 文档内容
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析后的文档结构
        """
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

        # 调用parse_content方法（由子类实现）
        return self.parse_content(system_prompt, user_prompt)

    def parse_generic(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析通用内容

        Args:
            content: 文本内容
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析后的结构
        """
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

        # 调用parse_content方法（由子类实现）
        return self.parse_content(system_prompt, user_prompt)

    def handle_response(self, response_text: str) -> Dict[str, Any]:
        """处理API响应，提取JSON内容

        Args:
            response_text: API响应文本

        Returns:
            Dict: 解析后的JSON结果

        Raises:
            ValueError: 如果响应无法解析为有效的JSON
        """
        try:
            # 尝试直接解析整个文本
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # 如果失败，尝试提取JSON部分（通常被```json和```包围）
            json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
            matches = re.findall(json_pattern, response_text)

            if matches:
                try:
                    result = json.loads(matches[0])
                    return result
                except json.JSONDecodeError:
                    logger.error("无法解析提取的JSON内容")

            # 如果还是失败，尝试其他提取方法
            # ...

            logger.error("响应中找不到有效的JSON内容")
            raise ValueError("响应中找不到有效的JSON内容")

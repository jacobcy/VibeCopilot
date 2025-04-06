"""
Ollama内容解析器
使用Ollama服务解析Markdown文档和规则文件
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.content_parser.base_parser import ContentParser

logger = logging.getLogger(__name__)


class OllamaParser(ContentParser):
    """Ollama内容解析器"""

    def __init__(self, model: str = "mistral", content_type: str = "generic"):
        """初始化解析器

        Args:
            model: 使用的Ollama模型
            content_type: 内容类型 ("rule", "document", "generic")
        """
        super().__init__(model, content_type)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """使用Ollama解析内容

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
        logger.info(f"使用Ollama解析规则内容: {context}")

        # 构建提示词
        prompt = f"""解析以下Markdown格式的规则文件，提取其结构和组件。

规则文件路径: {context}

规则内容:
{content}

请分析这个规则文件并提取以下信息:
1. 规则ID（通常是文件名，如没有明确定义）
2. 规则名称
3. 规则类型（agent、auto、manual、always）
4. 规则描述
5. 适用的文件模式（globs）
6. 是否始终应用
7. 规则条目列表（内容、优先级和分类）
8. 示例列表（如果有）

以严格JSON格式返回结果:
{{
  "id": "规则ID（如未明确定义则使用文件名）",
  "name": "规则名称",
  "type": "规则类型",
  "description": "规则描述",
  "globs": ["适用的文件模式1", "适用的文件模式2"],
  "always_apply": true或false,
  "items": [
    {{
      "content": "规则条目内容",
      "priority": 优先级数值,
      "category": "条目分类"
    }}
  ],
  "examples": [
    {{
      "content": "示例内容",
      "is_valid": true或false,
      "description": "示例描述"
    }}
  ]
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""

        # 调用Ollama
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True
            )

            # 提取JSON部分
            output = result.stdout.strip()
            json_start = output.find("{")
            json_end = output.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                try:
                    parsed_json = json.loads(json_str)

                    # 添加原始内容
                    if "content" not in parsed_json:
                        parsed_json["content"] = content

                    # 验证结果
                    from adapters.content_parser.lib.content_template import validate_rule_structure

                    if validate_rule_structure(parsed_json):
                        # 如果规则项为空，尝试从内容中提取块
                        if not parsed_json.get("items"):
                            from adapters.content_parser.lib.content_template import (
                                extract_blocks_from_content,
                            )

                            blocks = extract_blocks_from_content(content)
                            if blocks:
                                parsed_json["items"] = [
                                    {
                                        "content": block["content"],
                                        "category": block["type"],
                                        "id": block.get("id", f"block_{i}"),
                                    }
                                    for i, block in enumerate(blocks)
                                ]

                        return parsed_json
                    else:
                        return self._get_default_result(context)

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")
                    logger.debug(f"原始JSON字符串: {json_str}")
                    return self._get_default_result(context)
            else:
                logger.error(f"无法从输出中提取JSON: {output}")
                return self._get_default_result(context)

        except subprocess.CalledProcessError as e:
            logger.error(f"调用Ollama失败: {e}")
            logger.debug(f"错误输出: {e.stderr}")
            return self._get_default_result(context)
        except FileNotFoundError:
            logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
            return self._get_default_result(context)

    def _parse_document(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析文档内容

        Args:
            content: 文档文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的文档结构
        """
        logger.info(f"使用Ollama解析文档内容: {context}")

        # 构建提示词
        prompt = f"""解析以下Markdown格式的文档，提取其结构和组件。

文档文件路径: {context}

文档内容:
{content}

请分析这个文档并提取以下信息:
1. 文档ID（通常是文件名，如没有明确定义）
2. 文档标题（通常在一级标题中）
3. 文档描述（概述文档的目的）
4. 文档分块（基于标题层级）

以严格JSON格式返回结果:
{{
  "id": "文档ID",
  "title": "文档标题",
  "description": "文档描述",
  "blocks": [
    {{
      "id": "块ID",
      "type": "heading|text|code|list|quote",
      "level": 1-6,  // 仅用于heading类型
      "content": "块内容",
      "language": "编程语言"  // 仅用于code类型
    }}
  ]
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""

        # 调用Ollama
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True
            )

            # 提取JSON部分
            output = result.stdout.strip()
            json_start = output.find("{")
            json_end = output.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                try:
                    parsed_json = json.loads(json_str)

                    # 添加原始内容
                    if "content" not in parsed_json:
                        parsed_json["content"] = content

                    return parsed_json

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")
                    logger.debug(f"原始JSON字符串: {json_str}")
                    return self._get_default_result(context)
            else:
                logger.error(f"无法从输出中提取JSON: {output}")
                return self._get_default_result(context)

        except subprocess.CalledProcessError as e:
            logger.error(f"调用Ollama失败: {e}")
            logger.debug(f"错误输出: {e.stderr}")
            return self._get_default_result(context)
        except FileNotFoundError:
            logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
            return self._get_default_result(context)

    def _parse_generic(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析通用内容

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        logger.info(f"使用Ollama解析通用内容: {context}")

        # 构建提示词
        prompt = f"""解析以下Markdown格式的内容，提取其结构和关键信息。

文件路径: {context}

内容:
{content}

请分析这个内容并提取以下信息:
1. 内容ID（如文件名，除非明确定义）
2. 内容标题（通常在一级标题中）
3. 内容描述（如果有）
4. 内容类型（如果可以确定）
5. 关键点或摘要

以严格JSON格式返回结果:
{{
  "id": "内容ID",
  "title": "内容标题",
  "description": "内容描述",
  "type": "内容类型",
  "key_points": [
    "关键点1",
    "关键点2"
  ],
  "summary": "内容摘要"
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""

        # 调用Ollama
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True
            )

            # 提取JSON部分
            output = result.stdout.strip()
            json_start = output.find("{")
            json_end = output.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                try:
                    parsed_json = json.loads(json_str)

                    # 添加原始内容
                    if "content" not in parsed_json:
                        parsed_json["content"] = content

                    return parsed_json

                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")
                    logger.debug(f"原始JSON字符串: {json_str}")
                    return self._get_default_result(context)
            else:
                logger.error(f"无法从输出中提取JSON: {output}")
                return self._get_default_result(context)

        except subprocess.CalledProcessError as e:
            logger.error(f"调用Ollama失败: {e}")
            logger.debug(f"错误输出: {e.stderr}")
            return self._get_default_result(context)
        except FileNotFoundError:
            logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
            return self._get_default_result(context)

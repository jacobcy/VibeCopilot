"""
OpenAI规则解析器
使用OpenAI API解析规则文件
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from adapters.rule_parser.base_parser import RuleParser
from adapters.rule_parser.lib.openai_api import OpenAIClient
from adapters.rule_parser.lib.rule_template import extract_blocks_from_content, validate_rule_structure


class OpenAIRuleParser(RuleParser):
    """OpenAI规则解析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化解析器

        Args:
            model: 使用的OpenAI模型
        """
        super().__init__(model)

        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient(model)

    def parse_rule_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """使用OpenAI解析规则内容

        Args:
            content: 规则文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的规则结构
        """
        try:
            # 使用OpenAI API解析
            result = self.openai_client.parse_rule(content, context)

            # 验证结果
            if validate_rule_structure(result):
                # 如果规则项为空，尝试从内容中提取块
                if not result.get("items"):
                    blocks = extract_blocks_from_content(content)
                    if blocks:
                        result["items"] = [
                            {
                                "content": block["content"],
                                "category": block["type"],
                                "id": block["id"],
                            }
                            for block in blocks
                        ]

                return result
            else:
                return self._get_default_result(context)

        except Exception as e:
            print(f"规则解析失败: {e}")
            return self._get_default_result(context)

    def _get_default_result(self, file_path: str) -> Dict[str, Any]:
        """当解析失败时返回默认结果

        Args:
            file_path: 规则文件路径

        Returns:
            Dict: 默认的规则结构
        """
        filename = Path(file_path).stem if file_path else "unknown"
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
        }

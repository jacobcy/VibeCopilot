"""
OpenAI解析器

使用OpenAI API进行内容解析的实现。
"""

import json
import os
from typing import Any, Dict, Optional

from src.parsing.base_parser import BaseParser


class OpenAIClient:
    """简化版的OpenAI API客户端"""

    def __init__(self, api_key=None, model="gpt-4"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    async def chat_completion(self, messages, model=None, temperature=0.2):
        """模拟 OpenAI 聊天完成接口"""
        # 这里仅作为示例，实际应调用 OpenAI API
        return {"choices": [{"message": {"content": "模拟的 OpenAI 响应"}}]}


class OpenAIParser(BaseParser):
    """
    OpenAI解析器

    使用OpenAI API解析内容。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化OpenAI解析器

        Args:
            config: 配置参数
        """
        super().__init__(config)

        # 从配置中获取API密钥和模型
        api_key = self.config.get("api_key")
        model = self.config.get("model", "gpt-4")

        # 创建API客户端
        self.client = OpenAIClient(api_key, model)

        # 内容类型和提示模板的映射
        self.prompt_templates = {
            "rule": self._get_rule_prompt_template(),
            "document": self._get_document_prompt_template(),
            "generic": self._get_generic_prompt_template(),
            "code": self._get_code_prompt_template(),
        }

    def parse_text(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        使用OpenAI API解析文本内容

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如'rule'、'document'等

        Returns:
            解析结果
        """
        # 如果未指定内容类型，默认为通用类型
        content_type = content_type or "generic"

        # 获取对应的提示模板
        prompt_template = self.prompt_templates.get(content_type, self.prompt_templates["generic"])

        # 格式化提示
        prompt = prompt_template.format(content=content)

        # 准备消息
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that parses content accurately.",
            },
            {"role": "user", "content": prompt},
        ]

        # 调用API（简化版）
        try:
            # 这里应该是异步调用，但为了简化示例，使用同步代码
            # response = await self.client.chat_completion(messages)
            # result_text = response["choices"][0]["message"]["content"]

            # 模拟解析结果
            if content_type == "rule":
                result = self._parse_rule(content)
            elif content_type == "document":
                result = self._parse_document(content)
            else:
                result = self._parse_generic(content)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_type": content_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }

    def _get_rule_prompt_template(self) -> str:
        """获取规则解析的提示模板"""
        return """
        Parse the following rule content and extract its structured information.
        Return the result as JSON.

        Rule content:
        {content}
        """

    def _get_document_prompt_template(self) -> str:
        """获取文档解析的提示模板"""
        return """
        Parse the following document content and extract its structured information.
        Return the result as JSON.

        Document content:
        {content}
        """

    def _get_generic_prompt_template(self) -> str:
        """获取通用内容解析的提示模板"""
        return """
        Parse the following content and extract its key information.
        Return the result as JSON.

        Content:
        {content}
        """

    def _get_code_prompt_template(self) -> str:
        """获取代码解析的提示模板"""
        return """
        Analyze the following code and extract its key components and functionality.
        Return the result as JSON.

        Code:
        {content}
        """

    def _parse_rule(self, content: str) -> Dict[str, Any]:
        """解析规则内容"""
        # 提取Front Matter和Markdown内容
        front_matter = {}
        markdown_content = content

        # 简单解析Front Matter（实际应使用更强大的解析器）
        if content.startswith("---"):
            try:
                end_index = content.find("---", 3)
                if end_index != -1:
                    front_matter_text = content[3:end_index].strip()
                    # 简单解析YAML格式的Front Matter
                    for line in front_matter_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            front_matter[key.strip()] = value.strip()

                    markdown_content = content[end_index + 3 :].strip()
            except Exception:
                # 解析错误，保持原样
                pass

        # 提取标题
        title = ""
        lines = markdown_content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        return {
            "success": True,
            "content_type": "rule",
            "front_matter": front_matter,
            "title": title,
            "content": markdown_content,
            "metadata": {
                "title": title,
                "type": front_matter.get("type", "unknown"),
                "description": front_matter.get("description", ""),
                "tags": front_matter.get("tags", "").split(",") if front_matter.get("tags") else [],
            },
        }

    def _parse_document(self, content: str) -> Dict[str, Any]:
        """解析文档内容"""
        # 提取标题
        title = ""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # 简单解析目录结构
        headings = []
        for line in lines:
            if line.startswith("#"):
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                heading_text = line[level:].strip()
                headings.append({"level": level, "text": heading_text})

        return {
            "success": True,
            "content_type": "document",
            "title": title,
            "content": content,
            "structure": {"headings": headings},
            "metadata": {
                "title": title,
                "word_count": len(content.split()),
                "line_count": len(lines),
            },
        }

    def _parse_generic(self, content: str) -> Dict[str, Any]:
        """解析通用内容"""
        # 简单分析
        lines = content.split("\n")

        return {
            "success": True,
            "content_type": "generic",
            "content": content,
            "metadata": {
                "line_count": len(lines),
                "word_count": len(content.split()),
                "char_count": len(content),
            },
        }

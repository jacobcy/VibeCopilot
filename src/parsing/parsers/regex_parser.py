"""
正则表达式解析器

使用正则表达式进行简单内容解析的实现。
"""

import re
from typing import Any, Dict, List, Optional

from src.parsing.base_parser import BaseParser


class RegexParser(BaseParser):
    """
    正则表达式解析器

    使用正则表达式进行简单内容解析。
    主要用于不需要深度理解的简单模式匹配。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化正则表达式解析器

        Args:
            config: 配置参数
        """
        super().__init__(config)

        # 内容类型到解析模式的映射
        self.patterns = {
            "rule": self._get_rule_patterns(),
            "document": self._get_document_patterns(),
            "generic": self._get_generic_patterns(),
            "code": self._get_code_patterns(),
        }

    def parse_text(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        使用正则表达式解析文本内容

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如'rule'、'document'等

        Returns:
            解析结果
        """
        # 如果未指定内容类型，默认为通用类型
        content_type = content_type or "generic"

        # 获取对应的模式
        patterns = self.patterns.get(content_type, self.patterns["generic"])

        try:
            # 根据内容类型调用相应的解析方法
            if content_type == "rule":
                result = self._parse_rule(content, patterns)
            elif content_type == "document":
                result = self._parse_document(content, patterns)
            else:
                result = self._parse_generic(content, patterns)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content_type": content_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }

    def _get_rule_patterns(self) -> Dict[str, str]:
        """获取规则解析的正则表达式模式"""
        return {
            "front_matter": r"---\s*\n(.*?)\n\s*---",
            "title": r"^#\s+(.+)$",
            "sections": r"^(##\s+.+)$",
            "examples": r"<example.*?>(.*?)</example>",
            "tags": r"tags:\s*[\"']?(.*?)[\"']?$",
            "description": r"description:\s*[\"']?(.*?)[\"']?$",
            "type": r"type:\s*[\"']?(.*?)[\"']?$",
        }

    def _get_document_patterns(self) -> Dict[str, str]:
        """获取文档解析的正则表达式模式"""
        return {
            "title": r"^#\s+(.+)$",
            "headings": r"^(#+)\s+(.+)$",
            "links": r"\[([^\]]+)\]\(([^)]+)\)",
            "images": r"!\[([^\]]*)\]\(([^)]+)\)",
            "code_blocks": r"```([a-zA-Z]*)\n(.*?)```",
        }

    def _get_generic_patterns(self) -> Dict[str, str]:
        """获取通用内容解析的正则表达式模式"""
        return {
            "urls": r"https?://[^\s]+",
            "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "dates": r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        }

    def _get_code_patterns(self) -> Dict[str, str]:
        """获取代码解析的正则表达式模式"""
        return {
            "functions": r"(def|function)\s+(\w+)\s*\(([^)]*)\)",
            "classes": r"class\s+(\w+)",
            "imports": r"(import|from)\s+([^;]+)",
            "comments": r"(#|//|/\*).*",
        }

    def _parse_rule(self, content: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """
        解析规则内容

        Args:
            content: 规则内容
            patterns: 正则表达式模式

        Returns:
            解析结果
        """
        # 提取Front Matter
        front_matter = {}
        front_matter_match = re.search(patterns["front_matter"], content, re.DOTALL)
        if front_matter_match:
            front_matter_text = front_matter_match.group(1)
            for line in front_matter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    front_matter[key.strip()] = value.strip()

        # 提取标题
        title = ""
        title_match = re.search(patterns["title"], content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)

        # 提取章节
        sections = []
        for match in re.finditer(patterns["sections"], content, re.MULTILINE):
            sections.append(match.group(1))

        # 提取示例
        examples = []
        for match in re.finditer(patterns["examples"], content, re.DOTALL):
            examples.append(match.group(1))

        return {
            "success": True,
            "content_type": "rule",
            "front_matter": front_matter,
            "title": title,
            "sections": sections,
            "examples": examples,
            "content": content,
            "metadata": {
                "title": title,
                "type": front_matter.get("type", ""),
                "description": front_matter.get("description", ""),
                "tags": front_matter.get("tags", "").split(",") if front_matter.get("tags") else [],
            },
        }

    def _parse_document(self, content: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """
        解析文档内容

        Args:
            content: 文档内容
            patterns: 正则表达式模式

        Returns:
            解析结果
        """
        # 提取标题
        title = ""
        title_match = re.search(patterns["title"], content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)

        # 提取标题结构
        headings = []
        for match in re.finditer(patterns["headings"], content, re.MULTILINE):
            level = len(match.group(1))  # '#' 的数量表示标题级别
            heading_text = match.group(2)
            headings.append({"level": level, "text": heading_text})

        # 提取链接
        links = []
        for match in re.finditer(patterns["links"], content):
            links.append({"text": match.group(1), "url": match.group(2)})

        # 提取图片
        images = []
        for match in re.finditer(patterns["images"], content):
            images.append({"alt": match.group(1), "url": match.group(2)})

        # 提取代码块
        code_blocks = []
        for match in re.finditer(patterns["code_blocks"], content, re.DOTALL):
            code_blocks.append({"language": match.group(1), "code": match.group(2)})

        return {
            "success": True,
            "content_type": "document",
            "title": title,
            "structure": {"headings": headings},
            "elements": {"links": links, "images": images, "code_blocks": code_blocks},
            "content": content,
            "metadata": {
                "title": title,
                "link_count": len(links),
                "image_count": len(images),
                "code_block_count": len(code_blocks),
            },
        }

    def _parse_generic(self, content: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """
        解析通用内容

        Args:
            content: 通用内容
            patterns: 正则表达式模式

        Returns:
            解析结果
        """
        # 提取URL
        urls = re.findall(patterns["urls"], content)

        # 提取电子邮件
        emails = re.findall(patterns["emails"], content)

        # 提取日期
        dates = re.findall(patterns["dates"], content)

        # 计算基本统计信息
        lines = content.split("\n")
        words = content.split()

        return {
            "success": True,
            "content_type": "generic",
            "elements": {"urls": urls, "emails": emails, "dates": dates},
            "content": content,
            "metadata": {
                "line_count": len(lines),
                "word_count": len(words),
                "char_count": len(content),
                "url_count": len(urls),
                "email_count": len(emails),
                "date_count": len(dates),
            },
        }

"""
解析器混合类
提供不同类型内容的解析方法，用于减少重复代码
"""

import re
from typing import Any, Dict, List, Optional, Union


class RuleParsingMixin:
    """规则解析混合类"""

    def extract_rule_metadata(self, content: str) -> Dict[str, Any]:
        """提取规则元数据

        Args:
            content: 规则内容

        Returns:
            Dict: 提取的元数据
        """
        metadata = {}

        # 提取标题（通常是规则名称）
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["name"] = title_match.group(1).strip()

        # 尝试提取规则类型
        type_match = re.search(r"类型[:：]\s*(\w+)", content)
        if type_match:
            metadata["type"] = type_match.group(1).lower()
        else:
            # 默认类型为manual
            metadata["type"] = "manual"

        # 尝试提取规则描述
        description_match = re.search(r"^##\s+(.+)$", content, re.MULTILINE)
        if description_match:
            metadata["description"] = description_match.group(1).strip()

        return metadata

    def extract_rule_items(self, content: str) -> List[Dict[str, Any]]:
        """提取规则条目

        Args:
            content: 规则内容

        Returns:
            List[Dict]: 规则条目列表
        """
        items = []

        # 提取标准格式的规则条目（通常在列表中）
        item_pattern = r"(?:^|\n)[*-]\s+(.+?)(?=\n[*-]|\n\n|\n$|$)"
        for i, match in enumerate(re.finditer(item_pattern, content, re.DOTALL)):
            item_content = match.group(1).strip()
            items.append(
                {
                    "content": item_content,
                    "priority": i + 1,  # 默认优先级按顺序递增
                    "category": "general",  # 默认类别
                }
            )

        return items

    def extract_rule_examples(self, content: str) -> List[Dict[str, Any]]:
        """提取规则示例

        Args:
            content: 规则内容

        Returns:
            List[Dict]: 示例列表
        """
        examples = []

        # 提取<example>标签中的示例
        example_pattern = r"<example(?:\s+type=\"([^\"]+)\")?>[\s\n]*([\s\S]*?)[\s\n]*<\/example>"
        for match in re.finditer(example_pattern, content):
            example_type = match.group(1) or "valid"
            example_content = match.group(2).strip()
            examples.append(
                {
                    "content": example_content,
                    "is_valid": example_type.lower() != "invalid",
                    "description": "",
                }
            )

        return examples


class DocumentParsingMixin:
    """文档解析混合类"""

    def extract_document_metadata(self, content: str) -> Dict[str, Any]:
        """提取文档元数据

        Args:
            content: 文档内容

        Returns:
            Dict: 提取的元数据
        """
        metadata = {}

        # 提取标题（通常是一级标题）
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 尝试提取文档描述（通常在标题下的段落）
        if title_match:
            title_pos = title_match.end()
            desc_match = re.search(r"\n\n(.+?)(?=\n\n|$)", content[title_pos:])
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()

        return metadata

    def extract_document_blocks(self, content: str) -> List[Dict[str, Any]]:
        """提取文档块

        Args:
            content: 文档内容

        Returns:
            List[Dict]: 文档块列表
        """
        blocks = []

        # 提取标题块
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        for i, line in enumerate(content.split("\n")):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                blocks.append({"id": f"h{level}_{i}", "type": "heading", "level": level, "content": title})

        # 提取代码块
        code_pattern = r"```([a-zA-Z]*)\n([\s\S]*?)```"
        for i, match in enumerate(re.finditer(code_pattern, content)):
            language = match.group(1) or "text"
            code_content = match.group(2)
            blocks.append({"id": f"code_{i}", "type": "code", "language": language, "content": code_content})

        # 提取引用块
        quote_pattern = r"((?:^>\s+.+\n?)+)"
        for i, match in enumerate(re.finditer(quote_pattern, content, re.MULTILINE)):
            quote_content = match.group(1)
            blocks.append({"id": f"quote_{i}", "type": "quote", "content": quote_content})

        # 提取列表块
        list_pattern = r"(?:^[*-]\s+.+$(?:\n[*-]\s+.+$)+)"
        for i, match in enumerate(re.finditer(list_pattern, content, re.MULTILINE)):
            list_content = match.group(0)
            blocks.append({"id": f"list_{i}", "type": "list", "content": list_content})

        # 提取表格块
        table_pattern = r"(\|.+\|(?:\n\|.+\|)+)"
        for i, match in enumerate(re.finditer(table_pattern, content)):
            table_content = match.group(1)
            blocks.append({"id": f"table_{i}", "type": "table", "content": table_content})

        return blocks


class GenericParsingMixin:
    """通用内容解析混合类"""

    def extract_generic_metadata(self, content: str) -> Dict[str, Any]:
        """提取通用内容元数据

        Args:
            content: 文本内容

        Returns:
            Dict: 提取的元数据
        """
        metadata = {}

        # 提取标题（通常是一级标题）
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 尝试提取内容类型
        type_match = re.search(r"类型[:：]\s*(\w+)", content)
        if type_match:
            metadata["type"] = type_match.group(1).lower()
        else:
            metadata["type"] = "generic"

        # 尝试提取描述
        if title_match:
            title_pos = title_match.end()
            desc_match = re.search(r"\n\n(.+?)(?=\n\n|$)", content[title_pos:])
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()

        return metadata

    def extract_key_points(self, content: str) -> List[str]:
        """提取关键点

        Args:
            content: 文本内容

        Returns:
            List[str]: 关键点列表
        """
        key_points = []

        # 尝试从列表中提取关键点
        bullet_pattern = r"(?:^|\n)[*-]\s+(.+?)(?=\n[*-]|\n\n|\n$|$)"
        for match in re.finditer(bullet_pattern, content, re.DOTALL):
            key_points.append(match.group(1).strip())

        return key_points

    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要

        Args:
            content: 文本内容
            max_length: 最大摘要长度

        Returns:
            str: 内容摘要
        """
        # 去除标题、代码块等
        clean_content = re.sub(r"^#+\s+.+$", "", content, flags=re.MULTILINE)
        clean_content = re.sub(r"```.*?```", "", clean_content, flags=re.DOTALL)

        # 取前N个字符作为摘要
        summary = " ".join(clean_content.split())[:max_length]

        # 如果摘要被截断，添加省略号
        if len(clean_content) > max_length:
            summary += "..."

        return summary

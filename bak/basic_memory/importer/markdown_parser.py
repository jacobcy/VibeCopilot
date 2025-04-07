"""
Markdown解析模块
提供解析Markdown文档的功能，包括front matter、链接和标签提取
"""

import re
from datetime import date, datetime
from typing import Dict, List, Set, Tuple, Union

import frontmatter


class MarkdownParser:
    """Markdown解析器，提供各种Markdown解析方法"""

    @staticmethod
    def serialize_date(obj: Union[Dict, List, datetime, date, str, int, float, bool, None]) -> Union[Dict, List, str, int, float, bool, None]:
        """递归序列化日期对象

        Args:
            obj: 需要序列化的对象

        Returns:
            序列化后的对象
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: MarkdownParser.serialize_date(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [MarkdownParser.serialize_date(item) for item in obj]
        return obj

    @staticmethod
    def extract_front_matter(content: str) -> Tuple[Dict, str]:
        """提取front matter和内容

        Args:
            content: Markdown内容

        Returns:
            Tuple[Dict, str]: (元数据字典, 内容文本)
        """
        post = frontmatter.loads(content)
        metadata = dict(post.metadata) if post.metadata else {}

        # 递归处理所有日期类型
        metadata = MarkdownParser.serialize_date(metadata)

        return metadata, post.content

    @staticmethod
    def extract_links(content: str) -> Set[str]:
        """提取Markdown链接

        Args:
            content: Markdown内容

        Returns:
            Set[str]: 链接集合
        """
        links = set()

        # 匹配 [[Wiki链接]]
        wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)
        for link in wiki_links:
            if "|" in link:  # [[链接|显示文本]]
                link = link.split("|")[0]
            links.add(link)

        # 匹配 [标题](链接.md)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+\.md)\)", content)
        for _, link in md_links:
            links.add(link)

        return links

    @staticmethod
    def extract_tags(content: str, metadata: Dict) -> Set[str]:
        """提取标签

        Args:
            content: Markdown内容
            metadata: 元数据字典

        Returns:
            Set[str]: 标签集合
        """
        tags = set()

        # 从front matter提取
        if "tags" in metadata:
            if isinstance(metadata["tags"], str):
                tags.update(tag.strip() for tag in metadata["tags"].split(","))
            elif isinstance(metadata["tags"], list):
                tags.update(metadata["tags"])

        # 从内容提取 #标签
        content_tags = re.findall(r"#(\w+)", content)
        tags.update(content_tags)

        return tags

    @staticmethod
    def split_content(content: str) -> List[Dict[str, str]]:
        """将内容分割为观察单元

        Args:
            content: Markdown内容

        Returns:
            List[Dict]: 观察单元列表，每个单元包含content和type
        """
        observations = []

        # 按段落分割
        paragraphs = content.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 判断内容类型
            if para.startswith("#"):
                obs_type = "heading"
            elif para.startswith("```"):
                obs_type = "code"
            elif para.startswith("- ") or para.startswith("* "):
                obs_type = "list"
            else:
                obs_type = "paragraph"

            observations.append({"content": para, "type": obs_type})

        return observations

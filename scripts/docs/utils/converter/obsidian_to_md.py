"""
将Obsidian Wiki格式转换为标准Markdown的工具。
"""

import logging
import os
import re
from typing import Optional, Set

from scripts.docs.utils.converter.constants import DEFAULT_EXCLUDE_PATTERNS
from scripts.docs.utils.converter.utils import split_frontmatter


class ObsidianToMD:
    """
    将Obsidian Wiki风格转换为标准Markdown的转换器。

    主要处理以下转换：
    1. Wiki链接 [[路径|文本]] -> [文本](路径.md)
    2. 嵌入链接 ![[路径]] -> ![](路径)
    3. 保留必要的frontmatter
    """

    def __init__(
        self, preserve_front_matter: bool = True, exclude_patterns: Optional[Set[str]] = None
    ):
        """
        初始化转换器。

        Args:
            preserve_front_matter: 是否保留frontmatter
            exclude_patterns: 要排除的文件模式集合
        """
        self.preserve_front_matter = preserve_front_matter
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
        self.logger = logging.getLogger(__name__)

    def should_exclude(self, file_path: str) -> bool:
        """
        判断文件是否应该被排除。

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果文件应该被排除则返回True
        """
        normalized_path = os.path.normpath(file_path)
        return any(re.match(pattern, normalized_path) for pattern in self.exclude_patterns)

    def convert_file(
        self, source: str, target: str, logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        将Obsidian格式文件转换为标准Markdown。

        Args:
            source: 源文件路径
            target: 目标文件路径
            logger: 可选的日志记录器

        Returns:
            bool: 转换是否成功
        """
        if logger:
            self.logger = logger

        # 检查文件是否应该被排除
        if self.should_exclude(source) or self.should_exclude(target):
            self.logger.info(f"跳过排除的文件: {source}")
            return True

        try:
            self.logger.info(f"转换文件: {source} -> {target}")

            # 确保目标目录存在
            os.makedirs(os.path.dirname(target), exist_ok=True)

            # 读取源文件
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()

            # 转换内容
            converted_content = self.convert_content(
                content, os.path.dirname(source), os.path.dirname(target)
            )

            # 写入目标文件
            with open(target, "w", encoding="utf-8") as f:
                f.write(converted_content)

            return True
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            return False

    def convert_content(self, content: str, source_dir: str, target_dir: str) -> str:
        """
        转换Obsidian内容为标准Markdown。

        Args:
            content: 原始Obsidian内容
            source_dir: 源文件目录路径
            target_dir: 目标文件目录路径

        Returns:
            str: 转换后的内容
        """
        # 分离frontmatter和内容
        frontmatter, main_content = split_frontmatter(content)

        # 转换主要内容
        converted_content = main_content

        # 转换Wiki链接
        converted_content = self._convert_wiki_links_with_text(converted_content)
        converted_content = self._convert_simple_wiki_links(converted_content)

        # 转换嵌入链接
        converted_content = self._convert_embedded_links(converted_content)

        # 重新组合frontmatter和内容
        if frontmatter and self.preserve_front_matter:
            return f"{frontmatter}\n\n{converted_content}"

        return converted_content

    def _convert_wiki_links_with_text(self, content: str) -> str:
        """
        转换带有显示文本的Wiki链接为标准链接。
        例如 [[路径|文本]] -> [文本](路径.md)

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """
        # 匹配带有显示文本的Wiki链接
        pattern = r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]"
        return re.sub(pattern, lambda m: f"[{m.group(2) or m.group(1)}]({m.group(1)}.md)", content)

    def _convert_simple_wiki_links(self, content: str) -> str:
        """
        转换简单Wiki链接为标准链接。
        例如 [[路径]] -> [路径](路径.md)

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """
        # 匹配简单的Wiki链接
        pattern = r"\[\[([^\]|#]+)(?:#[^\]]+)?\]\]"
        return re.sub(pattern, lambda m: f"[{m.group(1)}]({m.group(1)}.md)", content)

    def _convert_embedded_links(self, content: str) -> str:
        """
        转换嵌入链接为标准图片链接。
        例如 ![[路径]] -> ![](路径)

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """

        def replace_embed(match):
            path = match.group(1)
            alt_text = match.group(3) if match.group(3) else ""

            # 如果路径没有扩展名，添加.md
            if not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".md")):
                path = f"{path}.md"

            return f"![{alt_text}]({path})"

        # 匹配嵌入链接，包括可能的文本描述
        pattern = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"
        return re.sub(pattern, replace_embed, content)

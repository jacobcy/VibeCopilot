"""
将标准Markdown转换为Obsidian Wiki格式的工具。
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional, Set, Tuple

from adapters.obsidian.converter.constants import DEFAULT_EXCLUDE_PATTERNS
from adapters.obsidian.converter.utils import split_frontmatter


class MDToObsidian:
    """
    将标准Markdown转换为Obsidian Wiki风格的转换器。

    主要处理以下转换：
    1. 标准链接 [文本](路径.md) -> [[路径|文本]]
    2. 处理相对路径和绝对路径
    3. 优化frontmatter以适应Obsidian
    """

    def __init__(
        self,
        preserve_front_matter: bool = True,
        preserve_images: bool = True,
        exclude_patterns: Optional[Set[str]] = None,
    ):
        """
        初始化转换器。

        Args:
            preserve_front_matter: 是否保留frontmatter
            preserve_images: 是否保留图片链接格式
            exclude_patterns: 要排除的文件模式集合
        """
        self.preserve_front_matter = preserve_front_matter
        self.preserve_images = preserve_images
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
        将标准Markdown文件转换为Obsidian格式。

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

        # 检查是否涉及website/docs目录
        if "website/docs" in source or "website/docs" in target:
            self.logger.info(f"跳过website/docs目录下的文件: {source}")
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
        转换Markdown内容为Obsidian格式。

        Args:
            content: 原始Markdown内容
            source_dir: 源文件目录路径
            target_dir: 目标文件目录路径

        Returns:
            str: 转换后的内容
        """
        # 分离frontmatter和内容
        frontmatter, main_content = split_frontmatter(content)

        # 转换主要内容
        converted_content = main_content

        # 转换标准链接为Wiki链接，但排除图片链接
        if self.preserve_images:
            # 先处理非图片的标准链接
            converted_content = self._convert_normal_links(converted_content)
        else:
            # 所有链接都转换
            converted_content = self._convert_all_links(converted_content)

        # 重新组合frontmatter和内容
        if frontmatter and self.preserve_front_matter:
            return f"{frontmatter}\n\n{converted_content}"

        return converted_content

    def _convert_normal_links(self, content: str) -> str:
        """
        转换非图片的标准链接为Wiki链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """

        # 排除图片链接(!开头)，转换标准链接
        def replace_links(match):
            if match.group(0).startswith("!"):
                return match.group(0)  # 保留图片链接格式

            text = match.group(1)
            link = match.group(2)

            # 移除.md扩展名
            if link.endswith(".md"):
                link = link[:-3]

            # 创建Wiki链接
            return f"[[{link}|{text}]]"

        # 标准Markdown链接模式
        pattern = r"(?<!!)\[(.*?)\]\((.*?)\)"
        return re.sub(pattern, replace_links, content)

    def _convert_all_links(self, content: str) -> str:
        """
        转换所有标准链接为Wiki链接，包括图片链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """

        def replace_links(match):
            is_image = match.group(0).startswith("!")
            text = match.group(1)
            link = match.group(2)

            # 移除.md扩展名
            if link.endswith(".md"):
                link = link[:-3]

            # 创建Wiki链接
            if is_image:
                return f"![[{link}|{text}]]"
            else:
                return f"[[{link}|{text}]]"

        # 匹配所有链接，包括图片链接
        pattern = r"(!?)\[(.*?)\]\((.*?)\)"
        return re.sub(pattern, replace_links, content)

"""
目录生成器 - 自动生成文档目录和索引文件.

扫描文档目录结构，提取元数据，生成分类索引页面.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class IndexGenerator:
    """文档目录索引生成器，创建分类索引页面."""

    def __init__(self, base_dir: str):
        """
        初始化目录生成器.

        Args:
            base_dir: 文档根目录的绝对路径
        """
        self.base_dir = Path(base_dir)
        self.index_filename = "_index.md"

    def generate_indexes(self, target_dirs: Optional[List[str]] = None) -> List[str]:
        """
        为指定目录生成索引文件.

        Args:
            target_dirs: 要生成索引的目录列表(相对于base_dir)，
                         如果为None则为所有子目录生成索引

        Returns:
            生成的索引文件路径列表
        """
        generated_files = []

        if target_dirs:
            dirs = [self.base_dir / dir_path for dir_path in target_dirs]
        else:
            # 获取所有子目录
            dirs = [
                p for p in self.base_dir.glob("**") if p.is_dir() and not p.name.startswith(".")
            ]

        for directory in dirs:
            index_path = self.generate_index_for_directory(directory)
            if index_path:
                generated_files.append(str(index_path))

        return generated_files

    def generate_index_for_directory(self, directory: Path) -> Optional[Path]:
        """
        为单个目录生成索引文件.

        Args:
            directory: 目录路径

        Returns:
            生成的索引文件路径，如果没有生成则返回None
        """
        # 跳过隐藏目录
        if directory.name.startswith("."):
            return None

        # 获取目录中的所有Markdown文件
        md_files = list(directory.glob("*.md")) + list(directory.glob("*.mdx"))

        # 过滤掉索引文件本身
        content_files = [f for f in md_files if f.name != self.index_filename]

        # 如果目录为空，不生成索引
        if not content_files:
            return None

        # 提取文件元数据
        pages = []
        for file_path in content_files:
            metadata = self._extract_metadata(file_path)
            pages.append(
                {
                    "path": file_path,
                    "title": metadata.get("title", file_path.stem),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", "未分类"),
                    "created": metadata.get("created", ""),
                    "updated": metadata.get("updated", ""),
                }
            )

        # 生成索引文件内容
        index_content = self._generate_index_content(directory.name, pages)

        # 写入索引文件
        index_path = directory / self.index_filename
        index_path.write_text(index_content, encoding="utf-8")

        return index_path

    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        从Markdown文件中提取元数据.

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        metadata = {}
        try:
            content = file_path.read_text(encoding="utf-8")

            # 提取YAML前置元数据
            frontmatter_match = re.search(r"^---\s+(.*?)\s+---", content, re.DOTALL)
            if frontmatter_match:
                yaml_text = frontmatter_match.group(1)
                try:
                    metadata = yaml.safe_load(yaml_text) or {}
                except yaml.YAMLError:
                    # 如果YAML解析失败，使用简单正则提取
                    for line in yaml_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()

            # 如果没有标题元数据，尝试从一级标题提取
            if "title" not in metadata:
                title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
                if title_match:
                    metadata["title"] = title_match.group(1).strip()

            # 如果没有描述元数据，尝试提取第一段落
            if "description" not in metadata:
                # 跳过前置元数据和一级标题
                content_without_fm = re.sub(r"^---\s+.*?\s+---", "", content, flags=re.DOTALL)
                content_without_fm = re.sub(r"^# .+$", "", content_without_fm, flags=re.MULTILINE)

                # 提取第一个非空段落
                paragraphs = re.findall(r"([^\n]+)\n\n", content_without_fm)
                if paragraphs:
                    metadata["description"] = paragraphs[0].strip()

        except (UnicodeDecodeError, IOError):
            # 文件读取或解码错误，返回空元数据
            pass

        return metadata

    def _generate_index_content(self, directory_name: str, pages: List[Dict]) -> str:
        """
        生成索引文件内容.

        Args:
            directory_name: 目录名称
            pages: 页面元数据列表

        Returns:
            生成的索引文件内容
        """
        # 创建前置元数据
        header = f"""---
title: {directory_name} 目录
description: {directory_name}文档索引
category: 索引
generated: true
---

# {directory_name} 文档目录

"""

        # 按类别分组
        categories = {}
        for page in pages:
            category = page["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(page)

        # 生成分类索引
        content = header

        # 对类别排序
        for category, category_pages in sorted(categories.items()):
            content += f"## {category}\n\n"

            # 对同一类别内的页面按标题排序
            for page in sorted(category_pages, key=lambda p: p["title"]):
                rel_path = os.path.relpath(page["path"], start=page["path"].parent)
                title = page["title"]
                description = page["description"]

                # 构建链接项
                link_item = f"- [{title}](./{rel_path})"
                if description:
                    link_item += f": {description}"

                content += link_item + "\n"

            content += "\n"

        return content

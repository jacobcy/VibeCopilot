"""
文件映射模块

处理Obsidian和Docusaurus之间的文件映射关系
"""

from pathlib import Path
from typing import Dict

from .base import BaseConverter, logger


class FileMappingHandler(BaseConverter):
    """文件映射处理器"""

    def build_file_mapping(self) -> Dict[str, Path]:
        """
        构建Obsidian文件路径与文件的映射

        Returns:
            文件名到文件路径的映射
        """
        file_mapping = {}

        # 遍历所有Markdown文件
        for md_file in self.obsidian_dir.glob("**/*.md"):
            # 只跳过.obsidian配置目录和assets目录，而不是路径中包含这些名称的所有目录
            if (
                md_file.name == ".obsidian"
                or md_file.parent.name == ".obsidian"
                or md_file.parent.name == "assets"
            ):
                continue

            # 使用文件名作为键（去除扩展名）
            file_mapping[md_file.stem] = md_file.relative_to(self.obsidian_dir)

        self.file_mapping = file_mapping
        logger.info(f"构建了 {len(file_mapping)} 个文件的映射")
        return file_mapping

    def get_file_by_name(self, filename: str) -> Path:
        """
        根据文件名获取文件路径

        Args:
            filename: 文件名（不含扩展名）

        Returns:
            文件的相对路径
        """
        if not self.file_mapping:
            self.build_file_mapping()

        if filename in self.file_mapping:
            return self.file_mapping[filename]
        return None

    def ensure_file_mapping(self) -> None:
        """
        确保文件映射已经构建
        """
        if not self.file_mapping:
            self.build_file_mapping()

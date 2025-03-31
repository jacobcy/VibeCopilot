"""
Docusaurus同步工具 - 将Obsidian文档同步到Docusaurus.

监控Obsidian文档变更，自动转换并同步到Docusaurus文档目录.
"""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..converters.index_generator import IndexGenerator
from ..converters.link_converter import LinkConverter


class DocusaurusSync:
    """Obsidian到Docusaurus的文档同步工具."""

    def __init__(
        self, obsidian_dir: str, docusaurus_dir: str, exclude_patterns: Optional[List[str]] = None
    ):
        """
        初始化Docusaurus同步工具.

        Args:
            obsidian_dir: Obsidian文档根目录
            docusaurus_dir: Docusaurus文档目录
            exclude_patterns: 要排除的文件/目录模式列表
        """
        self.obsidian_dir = Path(obsidian_dir)
        self.docusaurus_dir = Path(docusaurus_dir)
        self.exclude_patterns = exclude_patterns or [".obsidian/**", ".git/**", "**/.DS_Store"]

        self.link_converter = LinkConverter(obsidian_dir)
        self.index_generator = IndexGenerator(docusaurus_dir)

        self.logger = logging.getLogger("docusaurus_sync")

        # 确保目标目录存在
        self.docusaurus_dir.mkdir(parents=True, exist_ok=True)

    def sync_all(self) -> Dict[str, int]:
        """
        同步所有文档.

        Returns:
            同步统计信息字典 {'added': n, 'updated': n, 'deleted': n}
        """
        # 获取Obsidian和Docusaurus中的所有文档
        obsidian_files = self._get_all_markdown_files(self.obsidian_dir)
        docusaurus_files = self._get_all_markdown_files(self.docusaurus_dir)

        # 转换路径为相对路径，便于比较
        obsidian_relative = {self._to_relative_path(p, self.obsidian_dir) for p in obsidian_files}
        docusaurus_relative = {
            self._to_relative_path(p, self.docusaurus_dir) for p in docusaurus_files
        }

        # 计算需要添加、更新和删除的文件
        to_add = obsidian_relative - docusaurus_relative
        to_update = obsidian_relative.intersection(docusaurus_relative)
        to_delete = docusaurus_relative - obsidian_relative

        # 执行同步操作
        added = self._sync_files(to_add, "add")
        updated = self._sync_files(to_update, "update")
        deleted = self._delete_files(to_delete)

        # 生成索引文件
        self.generate_indexes()

        return {"added": added, "updated": updated, "deleted": deleted}

    def sync_file(self, file_path: str) -> bool:
        """
        同步单个文件.

        Args:
            file_path: 要同步的文件路径(相对于obsidian_dir)

        Returns:
            同步是否成功
        """
        src_path = self.obsidian_dir / file_path
        dst_path = self.docusaurus_dir / file_path

        if not src_path.exists():
            # 如果源文件不存在，但目标文件存在，则删除目标文件
            if dst_path.exists():
                dst_path.unlink()
                return True
            return False

        # 确保目标目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取内容并转换链接
        try:
            content = src_path.read_text(encoding="utf-8")
            converted = self.link_converter.obsidian_to_docusaurus(content, file_path)

            # 写入转换后的内容
            dst_path.write_text(converted, encoding="utf-8")

            # 尝试生成目录索引
            self.index_generator.generate_index_for_directory(dst_path.parent)

            return True

        except Exception as e:
            self.logger.error(f"同步文件失败: {file_path} - {str(e)}")
            return False

    def generate_indexes(self) -> List[str]:
        """
        为所有文档目录生成索引文件.

        Returns:
            生成的索引文件路径列表
        """
        return self.index_generator.generate_indexes()

    def _sync_files(self, file_paths: Set[str], mode: str) -> int:
        """
        同步文件集合.

        Args:
            file_paths: 要同步的文件路径集合
            mode: 同步模式 ('add' 或 'update')

        Returns:
            成功同步的文件数量
        """
        success_count = 0

        for rel_path in file_paths:
            if self.sync_file(rel_path):
                success_count += 1
                self.logger.info(f"{mode.capitalize()}d: {rel_path}")

        return success_count

    def _delete_files(self, file_paths: Set[str]) -> int:
        """
        删除文件集合.

        Args:
            file_paths: 要删除的文件路径集合

        Returns:
            成功删除的文件数量
        """
        success_count = 0

        for rel_path in file_paths:
            # 跳过索引文件
            if Path(rel_path).name == self.index_generator.index_filename:
                continue

            dst_path = self.docusaurus_dir / rel_path

            if dst_path.exists():
                try:
                    dst_path.unlink()
                    success_count += 1
                    self.logger.info(f"Deleted: {rel_path}")
                except Exception as e:
                    self.logger.error(f"删除文件失败: {rel_path} - {str(e)}")

        return success_count

    def _get_all_markdown_files(self, root_dir: Path) -> List[Path]:
        """
        获取目录中的所有Markdown文件.

        Args:
            root_dir: 根目录

        Returns:
            Markdown文件路径列表
        """
        md_files = []

        for ext in [".md", ".mdx", ".markdown"]:
            md_files.extend(root_dir.glob(f"**/*{ext}"))

        # 过滤排除的文件
        filtered_files = []
        for file_path in md_files:
            rel_path = self._to_relative_path(file_path, root_dir)
            if not self._is_excluded(rel_path):
                filtered_files.append(file_path)

        return filtered_files

    def _is_excluded(self, rel_path: str) -> bool:
        """
        检查文件是否被排除.

        Args:
            rel_path: 相对文件路径

        Returns:
            是否排除该文件
        """
        from fnmatch import fnmatch

        for pattern in self.exclude_patterns:
            if fnmatch(rel_path, pattern):
                return True

        return False

    def _to_relative_path(self, path: Path, base_dir: Path) -> str:
        """
        转换为相对路径.

        Args:
            path: 文件路径
            base_dir: 基准目录

        Returns:
            相对路径字符串
        """
        rel_path = str(path.relative_to(base_dir))

        # 确保使用正斜杠
        return rel_path.replace("\\", "/")

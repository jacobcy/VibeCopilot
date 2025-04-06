"""
Obsidian到Docusaurus转换基础模块

提供转换器的基类和通用功能
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional, Union

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("obsidian_to_docusaurus")


class BaseConverter:
    """Obsidian到Docusaurus转换器基类"""

    # Obsidian链接模式: [[文件名]] 或 [[文件名|显示文本]]
    OBSIDIAN_LINK_PATTERN = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # Obsidian嵌入模式: ![[文件名]]
    OBSIDIAN_EMBED_PATTERN = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    def __init__(
        self,
        obsidian_dir: Union[str, Path],
        docusaurus_dir: Union[str, Path],
        assets_dir: Optional[str] = None,
    ):
        """
        初始化转换器基类

        Args:
            obsidian_dir: Obsidian文档目录
            docusaurus_dir: Docusaurus文档目录
            assets_dir: 资源文件目录
        """
        self.obsidian_dir = Path(obsidian_dir)
        self.docusaurus_dir = Path(docusaurus_dir)
        self.assets_dir = Path(assets_dir) if assets_dir else self.obsidian_dir / "assets"

        # 确保目录存在
        self.docusaurus_dir.mkdir(parents=True, exist_ok=True)
        (self.docusaurus_dir / "assets").mkdir(parents=True, exist_ok=True)

        # 编译正则表达式
        self.obsidian_link_regex = re.compile(self.OBSIDIAN_LINK_PATTERN)
        self.obsidian_embed_regex = re.compile(self.OBSIDIAN_EMBED_PATTERN)

        # 存储文件映射
        self.file_mapping = {}

    def is_image_file(self, filename: str) -> bool:
        """
        判断文件是否为图片

        Args:
            filename: 文件名

        Returns:
            是否为图片
        """
        if "." not in filename:
            return False

        ext = filename.split(".")[-1].lower()
        return ext in ["png", "jpg", "jpeg", "gif", "svg"]

    def get_relative_path(self, path1: Union[str, Path], path2: Union[str, Path]) -> str:
        """
        获取两个路径间的相对路径

        Args:
            path1: 第一个路径
            path2: 第二个路径

        Returns:
            相对路径字符串
        """
        rel_path = os.path.relpath(str(path1), str(path2))
        # 处理Windows路径
        rel_path = rel_path.replace("\\", "/")
        return rel_path

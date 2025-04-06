"""
配置管理器 - 处理文档系统的配置和设置.

管理Obsidian和Docusaurus配置文件，以及同步设置.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.docs_engine.config import (
    ConfigLoader,
    create_default_config,
    generate_docusaurus_sidebar,
    generate_obsidian_config,
)

logger = logging.getLogger(__name__)


class ConfigManager:
    """文档系统配置管理器，处理配置文件和设置."""

    def __init__(self, base_dir: str):
        """
        初始化配置管理器.

        Args:
            base_dir: 项目根目录
        """
        self.base_dir = Path(base_dir)
        self.config_loader = ConfigLoader(base_dir)

        # 加载或创建默认配置
        self._load_config()

    def _load_config(self):
        """加载配置，如果不存在则创建默认配置."""
        self.config = self.config_loader.load_config()
        if not self.config:
            self.config = create_default_config(self.base_dir)
            self._save_config()

    def _save_config(self):
        """保存配置到文件."""
        self.config_loader.save_config(self.config)

    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置.

        Returns:
            配置字典
        """
        return self.config

    def get_obsidian_config(self) -> Dict[str, Any]:
        """
        获取Obsidian配置.

        Returns:
            Obsidian配置字典
        """
        return self.config["obsidian"]

    def get_docusaurus_config(self) -> Dict[str, Any]:
        """
        获取Docusaurus配置.

        Returns:
            Docusaurus配置字典
        """
        return self.config["docusaurus"]

    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        更新配置项.

        Args:
            section: 配置部分名称
            key: 配置键名
            value: 配置值

        Returns:
            更新是否成功
        """
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            self._save_config()
            return True
        return False

    def generate_obsidian_config(self, output_dir: Optional[str] = None) -> bool:
        """
        生成Obsidian配置文件.

        Args:
            output_dir: 输出目录，默认为obsidian_vault_dir/.obsidian

        Returns:
            生成是否成功
        """
        return generate_obsidian_config(self.config["obsidian"], output_dir)

    def generate_docusaurus_sidebar(self) -> Dict[str, Any]:
        """
        生成Docusaurus侧边栏配置.

        Returns:
            侧边栏配置字典
        """
        return generate_docusaurus_sidebar(self.config["docusaurus"], self.config["templates"])

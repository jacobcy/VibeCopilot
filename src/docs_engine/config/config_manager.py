"""
配置管理器 - 处理文档系统的配置和设置.

管理Obsidian和Docusaurus配置文件，以及同步设置.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigManager:
    """文档系统配置管理器，处理配置文件和设置."""

    def __init__(self, base_dir: str):
        """
        初始化配置管理器.

        Args:
            base_dir: 项目根目录
        """
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.config_file = self.config_dir / "docs_config.json"

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载或创建默认配置
        self._load_config()

    def _load_config(self):
        """加载配置，如果不存在则创建默认配置."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = self._create_default_config()
        else:
            self.config = self._create_default_config()
            self._save_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """
        创建默认配置.

        Returns:
            默认配置字典
        """
        return {
            "obsidian": {
                "vault_dir": str(self.base_dir / "docs"),
                "exclude_patterns": [
                    ".obsidian/**",
                    ".git/**",
                    "**/.DS_Store",
                    "**/node_modules/**",
                ],
                "plugins": ["dataview", "templater", "obsidian-git"],
            },
            "docusaurus": {
                "content_dir": str(self.base_dir / "website" / "docs"),
                "sidebar_category_order": ["指南", "API文档", "教程", "参考"],
            },
            "sync": {
                "auto_sync": True,
                "watch_for_changes": True,
                "sync_on_startup": True,
                "backup_before_sync": True,
            },
            "templates": {
                "template_dir": str(self.base_dir / "templates"),
                "default_template": "default",
                "default_category": "未分类",
            },
        }

    def _save_config(self):
        """保存配置到文件."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

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
        try:
            vault_dir = Path(self.config["obsidian"]["vault_dir"])
            config_dir = Path(output_dir) if output_dir else vault_dir / ".obsidian"

            # 确保配置目录存在
            config_dir.mkdir(parents=True, exist_ok=True)

            # 基础应用配置
            app_config = {
                "baseFolderPath": "",
                "readableLineLength": True,
                "strictLineBreaks": False,
                "showFrontmatter": True,
                "defaultViewMode": "source",
                "livePreview": True,
            }

            # 写入应用配置
            with open(config_dir / "app.json", "w", encoding="utf-8") as f:
                json.dump(app_config, f, indent=2)

            # 创建插件目录
            plugins_dir = config_dir / "plugins"
            plugins_dir.mkdir(exist_ok=True)

            # 配置插件
            for plugin in self.config["obsidian"]["plugins"]:
                plugin_dir = plugins_dir / plugin
                plugin_dir.mkdir(exist_ok=True)

                # 创建基本插件配置
                with open(plugin_dir / "data.json", "w", encoding="utf-8") as f:
                    json.dump({"enabled": True}, f, indent=2)

            return True

        except Exception as e:
            print(f"生成Obsidian配置失败: {str(e)}")
            return False

    def generate_docusaurus_sidebar(self) -> Dict[str, Any]:
        """
        生成Docusaurus侧边栏配置.

        Returns:
            侧边栏配置字典
        """
        try:
            content_dir = Path(self.config["docusaurus"]["content_dir"])
            category_order = self.config["docusaurus"]["sidebar_category_order"]

            # 扫描文档目录
            categories = {}

            # 遍历所有markdown文件
            for md_file in content_dir.glob("**/*.md"):
                # 跳过索引文件
                if md_file.name == "_index.md":
                    continue

                # 读取文件元数据
                category = self._get_doc_category(md_file)

                if category not in categories:
                    categories[category] = []

                # 计算相对路径
                rel_path = md_file.relative_to(content_dir)
                doc_id = str(rel_path.with_suffix(""))

                categories[category].append(
                    {"type": "doc", "id": doc_id, "label": self._get_doc_title(md_file)}
                )

            # 构建侧边栏配置
            sidebar = []

            # 先添加有序类别
            for category in category_order:
                if category in categories:
                    sidebar.append(
                        {
                            "type": "category",
                            "label": category,
                            "items": sorted(categories[category], key=lambda x: x["label"]),
                        }
                    )

                    # 从分类中移除已处理的类别
                    del categories[category]

            # 添加剩余类别
            for category, items in categories.items():
                sidebar.append(
                    {
                        "type": "category",
                        "label": category,
                        "items": sorted(items, key=lambda x: x["label"]),
                    }
                )

            return {"sidebar": sidebar}

        except Exception as e:
            print(f"生成侧边栏配置失败: {str(e)}")
            return {"sidebar": []}

    def _get_doc_category(self, file_path: Path) -> str:
        """
        获取文档的分类.

        Args:
            file_path: 文档文件路径

        Returns:
            文档分类名称
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 尝试解析前置元数据
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    front_matter = content[3:end].strip()
                    try:
                        metadata = yaml.safe_load(front_matter)
                        if metadata and "category" in metadata:
                            return metadata["category"]
                    except yaml.YAMLError:
                        pass

            # 如果没有找到分类，使用父目录名称
            parent_dir = file_path.parent.name
            if parent_dir and parent_dir != ".":
                return parent_dir

            # 默认分类
            return self.config["templates"]["default_category"]

        except Exception:
            return self.config["templates"]["default_category"]

    def _get_doc_title(self, file_path: Path) -> str:
        """
        获取文档的标题.

        Args:
            file_path: 文档文件路径

        Returns:
            文档标题
        """
        import re

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 尝试从前置元数据获取标题
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    front_matter = content[3:end].strip()
                    try:
                        metadata = yaml.safe_load(front_matter)
                        if metadata and "title" in metadata:
                            return metadata["title"]
                    except yaml.YAMLError:
                        pass

            # 尝试从一级标题获取
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()

            # 使用文件名作为标题
            return file_path.stem

        except Exception:
            return file_path.stem

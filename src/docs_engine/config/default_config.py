"""
默认配置生成器

提供文档系统的默认配置生成功能
"""

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def create_default_config(base_dir: str) -> Dict[str, Any]:
    """
    创建默认配置

    Args:
        base_dir: 项目根目录

    Returns:
        默认配置字典
    """
    base_path = Path(base_dir)

    return {
        "obsidian": {
            "vault_dir": str(base_path / "docs"),
            "exclude_patterns": [
                ".obsidian/**",
                ".git/**",
                "**/.DS_Store",
                "**/node_modules/**",
            ],
            "plugins": ["dataview", "templater", "obsidian-git"],
        },
        "docusaurus": {
            "content_dir": str(base_path / "website" / "docs"),
            "sidebar_category_order": ["指南", "API文档", "教程", "参考"],
        },
        "sync": {
            "auto_sync": True,
            "watch_for_changes": True,
            "sync_on_startup": True,
            "backup_before_sync": True,
        },
        "templates": {
            "template_dir": str(base_path / "templates"),
            "default_template": "default",
            "default_category": "未分类",
        },
    }

"""
Obsidian配置生成器

负责生成Obsidian配置文件
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def generate_obsidian_config(
    obsidian_config: Dict[str, Any], output_dir: Optional[str] = None
) -> bool:
    """
    生成Obsidian配置文件

    Args:
        obsidian_config: Obsidian配置字典
        output_dir: 输出目录，默认为obsidian_vault_dir/.obsidian

    Returns:
        生成是否成功
    """
    try:
        vault_dir = Path(obsidian_config["vault_dir"])
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
        for plugin in obsidian_config["plugins"]:
            plugin_dir = plugins_dir / plugin
            plugin_dir.mkdir(exist_ok=True)

            # 创建基本插件配置
            with open(plugin_dir / "data.json", "w", encoding="utf-8") as f:
                json.dump({"enabled": True}, f, indent=2)

        logger.info(f"成功生成Obsidian配置: {config_dir}")
        return True

    except Exception as e:
        logger.error(f"生成Obsidian配置失败: {str(e)}")
        return False

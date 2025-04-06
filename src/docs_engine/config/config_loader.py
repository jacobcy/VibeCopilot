"""
配置加载器

负责加载和保存文档系统的配置文件
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器类，负责配置文件的读写操作"""

    def __init__(self, base_dir: str):
        """初始化配置加载器

        Args:
            base_dir: 项目根目录
        """
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.config_file = self.config_dir / "docs_config.json"

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件

        Returns:
            配置字典，如果不存在则返回None
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return None
        else:
            logger.warning(f"配置文件不存在: {self.config_file}")
            return None

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件

        Args:
            config: 配置字典

        Returns:
            是否成功保存
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get_config_path(self) -> Path:
        """获取配置文件路径

        Returns:
            配置文件路径
        """
        return self.config_file

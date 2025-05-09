"""
配置设置模块

提供 SettingsConfig 类用于封装 settings.json 文件的管理
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

SETTINGS_FILE_PATH = ".vibecopilot/config/settings.json"


class SettingsConfig:
    """封装 settings.json 文件的配置类"""

    def __init__(self, settings_path: str = SETTINGS_FILE_PATH):
        """初始化配置对象

        Args:
            settings_path: 配置文件路径，默认为 SETTINGS_FILE_PATH
        """
        self.settings_path = settings_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.debug(f"已加载配置文件: {self.settings_path}")
            else:
                logger.info(f"配置文件不存在，使用默认空配置: {self.settings_path}")
                self._config = {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = {}

    def save(self) -> bool:
        """保存配置到文件

        Returns:
            bool: 是否成功保存
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)

            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {self.settings_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点分隔路径，如 "github.owner"
            default: 默认值，当配置不存在时返回

        Returns:
            Any: 配置值或默认值
        """
        if not key:
            return default

        parts = key.split(".")
        current = self._config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def set(self, key: str, value: Any) -> bool:
        """设置配置值

        Args:
            key: 配置键，支持点分隔路径，如 "github.owner"
            value: 配置值

        Returns:
            bool: 是否成功设置
        """
        if not key:
            return False

        parts = key.split(".")
        current = self._config

        # 导航到最后一个部分的父级
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        # 设置值
        current[parts[-1]] = value

        return True

    def update(self, config_dict: Dict[str, Any]) -> bool:
        """批量更新配置

        Args:
            config_dict: 要更新的配置字典

        Returns:
            bool: 是否成功更新
        """
        try:
            self._config.update(config_dict)
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False

    def __getitem__(self, key: str) -> Any:
        """使 SettingsConfig 实例支持字典类操作

        Args:
            key: 配置键

        Returns:
            Any: 配置值

        Raises:
            KeyError: 当配置键不存在时
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """使 SettingsConfig 实例支持字典类操作

        Args:
            key: 配置键
            value: 配置值
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """检查配置键是否存在

        Args:
            key: 配置键

        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None

"""
系统配置仓库模块

提供SystemConfig数据访问实现，使用统一的Repository模式。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.system_config import SystemConfig


class SystemConfigRepository(Repository[SystemConfig]):
    """SystemConfig仓库类"""

    def __init__(self, session: Session):
        """初始化SystemConfig仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, SystemConfig)

    def get_by_key(self, key: str) -> Optional[SystemConfig]:
        """根据键名获取配置

        Args:
            key: 配置键名

        Returns:
            SystemConfig对象或None
        """
        return self.session.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值或默认值
        """
        config = self.get_by_key(key)
        return config.value if config else default

    def set_value(self, key: str, value: Any, description: Optional[str] = None) -> SystemConfig:
        """设置配置值

        如果配置不存在，则创建；否则更新

        Args:
            key: 配置键名
            value: 配置值
            description: 配置描述

        Returns:
            更新或创建的SystemConfig对象
        """
        config = self.get_by_key(key)
        if config:
            config.value = str(value)
            if description:
                config.description = description
            self.session.commit()
            return config
        else:
            # 创建新配置
            config_data = {"key": key, "value": str(value), "description": description}
            return self.create(config_data)

    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置

        Returns:
            配置列表
        """
        return self.session.query(SystemConfig).all()

    def delete_config(self, key: str) -> bool:
        """删除配置

        Args:
            key: 配置键名

        Returns:
            是否成功删除
        """
        config = self.get_by_key(key)
        if config:
            self.session.delete(config)
            self.session.commit()
            return True
        return False

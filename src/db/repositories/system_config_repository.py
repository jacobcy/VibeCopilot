"""
系统配置仓库模块

提供SystemConfig数据访问实现，使用统一的Repository模式。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# 再次修正导入路径，指向正确的 Repository 基类文件
# from src.db.repositories.base_repository import Repository # 错误的路径
from src.db.repository import Repository  # 正确的基础仓库类路径
from src.models.db.system_config import SystemConfig  # 正确的路径

logger = logging.getLogger(__name__)


class SystemConfigRepository(Repository[SystemConfig]):
    """系统配置仓库，用于管理系统配置信息 (无状态)"""

    def __init__(self):
        """初始化系统配置仓库 (无状态，不接收 session)"""
        super().__init__(SystemConfig)  # 调用基类，传入模型类
        # 不再存储 self.session
        # self.model 属性由基类处理或此处无需设置

    def get_config(self, session: Session, key: str) -> Optional[SystemConfig]:
        """获取指定键的配置项

        Args:
            session: 数据库会话
            key: 配置项的键

        Returns:
            配置项对象或 None
        """
        # 使用传入的 session
        return session.query(self.model_class).filter_by(key=key).first()

    def set_config(self, session: Session, key: str, value: str):
        """设置或更新配置项

        Args:
            session: 数据库会话
            key: 配置项的键
            value: 配置项的值
        """
        # 使用传入的 session 调用 get_config
        config = self.get_config(session, key)
        if config:
            logger.debug(f"更新配置项: {key}")
            config.value = value
        else:
            logger.debug(f"创建新配置项: {key}")
            config = SystemConfig(key=key, value=value)
            session.add(config)  # 使用传入的 session 添加
        # 不需要在这里 commit，由 session scope 管理

    def delete_config(self, session: Session, key: str):
        """删除配置项

        Args:
            session: 数据库会话
            key: 配置项的键
        """
        # 使用传入的 session 调用 get_config
        config = self.get_config(session, key)
        if config:
            logger.debug(f"删除配置项: {key}")
            session.delete(config)  # 使用传入的 session 删除
            # 不需要在这里 commit

    def get_by_key(self, session: Session, key: str) -> Optional[SystemConfig]:
        """根据键名获取配置

        Args:
            session: 数据库会话
            key: 配置键名

        Returns:
            SystemConfig对象或None
        """
        # 使用传入的 session
        return session.query(self.model_class).filter(self.model_class.key == key).first()

    def get_value(self, session: Session, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            session: 数据库会话
            key: 配置键名
            default: 默认值

        Returns:
            配置值或默认值
        """
        # 使用传入的 session 调用 get_by_key
        config = self.get_by_key(session, key)
        return config.value if config else default

    def set_value(self, session: Session, key: str, value: Any, description: Optional[str] = None) -> SystemConfig:
        """设置配置值

        如果配置不存在，则创建；否则更新

        Args:
            session: 数据库会话
            key: 配置键名
            value: 配置值
            description: 配置描述

        Returns:
            更新或创建的SystemConfig对象
        """
        # 使用传入的 session 调用 get_by_key
        config = self.get_by_key(session, key)
        if config:
            config.value = str(value)
            if description:
                config.description = description
            # 不再需要 commit，session scope 管理
            # session.commit()
            return config
        else:
            # 创建新配置
            config_data = {"key": key, "value": str(value), "description": description}
            # 使用基类的 create 方法，传入 session
            return self.create(session, config_data)

    def get_all_configs(self, session: Session) -> List[SystemConfig]:
        """获取所有配置

        Args:
            session: 数据库会话

        Returns:
            配置列表
        """
        # 使用传入的 session
        return session.query(self.model_class).all()

"""
系统配置数据库模型

定义系统配置相关的数据库模型，用于存储全局配置和状态。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, String, Text

from src.models.db.base import Base


class SystemConfig(Base):
    """系统配置数据库模型，存储键值对形式的配置项"""

    __tablename__ = "system_configs"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        """初始化SystemConfig"""
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """从字典创建实例"""
        return cls(key=data.get("key"), value=data.get("value"), description=data.get("description"))

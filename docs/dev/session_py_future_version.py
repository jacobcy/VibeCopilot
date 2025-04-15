"""
数据库会话模块

提供数据库会话管理功能。

警告: 该模块已被弃用，计划在下一个主版本(v2.0.0)中移除。
请直接从src.db导入SessionLocal和get_db，例如:
    from src.db import SessionLocal, get_db
"""

import warnings

from sqlalchemy.orm import Session

# 从连接管理器导入，保持与原来相同的实现方式
from src.db.connection_manager import get_session_factory

# 创建默认会话工厂
SessionLocal = get_session_factory()

# 添加强烈弃用警告
warnings.warn("src.db.session模块已被正式弃用，将在v2.0.0版本中移除。请直接从src.db导入SessionLocal和get_db", DeprecationWarning, stacklevel=2)


def get_db() -> Session:
    """获取数据库会话

    警告: 此函数已被弃用，计划在v2.0.0版本中移除。
    请使用 from src.db import get_db 代替。

    Returns:
        数据库会话对象
    """
    warnings.warn("src.db.session.get_db()已被弃用，将在v2.0.0版本中移除。请直接使用src.db.get_db()", DeprecationWarning, stacklevel=2)
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

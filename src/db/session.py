"""
数据库会话模块

提供数据库会话管理功能。
"""

from sqlalchemy.orm import Session

from src.db import get_session_factory

# 创建默认会话工厂
SessionLocal = get_session_factory()


def get_db() -> Session:
    """获取数据库会话

    Returns:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

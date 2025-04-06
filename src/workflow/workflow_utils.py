#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流工具模块

提供工作流系统的通用工具和辅助函数。
"""

import logging

from sqlalchemy.orm import Session

from src.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_session() -> Session:
    """获取数据库会话

    Returns:
        SQLAlchemy会话对象
    """
    return SessionLocal()

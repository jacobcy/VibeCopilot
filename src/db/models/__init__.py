"""
数据库模型模块

定义VibeCopilot统一数据库模型，包括：
1. 数据库基础设施
2. 业务实体模型
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

__all__ = ["Base"]

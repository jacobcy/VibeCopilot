"""
数据库模型模块 (已重定向)

注意: 此模块已被重定向到src.models.db
请使用 from src.models.db import Base 替代 from src.db.models import Base
"""

# 为保持向后兼容，从新位置导入
from src.models.db import Base

__all__ = ["Base"]

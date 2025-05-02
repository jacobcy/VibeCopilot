import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库URL，应根据.env或配置文件设置
DATABASE_URL = "sqlite:///./test.db"  # 示例，使用SQLite；请根据实际环境调整

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

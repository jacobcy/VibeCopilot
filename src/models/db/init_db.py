import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config import config_manager  # Import config manager
from src.models.db import docs_engine  # Assuming docs models exist here
from src.models.db import template  # Assuming template models exist here
from src.models.db import flow_session, roadmap, task

# Explicitly import all model modules to ensure they are registered with Base
from src.models.db.base import Base  # Import Base from its definition

# Add imports for any other model files...


logger = logging.getLogger(__name__)


def get_db_path():
    """获取数据库文件路径

    优先级:
    1. DATABASE_URL 环境变量 (提取路径部分)
    2. 默认值: data/vibecopilot.db (相对于项目根目录)

    Returns:
        str: 数据库文件的完整路径
    """
    # 获取 DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        if database_url.startswith("sqlite:///"):
            # 提取路径部分
            db_path = database_url[len("sqlite:///") :]
            # 确保是绝对路径
            if not os.path.isabs(db_path):
                logger.warning(f"数据库路径是相对路径: {db_path}，将基于项目根目录转换为绝对路径")
                db_path = os.path.abspath(db_path)
            return db_path
        else:
            logger.warning(f"不支持的数据库URL格式: {database_url}，将使用默认SQLite路径")

    # 使用默认路径
    default_path = os.path.abspath("data/vibecopilot.db")
    logger.info(f"使用默认数据库路径: {default_path}")
    return default_path


def init_db():
    """初始化数据库

    创建数据库表结构，如果表已存在则不会重新创建

    Returns:
        bool: 初始化是否成功
    """
    try:
        db_path = get_db_path()

        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # 构建数据库URL
        database_url = f"sqlite:///{db_path}"
        logger.info(f"初始化数据库: {database_url}")

        # 创建数据库引擎
        engine = create_engine(database_url, connect_args={"check_same_thread": False})

        # 创建所有表
        Base.metadata.create_all(engine)
        logger.info(f"数据库表已成功创建在 {db_path}")

        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # TODO: 在这里添加初始数据，如果需要的话

        db.commit()
        db.close()
        return True

    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = init_db()
    if success:
        print("数据库初始化成功")
    else:
        print("数据库初始化失败，请检查日志")

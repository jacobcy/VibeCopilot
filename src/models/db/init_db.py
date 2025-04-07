import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 导入所有需要初始化的模型
from src.models.db.roadmap import Base, Task

logger = logging.getLogger(__name__)


def get_db_path():
    """获取数据库文件路径

    返回SQLite数据库文件的绝对路径，确保目录存在

    Returns:
        str: 数据库文件的完整路径
    """
    home_dir = os.path.expanduser("~")
    db_dir = os.path.join(home_dir, ".vibecopilot")

    # 确保目录存在
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    return os.path.join(db_dir, "vibecopilot.db")


def init_db():
    """初始化数据库

    创建数据库表结构，如果表已存在则不会重新创建

    Returns:
        bool: 初始化是否成功
    """
    db_path = get_db_path()

    # 创建数据库引擎
    engine = create_engine(f"sqlite:///{db_path}")

    # 创建所有表
    try:
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

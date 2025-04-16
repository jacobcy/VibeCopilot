import logging
import os
from pathlib import Path

# 移除 create_engine, sessionmaker 的导入，因为不再直接使用
from sqlalchemy.ext.declarative import declarative_base

from src.core.config import get_config  # 更新导入
from src.models.db import docs_engine  # Assuming docs models exist here
from src.models.db import log  # 导入日志模型
from src.models.db import template  # Assuming template models exist here
from src.models.db import flow_session, roadmap, task

# Explicitly import all model modules to ensure they are registered with Base
from src.models.db.base import Base  # Import Base from its definition

# Add imports for any other model files...


logger = logging.getLogger(__name__)

# 移除冗余的 get_db_path 函数
# def get_db_path(): ...


def init_db(force_recreate=False):
    """初始化数据库

    使用 DBConnectionManager 确保数据库表结构存在

    Args:
        force_recreate: 是否强制重新创建表

    Returns:
        bool: 初始化是否成功
    """
    # 引入 connection_manager 相关函数
    from src.db.connection_manager import ensure_tables_exist, get_engine

    logger.info(f"数据库初始化被调用 (force_recreate={force_recreate})")

    try:
        # 使用连接管理器确保表存在
        success = ensure_tables_exist(force_recreate)
        if success:
            logger.info("数据库表初始化/验证完成")
        else:
            # ensure_tables_exist 内部会记录错误，这里只记录最终结果
            logger.error("数据库表初始化/验证失败")
            return False

        # 返回 True 表示成功 (即使表已存在)
        return True

    except Exception as e:
        # ensure_tables_exist 内部的错误应该已经记录
        logger.error(f"初始化数据库时发生意外错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 可以添加 --force 参数支持
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the VibeCopilot database.")
    parser.add_argument("--force", action="store_true", help="Force recreation of database tables.")
    args = parser.parse_args()

    success = init_db(force_recreate=args.force)
    if success:
        print("数据库初始化成功")
    else:
        print("数据库初始化失败，请检查日志")

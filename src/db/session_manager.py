# src/db/session_manager.py
from contextlib import contextmanager

from loguru import logger
from sqlalchemy.orm import Session

# 假设连接管理在此，如果实际路径不同，请告知
from src.db.connection_manager import get_session_factory


@contextmanager
def session_scope():
    """提供一个事务性的数据库会话作用域。

    用法:
        with session_scope() as session:
            # 在这里执行数据库操作
            repo.create(session, data)
    """
    session = get_session_factory()()
    logger.debug("数据库会话开始")
    try:
        yield session
        session.commit()
        logger.debug("数据库会话提交成功")
    except Exception as e:
        logger.error(f"数据库会话异常，执行回滚: {e}", exc_info=True)
        session.rollback()
        raise  # 重新抛出异常，以便上层处理
    finally:
        session.close()
        logger.debug("数据库会话关闭")

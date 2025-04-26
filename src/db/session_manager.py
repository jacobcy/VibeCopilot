# src/db/session_manager.py
import logging  # Import standard logging
from contextlib import contextmanager

from sqlalchemy.orm import Session

# Define standard logger
logger = logging.getLogger(__name__)

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
    # logger.debug(f"数据库会话开始. Type: {type(session)}, Value: {session}")
    # session_bind = getattr(session, 'bind', 'Attribute Missing')
    # logger.debug(f"Session bind state on creation. Bind Type: {type(session_bind)}, Bind Value: {session_bind}")
    # <<< Remove debugging prints >>>
    # print(f"--- DEBUG [session_manager] BEFORE YIELD --- Session Type: {type(session)}")
    # try:
    #     bind_val = getattr(session, 'bind', 'BIND_ATTR_MISSING')
    #     print(f"--- DEBUG [session_manager] BEFORE YIELD --- Session Bind Type: {type(bind_val)}, Value: {bind_val}")
    # except Exception as e:
    #     print(f"--- ERROR [session_manager] BEFORE YIELD --- Getting bind failed: {e}")
    # <<< Optionally add a standard logger.debug call here if desired >>>
    logger.debug(f"Session scope started. Session: {session}")  # Example standard log

    try:
        # If this check is still deemed valuable, keep it, otherwise remove.
        # It wasn't hit during our error, so maybe less critical now.
        if not isinstance(session, Session):
            logger.error(f"session_scope: get_session_factory() 返回的不是 Session 对象! Type: {type(session)}")
            # Consider raising an exception here if this is truly unexpected
        yield session
        session.commit()
        logger.debug("数据库会话提交成功")
    except Exception as e:
        # Remove exc_info=True to avoid printing traceback here
        # Rely on the caller to handle logging details if needed
        logger.error(f"数据库会话异常，执行回滚: {e}")
        session.rollback()
        raise  # 重新抛出异常，以便上层处理
    finally:
        session.close()
        logger.debug("数据库会话关闭")

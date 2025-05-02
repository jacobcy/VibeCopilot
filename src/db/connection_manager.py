"""
数据库连接管理器模块

提供全局单例的数据库连接管理，确保数据库只初始化一次
"""

import logging
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

# 引入 get_config
from src.core.config.manager import get_config

# Removed import of setup_logger
from src.models.db.base import Base

logger = logging.getLogger(__name__)


class DBConnectionManager:
    """数据库连接管理器 (单例模式)"""

    _instance = None
    _initialized = False
    _tables_ensured = False  # 新增变量，跟踪表是否已确保存在
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 初始化移到 get_engine 或 get_session 调用时，确保 config 已加载
        pass

    def _initialize_if_needed(self):
        """如果未初始化，则初始化数据库连接"""
        # logger.warning("DBConnectionManager: Forcing re-initialization check for debugging...") # Removed force
        # self._initialized = False # Removed force

        if not self._initialized:
            # <<< Log entry >>>
            logger.debug("Entering DBConnectionManager._initialize_if_needed")
            import traceback

            # 获取调用栈信息
            # caller_info = "".join(traceback.format_stack()[:-1]) # Commented out, potentially verbose
            logger.debug("DBConnectionManager._initialize_if_needed 被调用")

            try:
                # <<< Log before config load >>>
                # print("DEBUG [connection_manager]: Attempting to call get_config()") # Using print again
                logger.debug("Attempting to call get_config()")  # Reverting to logger
                config_manager = get_config()
                # print(f"DEBUG [connection_manager]: get_config() returned. Type: {type(config_manager)}") # Using print again
                logger.debug(f"get_config() returned. Type: {type(config_manager)}")  # Reverting to logger

                # <<< Log before getting URL >>>
                # print("DEBUG [connection_manager]: Attempting to get database.url") # Using print again
                logger.debug("Attempting to get database.url")  # Reverting to logger
                database_url = config_manager.get("database.url")
                # print(f"DEBUG [connection_manager]: database.url retrieved. Type: {type(database_url)}, Value: {database_url}") # Using print again
                logger.debug(f"Database URL retrieved. Type: {type(database_url)}, Value: {database_url}")  # Reverting to logger

                if not database_url:
                    # print("ERROR [connection_manager]: database.url is missing or empty!") # Using print again
                    logger.error("Database URL is missing or empty!")  # Reverting to logger
                    raise ValueError("Database URL not found in configuration.")

                # 检查是否是 SQLite 路径并确保目录存在
                if database_url.startswith("sqlite:///"):
                    db_path = database_url[len("sqlite:///") :]
                    # 确保是绝对路径 (ConfigManager 应该处理了，但 double check)
                    if not os.path.isabs(db_path):
                        project_root = config_manager.get("paths.project_root", os.getcwd())
                        db_path = os.path.abspath(os.path.join(project_root, db_path))
                        database_url = f"sqlite:///{db_path}"  # 更新为绝对路径URL

                    db_dir = os.path.dirname(db_path)
                    if db_dir:
                        os.makedirs(db_dir, exist_ok=True)

                # 从配置获取连接池配置 (如果需要，可以在 defaults.py 中定义)
                pool_size = config_manager.get("database.pool_size", 20)
                max_overflow = config_manager.get("database.max_overflow", 30)
                pool_timeout = config_manager.get("database.pool_timeout", 60)
                pool_recycle = config_manager.get("database.pool_recycle", 3600)
                db_debug = config_manager.get("database.debug", False)

                # 创建数据库引擎
                # print("DEBUG [connection_manager]: Attempting to create engine...") # Using print again
                logger.debug("Attempting to create engine...")  # Reverting to logger
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
                    poolclass=QueuePool,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle,
                    echo=db_debug,  # 从配置控制是否打印SQL
                )
                # <<< Log engine state >>>
                # print(f"DEBUG [connection_manager]: Engine created. Type: {type(self._engine)}, Value: {self._engine}") # Using print again
                logger.debug(f"Engine created. Type: {type(self._engine)}, Value: {self._engine}")  # Reverting to logger

                # 创建会话工厂
                # print("DEBUG [connection_manager]: Attempting to create session factory...") # Using print again
                logger.debug("Attempting to create session factory...")  # Reverting to logger
                self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
                # <<< Log session factory bind state >>>
                factory_bind = self._session_factory.kw.get("bind")
                # print(f"DEBUG [connection_manager]: Session factory created. Bind Type: {type(factory_bind)}, Bind Value: {factory_bind}") # Using print again
                logger.debug(f"Session factory created. Bind Type: {type(factory_bind)}, Bind Value: {factory_bind}")  # Reverting to logger

                self._initialized = True
                # print(f"INFO [connection_manager]: Initialization complete. DB: {database_url}") # Using print again
                logger.info(f"数据库连接管理器初始化完成: {database_url}")  # Reverting to logger
                # print(f"DEBUG [connection_manager]: Pool config - Size: {pool_size}, Overflow: {max_overflow}, Timeout: {pool_timeout}, Recycle: {pool_recycle}") # Using print again
                logger.debug(f"连接池配置 - 大小: {pool_size}, 溢出: {max_overflow}, 超时: {pool_timeout}s, 回收: {pool_recycle}s")  # Reverting to logger
            except Exception as e:
                # print(f"ERROR [connection_manager] in _initialize_if_needed: {e}") # Using print again
                logger.error(f"初始化数据库连接管理器失败: {e}", exc_info=True)  # Reverting to logger
                # print(traceback.format_exc()) # Using print again - covered by exc_info=True
                raise

    # 移除 _get_db_path 方法，因为 URL 直接从 config 获取
    # def _get_db_path(self) -> str: ...

    def get_engine(self) -> Engine:
        """获取数据库引擎"""
        self._initialize_if_needed()
        if self._engine is None:
            raise RuntimeError("Database engine is not initialized.")
        return self._engine

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        self._initialize_if_needed()
        if self._session_factory is None:
            raise RuntimeError("Session factory is not initialized.")
        return self._session_factory()

    def get_session_factory(self):
        """获取会话工厂"""
        self._initialize_if_needed()
        if self._session_factory is None:
            raise RuntimeError("Session factory is not initialized.")
        return self._session_factory

    def ensure_tables_exist(self, force_recreate=False):
        """
        确保所有表存在

        Args:
            force_recreate: 是否强制重新创建表
        """
        # 检查环境变量中的force_recreate设置 (保留此逻辑)
        env_force = os.getenv("FORCE_RECREATE", "").lower() == "true"
        force_recreate = force_recreate or env_force

        logger.debug(f"ensure_tables_exist 被调用 (force_recreate={force_recreate})")

        # 确保引擎已初始化
        engine = self.get_engine()

        if force_recreate:
            self._tables_ensured = False
            logger.warning("强制重新创建所有数据库表")
            Base.metadata.drop_all(engine)

        if not self._tables_ensured:
            try:
                Base.metadata.create_all(engine)
                logger.info("数据库表创建/验证完成")
                self._tables_ensured = True
            except Exception as e:
                logger.error(f"创建数据库表失败: {e}", exc_info=True)
                # 抛出异常或返回False，取决于调用者如何处理
                raise RuntimeError(f"Failed to create database tables: {e}")
        else:
            logger.debug("表已经确保存在，跳过表创建过程")

        return True


# 提供全局访问点
connection_manager = DBConnectionManager()


def get_engine() -> Engine:
    """获取全局数据库引擎"""
    return connection_manager.get_engine()


def get_session() -> Session:
    """获取新的数据库会话"""
    return connection_manager.get_session()


def get_session_factory():
    """获取会话工厂"""
    return connection_manager.get_session_factory()


def ensure_tables_exist(force_recreate=False) -> bool:
    """确保所有表存在"""
    return connection_manager.ensure_tables_exist(force_recreate)


def get_db_path() -> str:
    """获取数据库文件路径

    Returns:
        str: 数据库文件的绝对路径

    Raises:
        ValueError: 如果数据库URL不是SQLite或无法解析
    """
    config_manager = get_config()
    database_url = config_manager.get("database.url")

    if not database_url:
        raise ValueError("Database URL not found in configuration.")

    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite databases are supported for this operation.")

    db_path = database_url[len("sqlite:///") :]

    # 确保是绝对路径
    if not os.path.isabs(db_path):
        project_root = config_manager.get("paths.project_root", os.getcwd())
        db_path = os.path.abspath(os.path.join(project_root, db_path))

    return db_path

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

from src.core.logger import setup_logger
from src.models.db.base import Base

logger = setup_logger(__name__)


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
        if not self._initialized:
            self._initialize()

    def _initialize(self):
        """初始化数据库连接"""
        import traceback

        # 获取调用栈信息
        caller_info = "".join(traceback.format_stack()[:-1])
        logger.debug(f"DBConnectionManager._initialize 被调用")
        logger.debug(f"调用栈信息: \n{caller_info}")

        try:
            db_path = self._get_db_path()

            # 确保数据库目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            # 构建数据库URL
            database_url = f"sqlite:///{db_path}"

            # 创建数据库引擎
            self._engine = create_engine(database_url, connect_args={"check_same_thread": False})

            # 创建会话工厂
            self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

            # 记录初始化
            self._initialized = True
            logger.debug(f"数据库连接管理器初始化完成: {database_url}")
        except Exception as e:
            logger.error(f"初始化数据库连接管理器失败: {e}")
            raise

    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        # 获取DATABASE_URL
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
        logger.debug(f"使用默认数据库路径: {default_path}")
        return default_path

    def get_engine(self) -> Engine:
        """获取数据库引擎"""
        if not self._initialized:
            self._initialize()
        return self._engine

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        if not self._initialized:
            self._initialize()
        return self._session_factory()

    def get_session_factory(self):
        """获取会话工厂"""
        if not self._initialized:
            self._initialize()
        return self._session_factory

    def ensure_tables_exist(self, force_recreate=False):
        """确保所有表存在

        Args:
            force_recreate: 是否强制重新创建表
        """
        # 检查环境变量中的force_recreate设置
        env_force = os.getenv("FORCE_RECREATE", "").lower() == "true"
        force_recreate = force_recreate or env_force

        logger.debug(f"ensure_tables_exist 被调用 (force_recreate={force_recreate})")

        if not self._initialized:
            logger.debug("数据库连接未初始化，进行初始化...")
            self._initialize()

        # 如果强制重建，重置_tables_ensured标记
        if force_recreate:
            self._tables_ensured = False
            logger.debug("强制重新创建所有表")
            Base.metadata.drop_all(self._engine)

        # 如果表未确保存在，则创建
        if not self._tables_ensured:
            # 创建所有表 (如果不存在)
            Base.metadata.create_all(self._engine)
            logger.debug("数据库表创建/验证完成")
            # 标记表已经确保存在
            self._tables_ensured = True
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

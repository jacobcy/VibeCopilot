"""
工作流会话管理器基础类

提供FlowSessionManager的基础功能，包括初始化和仓库访问。
"""

import json
import logging  # Import logging
import os
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

# Import get_config
from src.core.config import get_config

# Define module-level logger
logger = logging.getLogger(__name__)

# 将导入移动到方法内部以解决循环导入 - 不再需要，直接从 repositories 导入
# from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.task_repository import TaskRepository  # Import TaskRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository


class FlowSessionManagerBase:
    """工作流会话管理器基础类，处理初始化和仓库访问"""

    # 存储当前会话ID的文件路径 - 使用配置
    # CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "current_session.json") # Old hardcoded path
    # Path will be constructed in __init__ using config

    def __init__(self, session: Session, logger_param=None):
        """初始化

        Args:
            session: SQLAlchemy会话对象
            logger_param: 可选的外部日志记录器 (renamed to avoid conflict)
        """
        # Get config and construct path
        config = get_config()
        data_dir = config.get("paths.data_dir")
        if not data_dir:
            raise ValueError("Configuration key 'paths.data_dir' is not set or invalid.")
        self.CURRENT_SESSION_FILE = os.path.join(data_dir, "status", "current_session.json")

        # <<< Use module-level logger here >>>
        logger.debug(f"FlowSessionManagerBase.__init__: Received session type={type(session)}")

        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository()
        self.session_repo = FlowSessionRepository()
        self.stage_repo = StageInstanceRepository()
        self.task_repo = TaskRepository()  # Add TaskRepository instance
        # Assign the passed logger (or None) to the instance variable
        self._logger = logger_param

        # <<< This block now correctly uses the PASSED logger (if any) >>>
        if self._logger:
            # Log again using the provided logger if needed, or remove redundancy
            self._logger.debug(f"Using provided logger. Session type: {type(session)}")
            self._logger.debug(f"Instance session type after assignment: {type(self.session)}")

        # 确保存储当前会话ID的目录存在
        os.makedirs(os.path.dirname(self.CURRENT_SESSION_FILE), exist_ok=True)

    def set_logger(self, logger):
        """设置日志记录器

        Args:
            logger: 日志记录器实例
        """
        self._logger = logger

    def _log(self, method: str, *args, **kwargs):
        """内部日志记录方法

        Args:
            method: 要调用的日志方法名
            args: 位置参数
            kwargs: 关键字参数
        """
        if self._logger and hasattr(self._logger, method):
            getattr(self._logger, method)(*args, **kwargs)

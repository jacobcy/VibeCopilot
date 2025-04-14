"""
工作流会话管理器基础类

提供FlowSessionManager的基础功能，包括初始化和仓库访问。
"""

import json
import os
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository


class FlowSessionManagerBase:
    """工作流会话管理器基础类，处理初始化和仓库访问"""

    # 存储当前会话ID的文件路径
    CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "current_session.json")

    def __init__(self, session: Session, logger=None):
        """初始化

        Args:
            session: SQLAlchemy会话对象
            logger: 可选的日志记录器
        """
        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository(session)
        self.session_repo = FlowSessionRepository(session)
        self.stage_repo = StageInstanceRepository(session)
        self._logger = logger

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

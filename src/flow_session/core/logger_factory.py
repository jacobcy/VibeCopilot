#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录器工厂模块

提供FlowSessionLogger的实例化和管理功能
"""

from typing import Optional

from src.flow_session.core.logger import FlowSessionLogger


class LoggerFactory:
    """日志记录器工厂类"""

    _instance = None
    _loggers = {}

    @classmethod
    def get_instance(cls) -> "LoggerFactory":
        """获取工厂单例

        Returns:
            LoggerFactory实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_logger(self, session_id: str) -> FlowSessionLogger:
        """获取或创建日志记录器

        Args:
            session_id: 会话ID

        Returns:
            FlowSessionLogger实例
        """
        if session_id not in self._loggers:
            self._loggers[session_id] = FlowSessionLogger(session_id)
        return self._loggers[session_id]

    def remove_logger(self, session_id: str) -> None:
        """移除日志记录器

        Args:
            session_id: 会话ID
        """
        if session_id in self._loggers:
            del self._loggers[session_id]

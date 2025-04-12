#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流会话服务组件

提供工作流会话的管理功能，是flow_session模块的服务接口。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionService:
    """工作流会话服务类，负责会话的CRUD和生命周期管理"""

    def __init__(self, session_manager, verbose=False):
        """初始化会话服务

        Args:
            session_manager: 会话管理器实例
            verbose: 是否显示详细日志
        """
        self.session_manager = session_manager
        self.verbose = verbose

    def create_session(self, workflow_id: str, name: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        创建工作流会话

        Args:
            workflow_id: 工作流定义ID
            name: 会话名称(可选)
            task_id: 关联的任务ID(可选)，表明会话的目的是完成该任务

        Returns:
            创建的会话数据
        """
        if self.verbose:
            logger.info(f"创建工作流会话: 工作流={workflow_id}, 名称={name}, 任务ID={task_id}")

        session = self.session_manager.create_session(workflow_id, name, task_id)
        return session.to_dict() if hasattr(session, "to_dict") else {"id": session.id, "name": session.name, "task_id": session.task_id}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话详情

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典或None
        """
        if self.verbose:
            logger.debug(f"获取会话详情: {session_id}")

        session = self.session_manager.get_session(session_id)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def list_sessions(self, status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出会话

        Args:
            status: 会话状态过滤
            workflow_id: 工作流ID过滤

        Returns:
            会话数据列表
        """
        if self.verbose:
            logger.debug(f"列出会话 (状态={status}, 工作流ID={workflow_id})")

        sessions = self.session_manager.list_sessions(status, workflow_id)
        return [s.to_dict() if hasattr(s, "to_dict") else {"id": s.id, "name": s.name} for s in sessions]

    def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新会话数据

        Args:
            session_id: 会话ID
            data: 更新数据

        Returns:
            更新后的会话数据或None
        """
        if self.verbose:
            logger.debug(f"更新会话数据: {session_id}")

        session = self.session_manager.update_session(session_id, data)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        if self.verbose:
            logger.info(f"删除会话: {session_id}")

        return self.session_manager.delete_session(session_id)

    def pause_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        暂停会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        if self.verbose:
            logger.info(f"暂停会话: {session_id}")

        session = self.session_manager.pause_session(session_id)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        if self.verbose:
            logger.info(f"恢复会话: {session_id}")

        session = self.session_manager.resume_session(session_id)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def complete_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        完成会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        if self.verbose:
            logger.info(f"完成会话: {session_id}")

        session = self.session_manager.complete_session(session_id)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        结束会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        if self.verbose:
            logger.info(f"结束会话: {session_id}")

        session = self.session_manager.close_session(session_id)
        return session.to_dict() if session and hasattr(session, "to_dict") else None

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        获取当前活跃会话

        Returns:
            当前会话数据字典或None
        """
        if self.verbose:
            logger.debug("正在获取当前活跃会话...")

        session = self.session_manager.get_current_session()

        if self.verbose and session:
            logger.debug(f"获取到当前活跃会话: {session.id}")
        elif self.verbose:
            logger.debug("没有活跃的会话")

        return session.to_dict() if session and hasattr(session, "to_dict") else None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow会话单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.session.operations import get_db_session
from src.models.db.flow_session import FlowSession


class TestFlowSession(unittest.TestCase):
    """测试Flow会话管理"""

    def setUp(self):
        """测试前准备"""
        self.mock_session = MagicMock(spec=Session)
        self.manager = FlowSessionManager(self.mock_session)

    def test_get_db_session(self):
        """测试获取数据库会话"""
        # 执行测试
        session = get_db_session()

        # 验证结果
        self.assertIsInstance(session, Session)

    def test_flow_session_manager(self):
        """测试Flow会话管理器"""
        # 设置模拟数据
        mock_flow_session = MagicMock(spec=FlowSession)
        mock_flow_session.id = "test-session"
        mock_flow_session.workflow_id = "test-flow"
        mock_flow_session.status = "ACTIVE"
        mock_flow_session.current_stage_id = "stage1"

        self.manager.get_session = MagicMock(return_value=mock_flow_session)

        # 测试获取会话
        session = self.manager.get_session("test-session")
        self.assertEqual(session.id, "test-session")
        self.assertEqual(session.workflow_id, "test-flow")
        self.assertEqual(session.status, "ACTIVE")
        self.assertEqual(session.current_stage_id, "stage1")

        self.manager.get_session.assert_called_once_with("test-session")

    def test_create_flow_session(self):
        """测试创建Flow会话"""
        # 设置模拟数据
        mock_session = {"id": "new-session", "workflow_id": "test-flow", "status": "ACTIVE", "current_stage_id": None}
        self.manager.create_session = MagicMock(return_value=mock_session)

        # 测试创建会话
        session = self.manager.create_session("test-flow")
        self.assertEqual(session["id"], "new-session")
        self.assertEqual(session["workflow_id"], "test-flow")
        self.assertEqual(session["status"], "ACTIVE")
        self.assertIsNone(session["current_stage_id"])

        self.manager.create_session.assert_called_once_with("test-flow")

    def test_update_flow_session(self):
        """测试更新Flow会话"""
        # 设置模拟数据
        mock_session = {"id": "test-session", "workflow_id": "test-flow", "status": "COMPLETED", "current_stage_id": "stage2"}
        self.manager.update_session = MagicMock(return_value=mock_session)

        # 测试更新会话
        update_data = {"status": "COMPLETED", "current_stage_id": "stage2"}
        session = self.manager.update_session("test-session", update_data)
        self.assertEqual(session["id"], "test-session")
        self.assertEqual(session["workflow_id"], "test-flow")
        self.assertEqual(session["status"], "COMPLETED")
        self.assertEqual(session["current_stage_id"], "stage2")

        self.manager.update_session.assert_called_once_with("test-session", update_data)

    def test_delete_flow_session(self):
        """测试删除Flow会话"""
        # 设置模拟
        self.manager.delete_session = MagicMock(return_value=True)

        # 测试删除会话
        result = self.manager.delete_session("test-session")
        self.assertTrue(result)

        self.manager.delete_session.assert_called_once_with("test-session")


if __name__ == "__main__":
    unittest.main()

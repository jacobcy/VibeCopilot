#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程会话管理器测试
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.flow_session.manager import FlowSessionManager
from src.flow_session.models import FlowSession


@pytest.fixture
def session_data():
    return {
        "id": "test-session-1",
        "name": "测试会话",
        "workflow_id": "dev-workflow",
        "status": "ACTIVE",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


class TestFlowSession:
    """测试Flow会话管理"""

    def setup_method(self):
        """测试前准备"""
        self.mock_session = MagicMock()
        self.manager = FlowSessionManager(self.mock_session)

    def test_flow_session_manager(self, mocker):
        """测试Flow会话管理器"""
        # 设置模拟数据
        mock_flow_session = MagicMock()
        mock_flow_session.id = "test-session"
        mock_flow_session.workflow_id = "test-flow"
        mock_flow_session.status = "ACTIVE"
        mock_flow_session.current_stage_id = "stage1"

        # 模拟get_session方法
        mocker.patch.object(self.manager, "get_session", return_value=mock_flow_session)

        # 测试获取会话
        session = self.manager.get_session("test-session")
        assert session.id == "test-session"
        assert session.workflow_id == "test-flow"
        assert session.status == "ACTIVE"
        assert session.current_stage_id == "stage1"

        self.manager.get_session.assert_called_once_with("test-session")

    def test_create_flow_session(self, mocker):
        """测试创建Flow会话"""
        # 设置模拟数据
        mock_session = {"id": "new-session", "workflow_id": "test-flow", "status": "ACTIVE", "current_stage_id": None}

        # 模拟create_session方法
        mocker.patch.object(self.manager, "create_session", return_value=mock_session)

        # 测试创建会话
        session = self.manager.create_session("test-flow")
        assert session["id"] == "new-session"
        assert session["workflow_id"] == "test-flow"
        assert session["status"] == "ACTIVE"
        assert session["current_stage_id"] is None

        self.manager.create_session.assert_called_once_with("test-flow")

    def test_update_flow_session(self, mocker):
        """测试更新Flow会话"""
        # 设置模拟数据
        mock_session = {"id": "test-session", "workflow_id": "test-flow", "status": "COMPLETED", "current_stage_id": "stage2"}

        # 模拟update_session方法
        mocker.patch.object(self.manager, "update_session", return_value=mock_session)

        # 测试更新会话
        update_data = {"status": "COMPLETED", "current_stage_id": "stage2"}
        session = self.manager.update_session("test-session", update_data)
        assert session["id"] == "test-session"
        assert session["workflow_id"] == "test-flow"
        assert session["status"] == "COMPLETED"
        assert session["current_stage_id"] == "stage2"

        self.manager.update_session.assert_called_once_with("test-session", update_data)

    def test_delete_flow_session(self, mocker):
        """测试删除Flow会话"""
        # 模拟delete_session方法
        mocker.patch.object(self.manager, "delete_session", return_value=True)

        # 测试删除会话
        result = self.manager.delete_session("test-session")
        assert result is True

        self.manager.delete_session.assert_called_once_with("test-session")


if __name__ == "__main__":
    pytest.main()

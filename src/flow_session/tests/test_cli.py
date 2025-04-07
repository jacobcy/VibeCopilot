#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow Session CLI测试模块
测试命令行界面功能
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from src.flow_session.cli import (
    abort_session,
    create_session,
    delete_session,
    list_sessions,
    pause_session,
    resume_session,
    show_session,
)


class TestFlowSessionCLI(unittest.TestCase):
    """测试Flow Session CLI功能"""

    @patch("src.flow_session.cli.get_db_session")
    @patch("src.flow_session.cli.FlowSessionManager")
    def test_list_sessions(self, mock_manager_class, mock_get_db_session):
        """测试list_sessions函数"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # 第一种情况：没有会话
        mock_manager.list_sessions.return_value = []

        # 捕获标准输出
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            list_sessions()

        # 验证输出
        self.assertIn("未找到工作流会话", captured_output.getvalue())

        # 重置
        captured_output = io.StringIO()

        # 第二种情况：有会话
        mock_session = MagicMock()
        mock_session.id = "test-id"
        mock_session.workflow_id = "test-workflow"
        mock_session.name = "Test Session"
        mock_session.status = "ACTIVE"
        mock_session.current_stage_id = "test-stage"
        mock_session.created_at.strftime.return_value = "2023-01-01 12:00"

        mock_manager.list_sessions.return_value = [mock_session]

        with redirect_stdout(captured_output):
            list_sessions()

        # 验证输出
        output = captured_output.getvalue()
        self.assertIn("工作流会话", output)
        self.assertIn("test-id", output)
        self.assertIn("test-workflow", output)
        self.assertIn("Test Session", output)
        self.assertIn("ACTIVE", output)

    @patch("src.flow_session.cli.get_db_session")
    @patch("src.flow_session.cli.FlowSessionManager")
    @patch("src.flow_session.cli.StageInstanceManager")
    def test_show_session(self, mock_stage_manager_class, mock_manager_class, mock_get_db_session):
        """测试show_session函数"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # 第一种情况：找不到会话
        mock_manager.get_session.return_value = None

        # 捕获标准输出
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            show_session("non-existent-id")

        # 验证输出
        self.assertIn("找不到ID为", captured_output.getvalue())

        # 重置
        captured_output = io.StringIO()

        # 第二种情况：找到会话
        mock_flow_session = MagicMock()
        mock_flow_session.id = "test-id"
        mock_flow_session.name = "Test Session"
        mock_flow_session.workflow_id = "test-workflow"
        mock_flow_session.status = "ACTIVE"
        mock_flow_session.created_at.strftime.return_value = "2023-01-01 12:00"
        mock_flow_session.updated_at.strftime.return_value = "2023-01-01 12:30"

        mock_manager.get_session.return_value = mock_flow_session

        # 模拟进度信息
        mock_manager.get_session_progress.return_value = {
            "completed_stages": [{"name": "Stage 1", "completed_at": "2023-01-01T12:15:00"}],
            "current_stage": {"name": "Stage 2", "id": "stage-2"},
            "pending_stages": [{"name": "Stage 3"}],
        }

        with redirect_stdout(captured_output):
            show_session("test-id")

        # 验证输出
        output = captured_output.getvalue()
        self.assertIn("工作流会话: test-id", output)
        self.assertIn("Test Session", output)
        self.assertIn("工作流: test-workflow", output)
        self.assertIn("状态: ACTIVE", output)
        self.assertIn("Stage 1 - 已完成", output)
        self.assertIn("Stage 2 - 进行中", output)
        self.assertIn("Stage 3 - 待进行", output)


if __name__ == "__main__":
    unittest.main()

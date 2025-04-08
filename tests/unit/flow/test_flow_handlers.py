#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow命令处理器单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from src.cli.commands.flow.handlers.create_handler import handle_create_subcommand
from src.cli.commands.flow.handlers.export_handler import handle_export_subcommand
from src.cli.commands.flow.handlers.import_handler import handle_import_subcommand
from src.cli.commands.flow.handlers.list_handler import handle_list_subcommand
from src.cli.commands.flow.handlers.next_handler import handle_next_subcommand
from src.cli.commands.flow.handlers.run_handler import handle_run_subcommand
from src.cli.commands.flow.handlers.show_handler import handle_show_subcommand
from src.cli.commands.flow.handlers.update_handler import handle_update_subcommand


class TestFlowHandlers(unittest.TestCase):
    """测试Flow命令处理器"""

    def test_list_handler(self):
        """测试list处理器"""
        args = {"workflow_type": None, "verbose": False}

        result = handle_list_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("code", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("meta", result)

    @patch("src.workflow.get_workflow")
    def test_export_handler(self, mock_get_workflow):
        """测试export处理器"""
        # 设置模拟工作流数据
        mock_workflow = {"id": "test-flow", "name": "Test Flow", "stages": []}
        mock_get_workflow.return_value = mock_workflow

        args = {"workflow_id": "test-flow", "format": "json", "output": None}

        result = handle_export_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("code", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("meta", result)

    def test_import_handler(self):
        """测试import处理器"""
        args = {"file_path": "test-flow.json", "overwrite": False}

        result = handle_import_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["code"], 501)  # 未实现状态码

    def test_next_handler(self):
        """测试next处理器"""
        args = {"session_id": "test-session", "current": "stage1"}

        result = handle_next_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["code"], 501)  # 未实现状态码

    def test_update_handler(self):
        """测试update处理器"""
        args = {"id": "test-flow", "name": "Updated Flow", "description": "Updated description"}

        result = handle_update_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["code"], 501)  # 未实现状态码

    @patch("src.workflow.get_workflow")
    def test_show_handler(self, mock_get_workflow):
        """测试show处理器"""
        # 设置模拟工作流数据
        mock_workflow = {"id": "test-flow", "name": "Test Flow", "stages": []}
        mock_get_workflow.return_value = mock_workflow

        args = {"workflow_id": "test-flow", "format": "json"}

        result = handle_show_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("code", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("meta", result)

    @patch("src.workflow.get_workflow")
    def test_run_handler(self, mock_get_workflow):
        """测试run处理器"""
        # 设置模拟工作流数据
        mock_workflow = {"id": "test-flow", "name": "Test Flow", "stages": [{"id": "stage1", "name": "Stage 1"}]}
        mock_get_workflow.return_value = mock_workflow

        args = {"workflow_id": "test-flow", "stage": None}

        result = handle_run_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("code", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("meta", result)

    def test_create_handler(self):
        """测试create处理器"""
        args = {"rule_path": ".cursor/rules/flow-rules/test-flow.mdc", "template": None, "variables": None, "output": None, "verbose": False}

        result = handle_create_subcommand(args)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("code", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("meta", result)


if __name__ == "__main__":
    unittest.main()

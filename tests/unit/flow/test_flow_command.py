#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow命令单元测试
"""

import argparse
import unittest
from unittest.mock import MagicMock, patch

from src.cli.commands.flow.flow_command import FlowCommand


class TestFlowCommand(unittest.TestCase):
    """测试Flow命令类"""

    def setUp(self):
        """测试前准备"""
        self.command = FlowCommand()

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.command.name, "flow")
        self.assertIsNotNone(self.command.description)

    def test_configure_parser(self):
        """测试命令行解析器配置"""
        parser = argparse.ArgumentParser()
        self.command.configure_parser(parser)

        # 验证子命令解析器
        subparsers = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
        self.assertEqual(len(subparsers), 1)

        # 验证所有必需的子命令都已注册
        subparser = subparsers[0]
        expected_subcommands = {"list", "create", "update", "show", "context", "next", "visualize", "export", "import", "run", "session"}
        self.assertEqual(set(subparser.choices.keys()), expected_subcommands)

    def test_execute_without_subcommand(self):
        """测试没有子命令时的执行"""
        args = argparse.Namespace()
        result = self.command.execute_with_args(args)
        self.assertEqual(result, 1)  # 应该返回错误码1

    @patch("src.cli.commands.flow.handlers.list_handler.handle_list_subcommand")
    def test_execute_list_subcommand(self, mock_handler):
        """测试list子命令执行"""
        # 设置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功列出工作流", "data": [], "meta": {"command": "flow list"}}

        # 执行命令
        args = argparse.Namespace(subcommand="list", workflow_type=None, verbose=False)
        result = self.command.execute_with_args(args)

        # 验证结果
        self.assertEqual(result, 0)

    @patch("src.cli.commands.flow.handlers.create_handler.handle_create_subcommand")
    def test_execute_create_subcommand(self, mock_handler):
        """测试create子命令执行"""
        # 设置模拟返回值
        mock_handler.return_value = {
            "status": "error",
            "code": 404,
            "message": "规则文件不存在: .cursor/rules/flow-rules/test-flow.mdc",
            "data": None,
            "meta": {"command": "flow create"},
        }

        # 执行命令
        args = argparse.Namespace(
            subcommand="create", rule_path=".cursor/rules/flow-rules/test-flow.mdc", template=None, variables=None, output=None, verbose=False
        )
        result = self.command.execute_with_args(args)

        # 验证结果
        self.assertEqual(result, 404)

    @patch("src.cli.commands.flow.handlers.run_handler.handle_run_subcommand")
    def test_execute_run_subcommand(self, mock_handler):
        """测试run子命令执行"""
        # 设置模拟返回值
        mock_handler.return_value = {
            "status": "error",
            "code": 400,
            "message": "必须提供目标阶段ID (stage)",
            "data": None,
            "meta": {"command": "flow run"},
        }

        # 执行命令
        args = argparse.Namespace(subcommand="run", workflow_id="test-flow", stage=None, verbose=False)
        result = self.command.execute_with_args(args)

        # 验证结果
        self.assertEqual(result, 400)

    def test_execute_invalid_subcommand(self):
        """测试无效子命令执行"""
        args = argparse.Namespace(subcommand="invalid")
        result = self.command.execute_with_args(args)
        self.assertEqual(result, 1)  # 应该返回错误码1

    @patch("src.cli.commands.flow.handlers.list_handler.handle_list_subcommand")
    def test_execute_handler_error(self, mock_handler):
        """测试处理器错误情况"""
        # 设置模拟返回值
        mock_handler.return_value = {
            "status": "success",
            "code": 0,
            "message": "没有找到工作流定义",
            "data": {"workflows": []},
            "meta": {"command": "flow list"},
        }

        args = argparse.Namespace(subcommand="list", workflow_type=None, verbose=False)
        result = self.command.execute_with_args(args)
        self.assertEqual(result, 0)  # 空列表应返回成功状态码0


if __name__ == "__main__":
    unittest.main()

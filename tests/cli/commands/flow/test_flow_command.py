#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流命令

验证工作流命令的基本功能
"""

import argparse
from unittest import mock

import pytest

from src.cli.commands.flow.flow_command import FlowCommand


class TestFlowCommand:
    """工作流命令测试类"""

    def test_init(self):
        """测试初始化"""
        cmd = FlowCommand()
        assert cmd.name == "flow"
        assert cmd.description is not None

    def test_configure_parser(self):
        """测试配置解析器"""
        cmd = FlowCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        # 验证子命令解析器已经配置
        assert parser._subparsers is not None

    @mock.patch("src.cli.commands.flow.flow_command.handle_list_subcommand")
    def test_execute_list(self, mock_handler):
        """测试执行列表子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功列出工作流", "data": []}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="list", workflow_type=None, verbose=False, _agent_mode=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_create_subcommand")
    def test_execute_create(self, mock_handler):
        """测试执行创建子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功创建工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="create", rule_path="path/to/rule.md", template=None, variables=None, output=None, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_show_subcommand")
    def test_execute_show(self, mock_handler):
        """测试执行查看子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功查看工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="show", workflow_id="test-id", format="text", diagram=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_export_subcommand")
    def test_execute_export(self, mock_handler):
        """测试执行导出子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功导出工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="export", workflow_id="test-id", format="json", output=None, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_run_subcommand")
    def test_execute_run(self, mock_handler):
        """测试执行运行子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功运行工作流阶段", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="run", workflow_id="test-id", stage="test-stage", name=None, completed=None, session=None, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_visualize_subcommand")
    def test_execute_visualize(self, mock_handler):
        """测试执行可视化子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功可视化工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="visualize", id="test-id", session=False, format="mermaid", output=None, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_context_subcommand")
    def test_execute_context(self, mock_handler):
        """测试执行上下文子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功获取工作流上下文", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(
            subcommand="context", workflow_id="test-id", stage_id="test-stage", session=None, completed=None, format="text", verbose=False
        )
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_update_subcommand")
    def test_execute_update(self, mock_handler):
        """测试执行更新子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功更新工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="update", id="test-id", name="New Name", description=None, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_import_subcommand")
    def test_execute_import(self, mock_handler):
        """测试执行导入子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功导入工作流", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="import", file_path="path/to/workflow.json", overwrite=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_next_subcommand")
    def test_execute_next(self, mock_handler):
        """测试执行下一步子命令"""
        # 配置模拟返回值
        mock_handler.return_value = {"status": "success", "code": 0, "message": "成功获取下一步建议", "data": {}}

        # 创建命令并执行
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="next", session_id="test-session", current=None, format="text", verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    @mock.patch("src.cli.commands.flow.flow_command.handle_session_command")
    def test_execute_session(self, mock_handler):
        """测试执行会话子命令"""
        # 配置模拟返回值
        mock_handler.return_value = (True, "成功管理工作流会话", {})

        # 创建命令并执行
        cmd = FlowCommand()
        # 会话子命令有多种可能的参数，这里仅测试基本情况
        args = argparse.Namespace(subcommand="session", session_subcommand="list", verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once()

    def test_execute_unknown_subcommand(self):
        """测试执行未知子命令"""
        cmd = FlowCommand()
        args = argparse.Namespace(subcommand="unknown")
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 1

    def test_execute_no_subcommand(self):
        """测试没有子命令"""
        cmd = FlowCommand()
        args = argparse.Namespace()
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 1

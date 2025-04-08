#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试知识库命令

验证知识库命令的基本功能
"""

import argparse
from unittest import mock

import pytest

from src.cli.commands.memory.memory_command import MemoryCommand


class TestMemoryCommand:
    """知识库命令测试类"""

    def test_init(self):
        """测试初始化"""
        cmd = MemoryCommand()
        assert cmd.name == "memory"
        assert cmd.description is not None

    def test_configure_parser(self):
        """测试配置解析器"""
        cmd = MemoryCommand()
        parser = argparse.ArgumentParser()
        cmd.configure_parser(parser)

        # 验证子命令解析器已经配置
        assert parser._subparsers is not None

    @mock.patch("src.cli.commands.memory.memory_command.handle_create_subcommand")
    def test_execute_write(self, mock_handler):
        """测试执行写入子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功写入知识库", {})

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(
            subcommand="create", title="测试文档", folder="test", tags="test,example", content="这是测试内容", agent_mode=False, verbose=False
        )
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    @mock.patch("src.cli.commands.memory.memory_command.handle_show_subcommand")
    def test_execute_read(self, mock_handler):
        """测试执行读取子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功读取知识库内容", {})

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="show", path="memory://test/document", agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    @mock.patch("src.cli.commands.memory.memory_command.handle_search_subcommand")
    def test_execute_search(self, mock_handler):
        """测试执行搜索子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功搜索知识库", [])

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="search", query="测试关键词", type=None, agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    @mock.patch("src.cli.commands.memory.memory_command.handle_import_subcommand")
    def test_execute_import(self, mock_handler):
        """测试执行导入子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功导入文档", {})

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="import", source_dir="/path/to/docs", agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    @mock.patch("src.cli.commands.memory.memory_command.handle_export_subcommand")
    def test_execute_export(self, mock_handler):
        """测试执行导出子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功导出知识库", {})

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="export", db=None, output=None, agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    @mock.patch("src.cli.commands.memory.memory_command.handle_sync_subcommand")
    def test_execute_sync(self, mock_handler):
        """测试执行同步子命令"""
        # 配置模拟行为
        mock_handler.return_value = (True, "成功同步文档", {})

        # 创建命令并执行
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="sync", sync_type="to-obsidian", agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 0
        mock_handler.assert_called_once_with(args)

    def test_execute_unknown_subcommand(self):
        """测试执行未知子命令"""
        cmd = MemoryCommand()
        args = argparse.Namespace(subcommand="unknown", agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 1

    def test_execute_no_subcommand(self):
        """测试没有子命令"""
        cmd = MemoryCommand()
        args = argparse.Namespace(agent_mode=False, verbose=False)
        result = cmd.execute_with_args(args)

        # 验证结果
        assert result == 1

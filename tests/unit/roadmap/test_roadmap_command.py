#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Roadmap命令功能
"""

import unittest
from unittest.mock import MagicMock, patch

from src.cli.commands.roadmap.roadmap_command import RoadmapCommand


class TestRoadmapCommand(unittest.TestCase):
    """测试Roadmap命令功能"""

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    def test_init_roadmap_command(self, mock_roadmap_service):
        """测试初始化路线图命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        # 测试初始化
        command = RoadmapCommand()

        # 验证服务创建
        mock_roadmap_service.assert_called_once()
        self.assertEqual(command.service, mock_service_instance)

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapCommandExecutor")
    def test_execute_list_subcommand(self, mock_executor, mock_roadmap_service):
        """测试执行list子命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        mock_executor_instance = MagicMock()
        mock_executor_instance.execute_command.return_value = {
            "success": True,
            "data": [
                {"id": "roadmap1", "name": "路线图1", "description": "描述1"},
                {"id": "roadmap2", "name": "路线图2", "description": "描述2"},
            ],
        }
        mock_executor.return_value = mock_executor_instance

        # 初始化命令
        command = RoadmapCommand()

        # 测试执行list子命令
        with patch("src.cli.commands.roadmap.roadmap_command.console") as mock_console:
            command.execute(["list"])

            # 验证执行器调用
            mock_executor_instance.execute_command.assert_called_once()
            # 验证输出调用（简化检查）
            self.assertTrue(mock_console.print.called)

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapCommandExecutor")
    def test_execute_show_subcommand(self, mock_executor, mock_roadmap_service):
        """测试执行show子命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        mock_executor_instance = MagicMock()
        mock_executor_instance.execute_command.return_value = {
            "success": True,
            "data": {
                "id": "roadmap1",
                "name": "路线图1",
                "description": "描述1",
                "milestones": [{"id": "m1", "name": "里程碑1", "tasks": []}],
            },
        }
        mock_executor.return_value = mock_executor_instance

        # 初始化命令
        command = RoadmapCommand()

        # 测试执行show子命令
        with patch("src.cli.commands.roadmap.roadmap_command.console") as mock_console:
            # 不带ID参数时应该显示错误消息
            command.execute(["show"])

            # 带ID参数时应该显示指定路线图
            command.execute(["show", "roadmap1"])

            # 验证执行器调用
            self.assertEqual(mock_executor_instance.execute_command.call_count, 2)
            # 验证输出调用（简化检查）
            self.assertTrue(mock_console.print.called)

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapCommandExecutor")
    def test_execute_sync_subcommand(self, mock_executor, mock_roadmap_service):
        """测试执行sync子命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        mock_executor_instance = MagicMock()
        mock_executor_instance.execute_command.return_value = {
            "success": True,
            "message": "同步成功",
            "data": {"updated": 2, "added": 1},  # 添加一些数据，这样会输出到控制台
        }
        mock_executor.return_value = mock_executor_instance

        # 初始化命令
        command = RoadmapCommand()

        # 测试执行sync子命令
        with patch("src.cli.commands.roadmap.roadmap_command.console") as mock_console:
            command.execute(["sync"])

            # 验证执行器调用
            mock_executor_instance.execute_command.assert_called_once()

            # 确保mock_console.print至少被调用一次
            args_list = mock_console.print.call_args_list
            print(f"mock_console.print call_args_list: {args_list}")
            self.assertTrue(mock_console.print.called, "console.print 应该被调用但没有被调用")

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapCommandExecutor")
    def test_execute_help_subcommand(self, mock_executor, mock_roadmap_service):
        """测试执行help子命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        mock_executor_instance = MagicMock()
        mock_executor.return_value = mock_executor_instance

        # 初始化命令
        command = RoadmapCommand()

        # 测试执行help子命令
        with patch("builtins.print") as mock_print:
            command.execute(["--help"])

            # 验证打印帮助信息
            mock_print.assert_called()

    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapService")
    @patch("src.cli.commands.roadmap.roadmap_command.RoadmapCommandExecutor")
    def test_execute_invalid_subcommand(self, mock_executor, mock_roadmap_service):
        """测试执行无效子命令"""
        # 设置模拟对象
        mock_service_instance = MagicMock()
        mock_roadmap_service.return_value = mock_service_instance

        mock_executor_instance = MagicMock()
        mock_executor_instance.execute_command.return_value = {"success": False, "error": "未知的路线图操作: invalid_subcommand"}
        mock_executor.return_value = mock_executor_instance

        # 初始化命令
        command = RoadmapCommand()

        # 测试执行无效子命令
        with patch("src.cli.commands.roadmap.roadmap_command.console") as mock_console:
            command.execute(["invalid_subcommand"])

            # 验证输出错误消息
            self.assertTrue(mock_console.print.called, "console.print 应该被调用")

            # 打印调用信息用于调试
            args_list = mock_console.print.call_args_list
            print(f"mock_console.print call_args_list: {args_list}")


if __name__ == "__main__":
    unittest.main()

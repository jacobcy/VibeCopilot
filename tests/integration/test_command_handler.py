"""
命令处理器集成测试模块

测试命令处理器的基本功能
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cli.command_parser import CommandParser
from src.cursor.command.handler import CursorCommandHandler


def test_command_handler_initialization():
    """测试命令处理器初始化"""
    handler = CursorCommandHandler()
    assert isinstance(handler.command_parser, CommandParser)
    assert handler.rule_engine is not None


def test_parse_command():
    """测试命令解析功能"""
    handler = CursorCommandHandler()

    # 测试带参数的命令
    command_name, args = handler._parse_command("/check --type=task --id=123")
    assert command_name == "check"
    assert "--type=task" in args
    assert "--id=123" in args

    # 测试无参数的命令
    command_name, args = handler._parse_command("/help")
    assert command_name == "help"
    assert len(args) == 0

    # 测试空格处理
    command_name, args = handler._parse_command("  /status  show  ")
    assert command_name == "status"
    assert args == ["show"]


def test_command_execution():
    """测试命令执行流程"""
    # 正确使用patch，目标是已实例化对象的方法
    with patch(
        "src.cli.command_parser.CommandParser.execute_command", return_value={"success": True, "message": "命令执行成功", "data": {"result": "ok"}}
    ) as mock_execute:
        handler = CursorCommandHandler()
        result = handler.handle_command("/test --arg=value")

        # 验证命令解析器被调用
        mock_execute.assert_called_once()

        # 验证结果
        assert result["success"] is True
        assert "message" in result


def test_error_handling():
    """测试错误处理"""
    # 模拟命令解析器抛出异常
    with patch("src.cli.command_parser.CommandParser") as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser.execute_command.side_effect = ValueError("未知命令")
        mock_parser.get_available_commands.return_value = []
        mock_parser_class.return_value = mock_parser

        handler = CursorCommandHandler()
        result = handler.handle_command("/unknown")

        # 验证错误处理
        assert result["success"] is False
        assert "error" in result
        assert "命令格式错误" in result["error"]
        assert "未知命令" in result["error"]

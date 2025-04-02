"""
命令解析器测试模块
"""

import pytest

from src.cli.base_command import BaseCommand
from src.cli.command_parser import CommandParser


class MockCommand(BaseCommand):
    """测试用命令类"""

    def __init__(self):
        super().__init__(name="mock", description="Mock command for testing")

    def execute(self, args):
        return {"success": True, "args": args}


def test_command_parser_initialization():
    """测试命令解析器初始化"""
    parser = CommandParser()
    assert isinstance(parser.commands, dict)
    assert len(parser.commands) >= 2  # 至少包含 check 和 update 命令


def test_parse_command_basic():
    """测试基本命令解析"""
    parser = CommandParser()
    command_str = "/check --type=task"
    name, args = parser.parse_command(command_str)
    assert name == "check"
    assert args == {"type": "task"}


def test_parse_command_with_multiple_args():
    """测试多参数命令解析"""
    parser = CommandParser()
    command_str = "/check --type=task --id=123 --verbose"
    name, args = parser.parse_command(command_str)
    assert name == "check"
    assert args == {"type": "task", "id": "123", "verbose": True}


def test_parse_command_without_args():
    """测试无参数命令解析"""
    parser = CommandParser()
    command_str = "/check"
    name, args = parser.parse_command(command_str)
    assert name == "check"
    assert args == {}


def test_parse_command_invalid_format():
    """测试无效命令格式"""
    parser = CommandParser()
    with pytest.raises(ValueError):
        parser.parse_command("check")  # 没有前导斜杠


def test_parse_command_empty():
    """测试空命令"""
    parser = CommandParser()
    with pytest.raises(ValueError):
        parser.parse_command("")


def test_register_command():
    """测试命令注册"""
    parser = CommandParser()
    mock_command = MockCommand()
    parser.register_command(mock_command)
    assert "mock" in parser.commands
    assert parser.commands["mock"] == mock_command


def test_execute_command_success():
    """测试命令执行成功"""
    parser = CommandParser()
    mock_command = MockCommand()
    parser.register_command(mock_command)
    result = parser.execute_command("/mock --test=value")
    assert result["success"] is True
    assert result["args"] == {"test": "value"}


def test_execute_command_unknown():
    """测试未知命令执行"""
    parser = CommandParser()
    result = parser.execute_command("/unknown")
    assert result["success"] is False
    assert "未知命令" in result["error"]


def test_execute_command_error():
    """测试命令执行错误"""
    parser = CommandParser()
    result = parser.execute_command("invalid")  # 无效格式
    assert result["success"] is False
    assert "处理命令失败" in result["error"]

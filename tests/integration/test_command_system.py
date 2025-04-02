"""
命令系统集成测试模块
"""

import pytest

from src.cli.command_parser import CommandParser
from src.core.rule_engine import RuleEngine
from src.cursor.command_handler import CursorCommandHandler


def test_command_handler_initialization():
    """测试命令处理器初始化"""
    handler = CursorCommandHandler()
    assert isinstance(handler.command_parser, CommandParser)
    assert isinstance(handler.rule_engine, RuleEngine)


def test_command_flow_check():
    """测试检查命令流程"""
    handler = CursorCommandHandler()
    result = handler.handle_command("/check --type=task")
    assert result["success"] is True


def test_command_flow_update():
    """测试更新命令流程"""
    handler = CursorCommandHandler()
    result = handler.handle_command("/update --status=done")
    assert result["success"] is True
    assert "message" in result
    assert result["data"]["status"] == "done"


def test_command_flow_invalid():
    """测试无效命令流程"""
    handler = CursorCommandHandler()
    result = handler.handle_command("invalid")
    assert result["success"] is False
    assert "处理命令失败" in result["error"]


def test_rule_engine_integration():
    """测试规则引擎集成"""
    handler = CursorCommandHandler()
    result = handler.handle_command("/rule --action=test")
    assert result["success"] is True
    assert result.get("handled") is True


def test_command_chain():
    """测试命令链执行"""
    handler = CursorCommandHandler()

    # 执行一系列相关命令
    results = []
    commands = [
        "/check --type=task",
        "/update --status=in_progress",
        "/check --type=task",
        "/update --status=done",
        "/check --type=task",
    ]

    for cmd in commands:
        result = handler.handle_command(cmd)
        results.append(result)
        assert result["success"] is True, f"命令 {cmd} 执行失败: {result.get('error', '')}"


def test_error_handling():
    """测试错误处理"""
    handler = CursorCommandHandler()

    error_cases = [
        ("", "命令不能为空"),
        ("no_slash", "命令必须以/开头"),
        ("/unknown", "未知命令"),
        ("/check --invalid", None),  # 参数验证由具体命令处理
    ]

    for cmd, expected_error in error_cases:
        result = handler.handle_command(cmd)
        assert result["success"] is False, f"命令 {cmd} 应该失败但返回成功"
        if expected_error:
            assert expected_error in result["error"], f"命令 {cmd} 的错误消息不符合预期"

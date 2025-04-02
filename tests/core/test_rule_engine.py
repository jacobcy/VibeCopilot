"""规则引擎测试模块"""

import os
from unittest.mock import mock_open, patch

import pytest

from src.core.exceptions import RuleError
from src.core.rule_engine import RuleEngine

MOCK_RULE = {
    "name": "test_rule",
    "pattern": "/test",
    "action": {"type": "response", "message": "Test rule executed"},
}

MOCK_RULE_YAML = """
name: test_rule
pattern: /test
action:
  type: response
  message: Test rule executed
"""


@pytest.fixture
def rule_engine():
    """创建规则引擎实例"""
    return RuleEngine()


def test_validate_rule(rule_engine):
    """测试规则验证"""
    # 有效规则
    assert rule_engine._validate_rule(MOCK_RULE) is True

    # 缺少必要字段
    invalid_rule = {"name": "test"}
    with pytest.raises(RuleError) as exc:
        rule_engine._validate_rule(invalid_rule)
    assert "缺少必要字段" in str(exc.value)

    # 无效的模式类型
    invalid_rule = {"name": "test", "pattern": 123, "action": {}}
    with pytest.raises(RuleError) as exc:
        rule_engine._validate_rule(invalid_rule)
    assert "规则模式必须是字符串" in str(exc.value)

    # 无效的动作类型
    invalid_rule = {"name": "test", "pattern": "/test", "action": "invalid"}
    with pytest.raises(RuleError) as exc:
        rule_engine._validate_rule(invalid_rule)
    assert "规则动作必须是字典" in str(exc.value)


def test_add_rule(rule_engine):
    """测试添加规则"""
    rule_engine.add_rule("test", MOCK_RULE, priority=1)

    # 验证规则是否添加成功
    assert rule_engine.get_rule("test") == MOCK_RULE
    assert rule_engine.rule_priorities["test"] == 1


def test_get_matching_rules(rule_engine):
    """测试获取匹配规则"""
    # 添加测试规则
    rule_engine.add_rule("test1", {"name": "test1", "pattern": "/test", "action": {}}, priority=1)

    rule_engine.add_rule("test2", {"name": "test2", "pattern": "/test", "action": {}}, priority=2)

    # 测试规则匹配
    matching_rules = rule_engine.get_matching_rules("/test command")
    assert len(matching_rules) == 2

    # 验证优先级排序
    assert matching_rules[0]["name"] == "test2"
    assert matching_rules[1]["name"] == "test1"

    # 测试无匹配规则
    assert len(rule_engine.get_matching_rules("/unknown")) == 0


@patch("os.walk")
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_RULE_YAML)
def test_load_rules(mock_file, mock_walk, rule_engine):
    """测试加载规则文件"""
    # 模拟规则文件
    mock_walk.return_value = [("/rules", [], ["test.yml"])]

    # 加载规则
    rule_engine.load_rules("/rules")

    # 验证规则是否加载成功
    assert "test_rule" in rule_engine.rules
    assert rule_engine.rules["test_rule"]["pattern"] == "/test"


def test_process_command(rule_engine):
    """测试命令处理"""
    # 添加测试规则
    rule_engine.add_rule("test", MOCK_RULE)

    # 测试匹配命令
    result = rule_engine.process_command("/test command")
    assert result["handled"] is True
    assert result["success"] is True
    assert result["rule"] == "test_rule"

    # 测试不匹配命令
    result = rule_engine.process_command("/unknown")
    assert result["handled"] is False

    # 测试异常处理
    with patch.object(rule_engine, "get_matching_rules", side_effect=Exception("Test error")):
        result = rule_engine.process_command("/test")
        assert result["handled"] is True
        assert result["success"] is False
        assert "规则引擎处理失败" in result["error"]

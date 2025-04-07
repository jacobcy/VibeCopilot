"""
基础解析器测试模块
"""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from rule_parser.base_parser import RuleParser


# 创建一个测试用的具体解析器类
class TestParser(RuleParser):
    """用于测试的规则解析器实现"""

    def parse_rule_content(self, content, context=""):
        """实现基类的抽象方法"""
        # 简单实现，返回包含文件名作为ID的结果
        return {"id": Path(context).stem if context else "test", "name": "测试规则", "content": content}


@pytest.fixture
def parser():
    """创建解析器实例"""
    return TestParser()


def test_init_default_model(parser):
    """测试初始化默认模型"""
    assert parser.model == "gpt-4o-mini"


def test_init_custom_model():
    """测试初始化自定义模型"""
    custom_parser = TestParser("test-model")
    assert custom_parser.model == "test-model"


def test_parse_rule_file_success(parser):
    """测试成功解析规则文件"""
    # 模拟文件内容
    mock_content = """---
name: 测试规则
description: 这是一个测试规则
---

# 测试规则

这是一个测试规则的内容。
"""

    # 模拟打开文件
    with patch("builtins.open", mock_open(read_data=mock_content)):
        # 解析文件
        result = parser.parse_rule_file("test_rule.md")

        # 验证结果
        assert result["id"] == "test_rule"
        assert result["name"] == "测试规则"
        assert "这是一个测试规则的内容" in result["content"]


def test_parse_rule_file_with_front_matter(parser):
    """测试解析带Front Matter的规则文件"""
    # 模拟文件内容
    mock_content = """---
id: custom-id
name: 前事项规则
type: manual
description: 这是一个带Front Matter的规则
globs: ["*.ts", "*.tsx"]
---

# 前事项规则

这是规则内容。
"""

    # 模拟打开文件
    with patch("builtins.open", mock_open(read_data=mock_content)):
        # 解析文件
        result = parser.parse_rule_file("front_matter_rule.md")

        # 验证结果
        assert result["id"] == "custom-id"  # 应该使用Front Matter中的ID
        assert result["name"] == "前事项规则"
        assert result["type"] == "manual"
        assert result["description"] == "这是一个带Front Matter的规则"
        assert "*.ts" in result["globs"]
        assert "这是规则内容" in result["content"]


def test_parse_rule_file_read_error(parser):
    """测试文件读取错误"""
    # 模拟文件打开失败
    with patch("builtins.open", side_effect=IOError("文件不存在")):
        # 解析文件
        result = parser.parse_rule_file("nonexistent_rule.md")

        # 验证返回了默认结果
        assert result["id"] == "nonexistent_rule"
        assert result["name"] == "nonexistent_rule"
        assert result["type"] == "manual"
        assert "无法解析的规则文件" in result["description"]


def test_get_default_result(parser):
    """测试获取默认结果"""
    # 调用_get_default_result方法
    result = parser._get_default_result("test_rule.md")

    # 验证结果
    assert result["id"] == "test_rule"
    assert result["name"] == "test_rule"
    assert result["type"] == "manual"
    assert "无法解析的规则文件" in result["description"]
    assert len(result["globs"]) == 0
    assert result["always_apply"] is False

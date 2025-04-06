"""
规则模板测试模块
"""

import pytest
from rule_parser.lib.rule_template import extract_blocks_from_content, validate_rule_structure


def test_validate_rule_structure_valid():
    """测试有效的规则结构验证"""
    # 创建有效的规则数据
    valid_rule = {
        "id": "test-rule",
        "name": "测试规则",
        "type": "manual",
        "description": "这是一个测试规则",
        "items": [{"content": "规则条目1"}],
        "examples": [{"content": "示例1", "is_valid": True}],
    }

    # 验证应该通过
    assert validate_rule_structure(valid_rule) is True


def test_validate_rule_structure_missing_required():
    """测试缺少必要字段的规则结构验证"""
    # 缺少必要字段的规则
    invalid_rule = {"description": "没有ID和名称的规则"}

    # 验证应该失败
    assert validate_rule_structure(invalid_rule) is False


def test_validate_rule_structure_invalid_items():
    """测试无效items字段的规则结构验证"""
    # items字段格式错误的规则
    invalid_rule = {"id": "test-rule", "name": "测试规则", "items": ["这不是一个字典"]}  # 应该是包含content字段的字典

    # 验证应该失败
    assert validate_rule_structure(invalid_rule) is False


def test_extract_blocks_from_content_with_blocks():
    """测试从有块标记的内容中提取块"""
    # 包含块标记的内容
    content = """# 测试规则

<!-- BLOCK START id=block1 type=principle -->
**P1: 第一个原则**

这是第一个原则的内容
<!-- BLOCK END -->

其他内容

<!-- BLOCK START id=block2 type=example -->
**示例1**

这是一个示例
<!-- BLOCK END -->
"""

    # 提取块
    blocks = extract_blocks_from_content(content)

    # 验证结果
    assert len(blocks) == 2
    assert blocks[0]["id"] == "block1"
    assert blocks[0]["type"] == "principle"
    assert "第一个原则" in blocks[0]["content"]

    assert blocks[1]["id"] == "block2"
    assert blocks[1]["type"] == "example"
    assert "示例1" in blocks[1]["content"]


def test_extract_blocks_from_content_without_blocks():
    """测试从没有块标记的内容中提取块"""
    # 不包含块标记的内容
    content = """# 测试规则

这是一个没有块标记的规则内容。
"""

    # 提取块
    blocks = extract_blocks_from_content(content)

    # 验证结果
    assert len(blocks) == 0


def test_extract_blocks_from_content_with_unclosed_block():
    """测试从有未闭合块的内容中提取块"""
    # 包含未闭合块的内容
    content = """# 测试规则

<!-- BLOCK START id=block1 type=principle -->
**P1: 第一个原则**

这是第一个原则的内容，但没有结束标记
"""

    # 提取块
    blocks = extract_blocks_from_content(content)

    # 验证结果：未闭合的块不应该被提取
    assert len(blocks) == 0

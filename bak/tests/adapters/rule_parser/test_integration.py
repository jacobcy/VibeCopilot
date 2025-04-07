"""
规则解析器集成测试模块
"""

import os
from pathlib import Path

import pytest
from rule_parser.utils import detect_rule_conflicts, parse_rule_content, parse_rule_file


# 获取测试fixtures目录
@pytest.fixture
def fixtures_dir():
    """获取测试fixtures目录"""
    tests_dir = Path(__file__).parent.parent.parent.parent
    return tests_dir / "fixtures" / "rule_parser"


def test_parse_simple_rule_file(fixtures_dir):
    """测试解析简单规则文件"""
    # 解析简单规则文件
    rule_path = fixtures_dir / "simple_rule.md"
    result = parse_rule_file(str(rule_path))

    # 验证结果
    assert result["id"] == "simple_rule"
    assert result["name"] is not None
    assert "计算总价" in result["content"]
    assert isinstance(result.get("items", []), list)


def test_parse_frontmatter_rule_file(fixtures_dir):
    """测试解析带Front Matter的规则文件"""
    # 解析带Front Matter的规则文件
    rule_path = fixtures_dir / "frontmatter_rule.md"
    result = parse_rule_file(str(rule_path))

    # 验证结果
    assert result["id"] == "test-frontmatter-rule"
    assert result["name"] == "前事项测试规则"
    assert result["type"] == "manual"
    assert result["description"] == "这是一个带Front Matter的测试规则"
    assert "*.ts" in result["globs"]
    assert result["always_apply"] is True

    # 验证结构化数据
    assert len(result.get("items", [])) > 0


def test_parse_rule_content():
    """测试解析规则内容"""
    # 规则内容
    content = """# 内容测试规则

这是一个用于测试的规则内容。

## 规则条目

* 规则条目1
* 规则条目2

## 示例

```
示例代码
```"""

    # 解析规则内容
    result = parse_rule_content(content, "content_test.md")

    # 验证结果
    assert result["name"] is not None
    assert "内容测试规则" in result["content"]
    assert isinstance(result.get("items", []), list)


def test_detect_conflicts(fixtures_dir):
    """测试检测规则冲突"""
    # 解析两个冲突的规则
    rule1_path = fixtures_dir / "conflicting_rule_1.md"
    rule2_path = fixtures_dir / "conflicting_rule_2.md"

    rule1 = parse_rule_file(str(rule1_path))
    rule2 = parse_rule_file(str(rule2_path))

    # 检测冲突
    conflict_result = detect_rule_conflicts(rule1, rule2)

    # 验证结果
    assert "has_conflict" in conflict_result
    assert isinstance(conflict_result["conflict_description"], str)

    # 由于使用简单冲突检测，这两个规则应该有glob冲突
    if conflict_result["has_conflict"]:
        assert "glob" in conflict_result["conflict_description"].lower()


def test_end_to_end_flow(fixtures_dir):
    """端到端测试规则解析流程"""
    # 列出测试目录中的所有规则文件
    rule_files = list(fixtures_dir.glob("*.md"))
    assert len(rule_files) > 0

    # 解析所有规则文件
    rules = []
    for rule_file in rule_files:
        rule = parse_rule_file(str(rule_file))
        assert rule["id"] is not None
        assert rule["name"] is not None
        assert len(rule["content"]) > 0
        rules.append(rule)

    # 尝试检测所有规则对之间的冲突
    conflict_count = 0
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            conflict = detect_rule_conflicts(rules[i], rules[j])
            if conflict["has_conflict"]:
                conflict_count += 1

    # 至少应该检测到一个冲突（冲突规则对）
    assert conflict_count > 0

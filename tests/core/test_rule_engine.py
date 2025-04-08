"""
规则引擎测试模块

测试规则引擎的主要功能，包括解析、验证、导出和生成
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.rule_model import Example, Rule, RuleItem, RuleMetadata
from src.rule_engine.exporters.rule_exporter import export_rule_to_yaml


class TestRuleExporter(unittest.TestCase):
    """测试规则导出器"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟规则数据
        self.MOCK_RULE = {
            "id": "test_rule",
            "name": "测试规则",
            "type": "auto",
            "description": "这是一个测试规则",
            "content": "# 测试规则\n\n这是一个用于测试的规则。",
            "globs": ["*.py", "*.md"],
            "always_apply": False,
            "metadata": {"author": "测试作者", "version": "1.0.0", "tags": ["测试", "示例"]},
            "items": [{"content": "规则项1", "priority": 1}, {"content": "规则项2", "priority": 2}],
            "examples": [{"content": "示例1", "is_valid": True}, {"content": "示例2", "is_valid": False}],
        }

    def test_export_rule_to_yaml(self):
        """测试将规则导出为YAML格式"""
        # 调用导出函数
        yaml_text = export_rule_to_yaml(self.MOCK_RULE)

        # 验证导出结果包含必要字段
        assert "id: test_rule" in yaml_text
        assert "name: 测试规则" in yaml_text
        assert "type: auto" in yaml_text
        assert "description: 这是一个测试规则" in yaml_text

        # 验证导出结果包含可选字段
        assert "globs:" in yaml_text
        assert "'*.py'" in yaml_text or "*.py" in yaml_text  # 允许任一种表示形式
        assert "'*.md'" in yaml_text or "*.md" in yaml_text  # 允许任一种表示形式

        # always_apply为False时字段可能不包含在结果中
        # 如果包含，应该为False
        if "always_apply:" in yaml_text:
            assert "always_apply: false" in yaml_text.lower() or "always_apply: False" in yaml_text

        # 验证导出结果包含metadata字段
        assert "metadata:" in yaml_text
        assert "author: 测试作者" in yaml_text
        assert "version: 1.0.0" in yaml_text
        assert "tags:" in yaml_text
        assert "- 测试" in yaml_text
        assert "- 示例" in yaml_text

        # 验证导出结果包含items字段
        assert "items:" in yaml_text
        assert "content: 规则项1" in yaml_text
        assert "priority: 1" in yaml_text
        assert "content: 规则项2" in yaml_text
        assert "priority: 2" in yaml_text

        # 验证导出结果包含examples字段
        assert "examples:" in yaml_text
        assert "content: 示例1" in yaml_text
        assert "is_valid: true" in yaml_text.lower() or "is_valid: True" in yaml_text
        assert "content: 示例2" in yaml_text
        assert "is_valid: false" in yaml_text.lower() or "is_valid: False" in yaml_text

        # 测试always_apply为True的情况
        rule_with_always_apply = self.MOCK_RULE.copy()
        rule_with_always_apply["always_apply"] = True
        yaml_text_always_apply = export_rule_to_yaml(rule_with_always_apply)
        assert "always_apply: true" in yaml_text_always_apply.lower() or "always_apply: True" in yaml_text_always_apply

    def test_export_rule_to_file(self):
        """测试将规则导出到文件"""
        # 使用临时文件
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # 调用导出函数
            result_path = export_rule_to_yaml(self.MOCK_RULE, temp_path)

            # 验证返回值是文件路径
            assert result_path == temp_path

            # 验证文件存在
            assert os.path.exists(temp_path)

            # 验证文件内容
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "id: test_rule" in content
                assert "name: 测试规则" in content
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_export_rule_object_to_yaml(self):
        """测试将Rule对象导出为YAML格式"""
        # 创建Rule对象
        metadata = RuleMetadata(
            author="测试作者", version="1.0.0", tags=["测试", "示例"], created_at="2023-01-01T00:00:00", updated_at="2023-01-01T00:00:00", dependencies=[]
        )

        items = [RuleItem(content="规则项1", priority=1), RuleItem(content="规则项2", priority=2)]

        examples = [Example(content="示例1", is_valid=True), Example(content="示例2", is_valid=False)]

        rule = Rule(
            id="test_rule",
            name="测试规则",
            type="auto",
            description="这是一个测试规则",
            content="# 测试规则\n\n这是一个用于测试的规则。",
            globs=["*.py", "*.md"],
            always_apply=False,
            metadata=metadata,
            items=items,
            examples=examples,
        )

        # 调用导出函数
        yaml_text = export_rule_to_yaml(rule)

        # 验证导出结果
        assert "id: test_rule" in yaml_text
        assert "name: 测试规则" in yaml_text
        assert "type: auto" in yaml_text


if __name__ == "__main__":
    unittest.main()

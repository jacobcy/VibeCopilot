"""
规则生成器单元测试

测试规则生成器的核心功能，包括规则内容生成和文件输出
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.rule_model import Rule, RuleType
from src.rule_engine.generators.rule_generator import RuleGenerator


class TestRuleGenerator:
    """规则生成器测试类"""

    def setup_method(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.template_repo = MagicMock()
        self.rule_repo = MagicMock()
        self.rule_generator = RuleGenerator(template_repo=self.template_repo, rule_repo=self.rule_repo)

    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.test_dir)

    def test_generate_rule(self):
        """测试生成规则数据"""
        # 模拟模板
        mock_template = MagicMock()
        mock_template.content = """---
id: {{ id }}
type: {{ type }}
title: {{ title }}
---

# {{ title }}

## 目的
{{ purpose }}

## 使用场景
{% for scene in scenes %}
- {{ scene }}
{% endfor %}
"""
        # 创建变量对象，确保name是字符串而不是MagicMock
        var1 = MagicMock()
        var1.name = "id"
        var1.required = True
        var1.default_value = None

        var2 = MagicMock()
        var2.name = "type"
        var2.required = True
        var2.default_value = '"rule"'

        var3 = MagicMock()
        var3.name = "title"
        var3.required = True
        var3.default_value = None

        var4 = MagicMock()
        var4.name = "purpose"
        var4.required = True
        var4.default_value = None

        var5 = MagicMock()
        var5.name = "scenes"
        var5.required = True
        var5.default_value = None

        mock_template.get_variables.return_value = [var1, var2, var3, var4, var5]

        # 设置模板仓库返回值
        self.template_repo.get_template_by_id.return_value = mock_template

        # 设置变量
        variables = {
            "id": "test-rule-01",
            "type": "rule",
            "title": "测试规则",
            "purpose": "用于测试规则生成器",
            "scenes": ["场景1", "场景2", "场景3"],
        }

        # 生成规则
        rule_data = self.rule_generator.generate_rule("test-template", variables)

        # 验证规则数据
        assert rule_data["id"] == "test-rule-01"
        assert rule_data["type"] == "rule"
        assert rule_data["title"] == "测试规则"
        assert "# 测试规则" in rule_data["content"]
        assert "## 目的\n用于测试规则生成器" in rule_data["content"]
        assert "- 场景1" in rule_data["content"]
        assert "- 场景2" in rule_data["content"]
        assert "- 场景3" in rule_data["content"]

    def test_generate_rule_with_missing_variables(self):
        """测试缺少必要变量时生成规则"""
        # 模拟模板
        mock_template = MagicMock()
        mock_template.content = "# {{ title }}\n{{ description }}"

        # 创建变量对象，确保name是字符串而不是MagicMock
        var1 = MagicMock()
        var1.name = "title"
        var1.required = True
        var1.default_value = None

        var2 = MagicMock()
        var2.name = "description"
        var2.required = True
        var2.default_value = None

        mock_template.get_variables.return_value = [var1, var2]

        # 设置模板仓库返回值
        self.template_repo.get_template_by_id.return_value = mock_template

        # 缺少必要变量
        variables = {
            "title": "测试规则"
            # 缺少 description
        }

        # 应该抛出ValueError异常
        with pytest.raises(ValueError):
            self.rule_generator.generate_rule("test-template", variables)

    def test_generate_rule_file(self):
        """测试生成规则文件"""
        # 模拟模板
        mock_template = MagicMock()
        mock_template.content = """---
id: {{ id }}
type: {{ type }}
---

# {{ title }}

{{ content }}
"""
        # 创建变量对象，确保name是字符串而不是MagicMock
        var1 = MagicMock()
        var1.name = "id"
        var1.required = True
        var1.default_value = None

        var2 = MagicMock()
        var2.name = "type"
        var2.required = True
        var2.default_value = '"rule"'

        var3 = MagicMock()
        var3.name = "title"
        var3.required = True
        var3.default_value = None

        var4 = MagicMock()
        var4.name = "content"
        var4.required = True
        var4.default_value = None

        mock_template.get_variables.return_value = [var1, var2, var3, var4]

        # 设置模板仓库返回值
        self.template_repo.get_template_by_id.return_value = mock_template

        # 设置变量
        variables = {
            "id": "test-rule-file",
            "type": "rule",
            "title": "测试规则文件",
            "content": "这是测试规则的内容。",
        }

        # 设置输出路径
        output_path = Path(self.test_dir) / "test_rule.md"

        # 生成规则文件
        result_path = self.rule_generator.generate_rule_file("test-template", variables, output_path)

        # 验证结果
        assert result_path == str(output_path)
        assert output_path.exists()

        # 验证文件内容
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# 测试规则文件" in content
            assert "这是测试规则的内容。" in content

    def test_save_rule(self):
        """测试保存规则到仓库"""
        # 设置规则数据
        rule_data = {
            "id": "test-save-rule",
            "type": "rule",
            "title": "测试保存规则",
            "content": "# 测试保存规则\n\n这是规则内容。",
        }

        # 模拟规则仓库的create方法
        self.rule_repo.create.return_value = rule_data

        # 保存规则
        result = self.rule_generator.save_rule(rule_data)

        # 验证规则仓库的create方法被调用
        self.rule_repo.create.assert_called_once_with(rule_data)

        # 验证结果
        assert result == rule_data

    def test_save_rule_without_repo(self):
        """测试没有设置规则仓库时保存规则"""
        # 创建没有规则仓库的生成器
        generator = RuleGenerator(template_repo=self.template_repo)

        # 设置规则数据
        rule_data = {"id": "test-rule", "type": "rule"}

        # 应该抛出RuntimeError异常
        with pytest.raises(RuntimeError):
            generator.save_rule(rule_data)

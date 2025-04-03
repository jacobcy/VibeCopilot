"""
规则生成器单元测试
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from src.rule_templates.core.rule_generator import RuleGenerator
from src.rule_templates.core.template_engine import TemplateEngine
from src.rule_templates.models.rule import Rule, RuleType
from src.rule_templates.models.template import (
    Template,
    TemplateMetadata,
    TemplateVariable,
    TemplateVariableType,
)


class RuleGeneratorTests(unittest.TestCase):
    """规则生成器测试类"""

    def setUp(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.template_engine = TemplateEngine()
        self.rule_generator = RuleGenerator(template_engine=self.template_engine)

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.test_dir)

    def create_test_template(self):
        """创建测试模板"""
        return Template(
            id="test-template",
            name="测试模板",
            description="用于测试的模板",
            type="agent",
            content="""---
description: {{ description }}
globs: {{ globs|default([]) }}
alwaysApply: {{ always_apply|default(false) }}
---

# {{ title }}

## 目的
{{ purpose }}

## 使用场景
{% for scene in scenes %}
- {{ scene }}
{% endfor %}

## 示例
```
{{ example }}
```
""",
            variables=[
                TemplateVariable(
                    name="title",
                    type=TemplateVariableType.STRING,
                    description="规则标题",
                    required=True,
                ),
                TemplateVariable(
                    name="description",
                    type=TemplateVariableType.STRING,
                    description="规则描述",
                    required=True,
                ),
                TemplateVariable(
                    name="purpose",
                    type=TemplateVariableType.STRING,
                    description="规则目的",
                    required=True,
                ),
                TemplateVariable(
                    name="scenes",
                    type=TemplateVariableType.ARRAY,
                    description="使用场景",
                    required=True,
                ),
                TemplateVariable(
                    name="example",
                    type=TemplateVariableType.STRING,
                    description="示例代码",
                    required=True,
                ),
                TemplateVariable(
                    name="globs",
                    type=TemplateVariableType.ARRAY,
                    description="文件匹配模式",
                    required=False,
                    default=[],
                ),
                TemplateVariable(
                    name="always_apply",
                    type=TemplateVariableType.BOOLEAN,
                    description="是否始终应用",
                    required=False,
                    default=False,
                ),
            ],
            metadata=TemplateMetadata(author="测试作者", tags=["test"], version="1.0.0"),
        )

    def test_generate_rule(self):
        """测试生成规则对象"""
        template = self.create_test_template()

        variables = {
            "title": "测试规则",
            "description": "这是一个测试规则",
            "purpose": "用于测试规则生成功能",
            "scenes": ["场景1", "场景2", "场景3"],
            "example": "console.log('测试示例')",
            "globs": ["*.js", "*.ts"],
            "always_apply": True,
        }

        rule = self.rule_generator.generate_rule(template, variables)

        # 验证规则基本属性
        self.assertEqual(rule.name, "测试规则")
        self.assertEqual(rule.description, "这是一个测试规则")
        self.assertEqual(rule.type, RuleType.AGENT)
        self.assertEqual(rule.globs, ["*.js", "*.ts"])
        self.assertTrue(rule.always_apply)

        # 验证规则ID
        self.assertEqual(rule.id, "测试规则")

        # 验证规则内容包含渲染后的变量
        self.assertIn("# 测试规则", rule.content)
        self.assertIn("## 目的\n用于测试规则生成功能", rule.content)
        self.assertIn("- 场景1", rule.content)
        self.assertIn("- 场景2", rule.content)
        self.assertIn("- 场景3", rule.content)
        self.assertIn("console.log(&#39;测试示例&#39;)", rule.content)

    def test_generate_rule_with_missing_required_variable(self):
        """测试缺少必填变量时生成规则"""
        template = self.create_test_template()

        # 缺少必填变量scenes
        variables = {
            "title": "测试规则",
            "description": "这是一个测试规则",
            "purpose": "用于测试规则生成功能",
            "example": "console.log('测试示例')",
        }

        # 应该抛出ValueError异常
        with self.assertRaises(ValueError):
            self.rule_generator.generate_rule(template, variables)

    def test_generate_rule_file(self):
        """测试生成规则文件"""
        template = self.create_test_template()

        variables = {
            "title": "测试规则文件",
            "description": "这是一个测试规则文件",
            "purpose": "用于测试规则文件生成功能",
            "scenes": ["场景1", "场景2"],
            "example": "console.log('测试示例')",
        }

        output_path = os.path.join(self.test_dir, "test_rule.md")

        rule = self.rule_generator.generate_rule_file(template, variables, output_path)

        # 验证文件已创建
        self.assertTrue(os.path.exists(output_path))

        # 验证文件内容
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# 测试规则文件", content)
        self.assertIn("## 目的\n用于测试规则文件生成功能", content)
        self.assertIn("- 场景1", content)
        self.assertIn("- 场景2", content)

    def test_generate_rule_json(self):
        """测试生成规则的JSON表示"""
        template = self.create_test_template()

        variables = {
            "title": "测试规则JSON",
            "description": "这是一个测试规则JSON",
            "purpose": "用于测试规则JSON生成功能",
            "scenes": ["场景1"],
            "example": "console.log('测试示例')",
        }

        # 先生成规则对象
        rule = self.rule_generator.generate_rule(template, variables)

        # 生成JSON字符串
        output_path = os.path.join(self.test_dir, "test_rule.json")
        rule_json = self.rule_generator.generate_rule_json(rule, output_path)

        # 验证JSON文件已创建
        self.assertTrue(os.path.exists(output_path))

        # 验证JSON内容
        import json

        rule_dict = json.loads(rule_json)

        self.assertEqual(rule_dict["name"], "测试规则JSON")
        self.assertEqual(rule_dict["description"], "这是一个测试规则JSON")
        self.assertEqual(rule_dict["type"], "agent")
        self.assertEqual(rule_dict["metadata"]["author"], "测试作者")

    def test_batch_generate_rules(self):
        """测试批量生成规则"""
        template = self.create_test_template()

        # 创建多个模板配置
        template_configs = [
            {
                "template": template,
                "variables": {
                    "title": "规则1",
                    "description": "这是规则1",
                    "purpose": "用于测试批量生成功能",
                    "scenes": ["场景1"],
                    "example": "示例1",
                },
                "output_file": "rule1.md",
            },
            {
                "template": template,
                "variables": {
                    "title": "规则2",
                    "description": "这是规则2",
                    "purpose": "用于测试批量生成功能",
                    "scenes": ["场景2.1", "场景2.2"],
                    "example": "示例2",
                },
                "output_file": "rule2.md",
            },
        ]

        # 批量生成规则
        rules = self.rule_generator.batch_generate_rules(template_configs, self.test_dir)

        # 验证生成了2个规则
        self.assertEqual(len(rules), 2)

        # 验证文件已创建
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "rule1.md")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "rule2.md")))

        # 验证规则属性
        self.assertEqual(rules[0].name, "规则1")
        self.assertEqual(rules[1].name, "规则2")


if __name__ == "__main__":
    unittest.main()

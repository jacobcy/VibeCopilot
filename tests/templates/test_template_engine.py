"""
模板引擎单元测试

测试模板引擎的核心功能，包括模板渲染和变量处理
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.models.template import Template, TemplateMetadata, TemplateVariable, TemplateVariableType
from src.templates.core.template_engine import TemplateEngine


class TestTemplateEngine:
    """模板引擎测试类"""

    def setup_method(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.template_engine = TemplateEngine()

    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.test_dir)

    def test_render_template_string(self):
        """测试渲染模板字符串"""
        template_string = "Hello, {{ name }}! Today is {{ day }}."
        variables = {"name": "World", "day": "Monday"}

        result = self.template_engine.render_template_string(template_string, variables)

        assert result == "Hello, World! Today is Monday."

    def test_render_template_with_filters(self):
        """测试使用过滤器渲染模板"""
        template_string = "{{ snake_case|camel_case }} {{ snake_case|pascal_case }} {{ snake_case|kebab_case }}"
        variables = {"snake_case": "hello_world"}

        result = self.template_engine.render_template_string(template_string, variables)

        assert result == "helloWorld HelloWorld hello-world"

    def test_render_template(self):
        """测试渲染模板对象"""
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            type="agent",
            content="Title: {{ title }}\nDescription: {{ description }}",
            variables=[
                TemplateVariable(
                    name="title",
                    type=TemplateVariableType.STRING,
                    description="The title",
                    required=True,
                ),
                TemplateVariable(
                    name="description",
                    type=TemplateVariableType.STRING,
                    description="The description",
                    required=False,
                    default="Default description",
                ),
            ],
            metadata=TemplateMetadata(author="Test Author", tags=["test"], version="1.0.0"),
        )

        variables = {"title": "Hello World"}

        result = self.template_engine.render_template(template, variables)

        assert result == "Title: Hello World\nDescription: Default description"

    def test_apply_template_to_file(self):
        """测试应用模板到文件"""
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            type="agent",
            content="# {{ title }}\n\n{{ content }}",
            variables=[
                TemplateVariable(
                    name="title",
                    type=TemplateVariableType.STRING,
                    description="The title",
                    required=True,
                ),
                TemplateVariable(
                    name="content",
                    type=TemplateVariableType.STRING,
                    description="The content",
                    required=True,
                ),
            ],
            metadata=TemplateMetadata(author="Test Author", tags=["test"], version="1.0.0"),
        )

        variables = {"title": "Test Document", "content": "This is a test document content."}

        output_path = os.path.join(self.test_dir, "output.md")

        self.template_engine.apply_template(template, variables, output_path)

        # 验证文件是否创建
        assert os.path.exists(output_path)

        # 验证文件内容
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == "# Test Document\n\nThis is a test document content."

    def test_template_validation_error(self):
        """测试模板变量验证错误"""
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            type="agent",
            content="{{ required_var }}",
            variables=[
                TemplateVariable(
                    name="required_var",
                    type=TemplateVariableType.STRING,
                    description="A required variable",
                    required=True,
                )
            ],
            metadata=TemplateMetadata(author="Test Author", tags=["test"], version="1.0.0"),
        )

        variables = {}  # 缺少必填变量

        with pytest.raises(ValueError):
            self.template_engine.render_template(template, variables)

    def test_syntax_error(self):
        """测试模板语法错误"""
        template_string = "{{ unclosed_tag"
        variables = {}

        with pytest.raises(ValueError):
            self.template_engine.render_template_string(template_string, variables)

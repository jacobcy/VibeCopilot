#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流模板加载器

验证从模板文件加载工作流定义的功能
"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest import mock

import pytest

from src.workflow.template_loader import create_workflow_from_template, get_available_templates, load_flow_template


class TestWorkflowTemplateLoader:
    """工作流模板加载器测试类"""

    @pytest.fixture
    def mock_template_path(self):
        """创建模拟模板文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
            template_data = {
                "id": "test-workflow",
                "name": "测试工作流",
                "description": "用于测试的工作流模板",
                "version": "1.0.0",
                "stages": [{"id": "stage1", "name": "阶段1", "description": "第一个阶段", "order": 1}],
                "transitions": [{"from": "stage1", "to": "complete", "condition": "阶段1完成"}],
            }
            json.dump(template_data, f, ensure_ascii=False, indent=2)
            template_path = f.name

        yield template_path

        # 清理临时文件
        os.unlink(template_path)

    @mock.patch("src.workflow.template_loader.get_template_path")
    def test_load_flow_template(self, mock_get_template_path, mock_template_path):
        """测试加载工作流模板"""
        # 配置模拟行为
        mock_get_template_path.return_value = mock_template_path

        # 执行测试
        template = load_flow_template("test-workflow")

        # 验证结果
        assert template is not None
        assert template["id"] == "test-workflow"
        assert template["name"] == "测试工作流"
        assert len(template["stages"]) == 1
        assert len(template["transitions"]) == 1

    @mock.patch("src.workflow.template_loader.load_flow_template")
    @mock.patch("uuid.uuid4")
    def test_create_workflow_from_template(self, mock_uuid4, mock_load_flow_template):
        """测试从模板创建工作流"""
        # 配置模拟行为
        test_uuid = "12345678-1234-5678-1234-567812345678"
        mock_uuid4.return_value = uuid.UUID(test_uuid)

        template_data = {
            "id": "test-workflow",
            "name": "测试工作流",
            "description": "用于测试的工作流模板",
            "version": "1.0.0",
            "stages": [{"id": "stage1", "name": "阶段1"}],
            "transitions": [{"from": "stage1", "to": "complete"}],
        }
        mock_load_flow_template.return_value = template_data

        # 执行测试
        workflow = create_workflow_from_template("test-workflow")

        # 验证结果
        assert workflow is not None
        assert workflow["id"] == test_uuid
        assert workflow["name"] == "测试工作流"
        assert workflow["source_template"] == "test-workflow"
        assert workflow["status"] == "active"
        assert len(workflow["stages"]) == 1
        assert len(workflow["transitions"]) == 1

    @mock.patch("src.workflow.template_loader.list_templates")
    @mock.patch("src.workflow.template_loader.load_flow_template")
    def test_get_available_templates(self, mock_load_flow_template, mock_list_templates):
        """测试获取可用模板列表"""
        # 配置模拟行为
        mock_list_templates.return_value = ["template1", "template2"]

        template1_data = {"id": "template1", "name": "模板1", "description": "第一个测试模板", "version": "1.0.0"}

        template2_data = {"id": "template2", "name": "模板2", "description": "第二个测试模板", "version": "1.1.0"}

        mock_load_flow_template.side_effect = lambda name: template1_data if name == "template1" else template2_data

        # 执行测试
        templates = get_available_templates()

        # 验证结果
        assert len(templates) == 2
        assert templates[0]["id"] == "template1"
        assert templates[0]["name"] == "模板1"
        assert templates[1]["id"] == "template2"
        assert templates[1]["name"] == "模板2"

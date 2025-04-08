#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流模板功能
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

from src.workflow.workflow_template import (
    create_workflow_from_template,
    create_workflow_template,
    delete_workflow_template,
    get_workflow_template,
    get_workflow_templates_directory,
    list_workflow_templates,
    update_workflow_template,
)


class TestWorkflowTemplates(unittest.TestCase):
    """测试工作流模板功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        os.makedirs(self.templates_dir, exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    @patch("src.workflow.workflow_template.get_config")
    def test_get_workflow_templates_directory(self, mock_get_config):
        """测试获取工作流模板目录"""
        mock_config = MagicMock()
        mock_config.get.return_value = self.temp_dir
        mock_get_config.return_value = mock_config

        expected_path = os.path.join(self.temp_dir, "workflow")
        result = get_workflow_templates_directory()

        self.assertEqual(result, expected_path)
        mock_get_config.assert_called_once()
        mock_config.get.assert_called_once_with("paths.templates_dir", "")

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.os.path.exists")
    @patch("src.workflow.workflow_template.os.listdir")
    def test_list_workflow_templates(self, mock_listdir, mock_exists, mock_get_dir):
        """测试列出工作流模板"""
        # 设置模拟返回值
        mock_get_dir.return_value = self.templates_dir
        mock_exists.return_value = True
        mock_listdir.return_value = ["template1.json", "template2.json", "not_a_template.txt"]

        # 创建测试模板文件
        template1 = {"id": "template1", "name": "Template 1", "description": "Template description 1"}
        template2 = {"id": "template2", "name": "Template 2", "description": "Template description 2"}

        with open(os.path.join(self.templates_dir, "template1.json"), "w") as f:
            json.dump(template1, f)
        with open(os.path.join(self.templates_dir, "template2.json"), "w") as f:
            json.dump(template2, f)

        with patch("src.workflow.workflow_template.read_json_file") as mock_read_json:
            mock_read_json.side_effect = lambda path: template1 if "template1" in path else template2

            templates = list_workflow_templates()

            self.assertEqual(len(templates), 2)
            self.assertEqual(templates[0], template1)
            self.assertEqual(templates[1], template2)

    @patch("src.workflow.workflow_template.list_workflow_templates")
    def test_get_workflow_template_by_id(self, mock_list_templates):
        """测试通过ID获取工作流模板"""
        templates = [{"id": "template1", "name": "Template 1"}, {"id": "template2", "name": "Template 2"}]
        mock_list_templates.return_value = templates

        # 测试找到模板
        template = get_workflow_template("template1")
        self.assertEqual(template, templates[0])

        # 测试未找到模板
        template = get_workflow_template("nonexistent")
        self.assertIsNone(template)

        mock_list_templates.assert_called()

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.ensure_directory_exists")
    @patch("src.workflow.workflow_template.uuid.uuid4")
    def test_create_workflow_template(self, mock_uuid, mock_ensure_dir, mock_get_dir):
        """测试创建工作流模板"""
        mock_get_dir.return_value = self.templates_dir
        mock_uuid.return_value = "test-uuid"

        template_data = {
            "name": "New Template",
            "description": "A new workflow template",
            "steps": [{"id": "step1", "type": "script", "name": "Step 1", "script": 'print("Hello")'}],
        }

        with patch("src.workflow.workflow_template.write_json_file") as mock_write_json:
            result = create_workflow_template(template_data)

            # 验证结果
            self.assertEqual(result["id"], "test-uuid")
            self.assertEqual(result["name"], "New Template")
            self.assertEqual(result["description"], "A new workflow template")
            self.assertEqual(len(result["steps"]), 1)

            # 验证调用
            mock_ensure_dir.assert_called_once_with(self.templates_dir)
            mock_write_json.assert_called_once()
            # 检查文件路径
            file_path = mock_write_json.call_args[0][0]
            expected_path = os.path.join(self.templates_dir, "test-uuid.json")
            self.assertEqual(file_path, expected_path)

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.os.path.exists")
    def test_update_workflow_template(self, mock_exists, mock_get_dir):
        """测试更新工作流模板"""
        mock_get_dir.return_value = self.templates_dir
        mock_exists.return_value = True

        template_id = "template-id"
        template_data = {
            "id": template_id,
            "name": "Updated Template",
            "description": "An updated workflow template",
            "steps": [{"id": "step1", "type": "script", "name": "Updated Step 1", "script": 'print("Updated")'}],
        }

        with patch("src.workflow.workflow_template.write_json_file") as mock_write_json:
            result = update_workflow_template(template_id, template_data)

            # 验证结果
            self.assertTrue(result["success"])
            self.assertEqual(result["template_id"], template_id)

            # 验证调用
            mock_write_json.assert_called_once()
            # 检查文件路径
            file_path = mock_write_json.call_args[0][0]
            expected_path = os.path.join(self.templates_dir, f"{template_id}.json")
            self.assertEqual(file_path, expected_path)

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.os.path.exists")
    def test_update_workflow_template_not_found(self, mock_exists, mock_get_dir):
        """测试更新不存在的工作流模板"""
        mock_get_dir.return_value = self.templates_dir
        mock_exists.return_value = False

        template_id = "nonexistent"
        template_data = {"id": template_id, "name": "Nonexistent Template"}

        result = update_workflow_template(template_id, template_data)

        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Template not found")

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.os.path.exists")
    @patch("src.workflow.workflow_template.os.remove")
    def test_delete_workflow_template(self, mock_remove, mock_exists, mock_get_dir):
        """测试删除工作流模板"""
        mock_get_dir.return_value = self.templates_dir
        mock_exists.return_value = True

        template_id = "template-to-delete"

        result = delete_workflow_template(template_id)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["template_id"], template_id)

        # 验证调用
        expected_path = os.path.join(self.templates_dir, f"{template_id}.json")
        mock_exists.assert_called_once_with(expected_path)
        mock_remove.assert_called_once_with(expected_path)

    @patch("src.workflow.workflow_template.get_workflow_templates_directory")
    @patch("src.workflow.workflow_template.os.path.exists")
    def test_delete_workflow_template_not_found(self, mock_exists, mock_get_dir):
        """测试删除不存在的工作流模板"""
        mock_get_dir.return_value = self.templates_dir
        mock_exists.return_value = False

        template_id = "nonexistent"

        result = delete_workflow_template(template_id)

        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Template not found")

    @patch("src.workflow.workflow_template.get_workflow_template")
    @patch("src.workflow.workflow_template.create_workflow")
    def test_create_workflow_from_template(self, mock_create_workflow, mock_get_template):
        """测试从模板创建工作流"""
        # 模拟模板
        template = {
            "id": "template-id",
            "name": "Template Name",
            "description": "Template Description",
            "steps": [{"id": "step1", "type": "script", "name": "Step 1", "script": 'print("Hello")'}],
        }
        mock_get_template.return_value = template

        # 模拟创建工作流的结果
        created_workflow = {"id": "new-workflow-id", "name": "New Workflow", "description": "Based on Template", "steps": template["steps"]}
        mock_create_workflow.return_value = created_workflow

        # 调用测试函数
        workflow_data = {"name": "New Workflow", "description": "Based on Template"}
        result = create_workflow_from_template("template-id", workflow_data)

        # 验证结果
        self.assertEqual(result, created_workflow)

        # 验证调用
        mock_get_template.assert_called_once_with("template-id")
        expected_data = {"name": "New Workflow", "description": "Based on Template", "steps": template["steps"], "template_id": "template-id"}
        mock_create_workflow.assert_called_once_with(expected_data)

    @patch("src.workflow.workflow_template.get_workflow_template")
    def test_create_workflow_from_template_not_found(self, mock_get_template):
        """测试从不存在的模板创建工作流"""
        mock_get_template.return_value = None

        workflow_data = {"name": "New Workflow"}
        result = create_workflow_from_template("nonexistent", workflow_data)

        self.assertIsNone(result)
        mock_get_template.assert_called_once_with("nonexistent")


if __name__ == "__main__":
    unittest.main()

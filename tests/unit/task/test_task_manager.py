#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task管理器单元测试
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.db.specific_managers.task_manager import TaskManager
from src.models.db.task import Task, TaskComment


class TestTaskManager(unittest.TestCase):
    """测试Task管理器"""

    def setUp(self):
        """测试前准备"""
        self.mock_entity_manager = MagicMock()
        self.mock_task_repo = MagicMock()
        self.manager = TaskManager(self.mock_entity_manager, self.mock_task_repo)

    def test_get_task(self):
        """测试获取任务"""
        # 设置模拟数据
        mock_task = {
            "id": "task_12345678",
            "title": "测试任务",
            "description": "这是一个测试任务",
            "status": "todo",
            "priority": "medium",
            "estimated_hours": 2,
            "is_completed": False,
            "assignee": "test_user",
            "labels": ["test", "unit"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.mock_entity_manager.get_entity.return_value = mock_task

        # 执行测试
        task = self.manager.get_task("task_12345678")

        # 验证结果
        self.assertEqual(task["id"], "task_12345678")
        self.assertEqual(task["title"], "测试任务")
        self.assertEqual(task["status"], "todo")
        self.mock_entity_manager.get_entity.assert_called_once_with("task", "task_12345678")

    def test_list_tasks(self):
        """测试获取任务列表"""
        # 设置模拟数据
        mock_tasks = [{"id": "task_12345678", "title": "测试任务1", "status": "todo"}, {"id": "task_87654321", "title": "测试任务2", "status": "in_progress"}]
        self.mock_entity_manager.get_entities.return_value = mock_tasks

        # 执行测试
        tasks = self.manager.list_tasks()

        # 验证结果
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["id"], "task_12345678")
        self.assertEqual(tasks[1]["id"], "task_87654321")
        self.mock_entity_manager.get_entities.assert_called_once_with("task")

    def test_create_task(self):
        """测试创建任务"""
        # 设置模拟数据
        task_data = {
            "title": "新测试任务",
            "description": "这是一个新的测试任务",
            "status": "todo",
            "priority": "high",
            "estimated_hours": 4,
            "assignee": "test_user",
        }
        mock_created_task = {
            **task_data,
            "id": "task_12345678",
            "is_completed": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.mock_entity_manager.create_entity.return_value = mock_created_task

        # 执行测试
        task = self.manager.create_task(task_data)

        # 验证结果
        self.assertEqual(task["title"], "新测试任务")
        self.assertEqual(task["status"], "todo")
        self.assertEqual(task["priority"], "high")
        self.mock_entity_manager.create_entity.assert_called_once_with("task", task_data)

    def test_update_task(self):
        """测试更新任务"""
        # 设置模拟数据
        update_data = {"status": "in_progress", "priority": "high", "estimated_hours": 6}
        mock_updated_task = {
            "id": "task_12345678",
            "title": "测试任务",
            "description": "这是一个测试任务",
            **update_data,
            "updated_at": datetime.now().isoformat(),
        }
        self.mock_entity_manager.update_entity.return_value = mock_updated_task

        # 执行测试
        task = self.manager.update_task("task_12345678", update_data)

        # 验证结果
        self.assertEqual(task["status"], "in_progress")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["estimated_hours"], 6)
        self.mock_entity_manager.update_entity.assert_called_once_with("task", "task_12345678", update_data)

    def test_delete_task(self):
        """测试删除任务"""
        # 设置模拟数据
        self.mock_entity_manager.delete_entity.return_value = True

        # 执行测试
        result = self.manager.delete_task("task_12345678")

        # 验证结果
        self.assertTrue(result)
        self.mock_entity_manager.delete_entity.assert_called_once_with("task", "task_12345678")

    def test_get_tasks_by_status(self):
        """测试根据状态获取任务"""
        # 设置模拟数据
        mock_tasks = [Task(id="task_1", title="任务1", status="in_progress"), Task(id="task_2", title="任务2", status="in_progress")]
        self.mock_task_repo.get_by_status.return_value = mock_tasks

        # 执行测试
        tasks = self.manager.get_tasks_by_status("in_progress")

        # 验证结果
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["id"], "task_1")
        self.assertEqual(tasks[0]["status"], "in_progress")
        self.mock_task_repo.get_by_status.assert_called_once_with("in_progress")

    def test_get_tasks_by_assignee(self):
        """测试根据分配人获取任务"""
        # 设置模拟数据
        mock_tasks = [Task(id="task_1", title="任务1", assignee="test_user"), Task(id="task_2", title="任务2", assignee="test_user")]
        self.mock_task_repo.get_by_assignee.return_value = mock_tasks

        # 执行测试
        tasks = self.manager.get_tasks_by_assignee("test_user")

        # 验证结果
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["id"], "task_1")
        self.assertEqual(tasks[0]["assignee"], "test_user")
        self.mock_task_repo.get_by_assignee.assert_called_once_with("test_user")


if __name__ == "__main__":
    unittest.main()

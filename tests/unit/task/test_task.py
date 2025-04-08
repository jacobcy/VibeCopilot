#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task模型单元测试
"""

import unittest
from datetime import datetime

from src.models.db.task import Task


class TestTask(unittest.TestCase):
    """测试Task模型"""

    def test_create_task(self):
        """测试创建任务"""
        # 创建任务
        task = Task(
            title="测试任务", description="这是一个测试任务", status="todo", priority="high", estimated_hours=4, assignee="test_user", labels=["test", "unit"]
        )

        # 验证基本属性
        self.assertTrue(task.id.startswith("task_"))
        self.assertEqual(task.title, "测试任务")
        self.assertEqual(task.description, "这是一个测试任务")
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.estimated_hours, 4)
        self.assertEqual(task.assignee, "test_user")
        self.assertEqual(task.labels, ["test", "unit"])
        self.assertFalse(task.is_completed)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        self.assertIsNone(task.completed_at)

    def test_create_task_with_id(self):
        """测试使用指定ID创建任务"""
        task_id = "task_12345678"
        task = Task(id=task_id, title="测试任务", description="这是一个测试任务")
        self.assertEqual(task.id, task_id)

    def test_task_to_dict(self):
        """测试任务转换为字典"""
        # 创建任务
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()
        task = Task(
            id="task_12345678",
            title="测试任务",
            description="这是一个测试任务",
            status="in_progress",
            priority="high",
            estimated_hours=4,
            is_completed=False,
            assignee="test_user",
            labels=["test", "unit"],
            created_at=created_at,
            updated_at=updated_at,
        )

        # 转换为字典
        task_dict = task.to_dict()

        # 验证字典内容
        self.assertEqual(task_dict["id"], "task_12345678")
        self.assertEqual(task_dict["title"], "测试任务")
        self.assertEqual(task_dict["description"], "这是一个测试任务")
        self.assertEqual(task_dict["status"], "in_progress")
        self.assertEqual(task_dict["priority"], "high")
        self.assertEqual(task_dict["estimated_hours"], 4)
        self.assertEqual(task_dict["is_completed"], False)
        self.assertEqual(task_dict["assignee"], "test_user")
        self.assertEqual(task_dict["labels"], ["test", "unit"])
        self.assertEqual(task_dict["created_at"], created_at)
        self.assertEqual(task_dict["updated_at"], updated_at)
        self.assertIsNone(task_dict["completed_at"])

    def test_task_representation(self):
        """测试任务的字符串表示"""
        task = Task(id="task_12345678", title="测试任务", status="todo")
        expected_repr = "<Task(id='task_12345678', title='测试任务', status='todo')>"
        self.assertEqual(repr(task), expected_repr)

    def test_task_defaults(self):
        """测试任务的默认值"""
        task = Task(title="测试任务")  # 只提供必需的title字段

        # 验证默认值
        self.assertTrue(task.id.startswith("task_"))
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.priority, "medium")
        self.assertEqual(task.estimated_hours, 0)
        self.assertFalse(task.is_completed)
        self.assertIsNone(task.story_id)
        self.assertIsNone(task.assignee)
        self.assertIsNone(task.labels)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        self.assertIsNone(task.completed_at)

    def test_task_update_timestamps(self):
        """测试任务时间戳的更新"""
        # 创建任务时的时间戳
        initial_created_at = datetime.now().isoformat()
        initial_updated_at = initial_created_at

        task = Task(title="测试任务", created_at=initial_created_at, updated_at=initial_updated_at)

        # 验证初始时间戳
        self.assertEqual(task.created_at, initial_created_at)
        self.assertEqual(task.updated_at, initial_updated_at)

        # 更新任务
        new_updated_at = datetime.now().isoformat()
        task.updated_at = new_updated_at

        # 验证更新后的时间戳
        self.assertEqual(task.created_at, initial_created_at)  # created_at 不应改变
        self.assertEqual(task.updated_at, new_updated_at)  # updated_at 应该更新


if __name__ == "__main__":
    unittest.main()

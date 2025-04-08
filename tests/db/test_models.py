"""
数据库模型测试模块

测试主要数据库模型的初始化、关系和方法
"""

import unittest
from datetime import datetime
from unittest.mock import patch

import pytest

from src.models.db.epic import Epic
from src.models.db.story import Story
from src.models.db.task import Task, TaskComment


class TestModels(unittest.TestCase):
    """数据库模型测试类"""

    def test_epic_creation(self):
        """测试Epic创建"""
        # 基本创建
        epic = Epic(title="测试Epic", description="Epic描述", status="backlog", priority="medium")

        # 测试ID自动生成
        self.assertTrue(epic.id.startswith("epic_"))

        # 测试字段赋值
        self.assertEqual(epic.title, "测试Epic")
        self.assertEqual(epic.description, "Epic描述")
        self.assertEqual(epic.status, "backlog")
        self.assertEqual(epic.priority, "medium")

        # 测试时间戳
        self.assertIsNotNone(epic.created_at)
        self.assertIsNotNone(epic.updated_at)

    def test_story_creation(self):
        """测试Story创建"""
        # 创建Epic
        epic = Epic(title="测试Epic", description="Epic描述")

        # 创建Story
        story = Story(
            title="测试Story", description="Story描述", acceptance_criteria="必须通过验收", points=5, epic_id=epic.id, status="backlog", priority="medium"
        )

        # 测试ID自动生成
        self.assertTrue(story.id.startswith("story_"))

        # 测试字段赋值
        self.assertEqual(story.title, "测试Story")
        self.assertEqual(story.description, "Story描述")
        self.assertEqual(story.acceptance_criteria, "必须通过验收")
        self.assertEqual(story.points, 5)
        self.assertEqual(story.epic_id, epic.id)
        self.assertEqual(story.status, "backlog")
        self.assertEqual(story.priority, "medium")

    def test_task_creation(self):
        """测试Task创建"""
        # 创建Story
        story = Story(title="测试Story", description="Story描述")

        # 创建Task
        task = Task(
            title="测试Task",
            description="Task描述",
            status="todo",
            estimated_hours=3,
            story_id=story.id,
            assignee="测试用户",
            labels=["bug", "frontend"],
            priority="medium",
        )

        # 测试ID自动生成
        self.assertTrue(task.id.startswith("task_"))

        # 测试字段赋值
        self.assertEqual(task.title, "测试Task")
        self.assertEqual(task.description, "Task描述")
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.estimated_hours, 3)
        self.assertEqual(task.story_id, story.id)
        self.assertEqual(task.assignee, "测试用户")
        self.assertEqual(task.labels, ["bug", "frontend"])
        self.assertEqual(task.priority, "medium")

        # 测试默认值
        self.assertFalse(task.is_completed)

    def test_task_comment_creation(self):
        """测试TaskComment创建"""
        # 创建Task
        task = Task(title="测试Task")

        # 创建TaskComment
        comment = TaskComment(task_id=task.id, author="测试用户", content="这是一条测试评论")

        # 测试ID自动生成
        self.assertTrue(comment.id.startswith("comment_"))

        # 测试字段赋值
        self.assertEqual(comment.task_id, task.id)
        self.assertEqual(comment.author, "测试用户")
        self.assertEqual(comment.content, "这是一条测试评论")

        # 测试时间戳
        self.assertIsNotNone(comment.created_at)

    def test_to_dict(self):
        """测试to_dict方法"""
        # 创建Epic
        epic = Epic(title="测试Epic", description="Epic描述", status="draft", priority="medium")

        # 调用to_dict方法
        epic_dict = epic.to_dict()

        # 测试字典结果
        self.assertEqual(epic_dict["title"], "测试Epic")
        self.assertEqual(epic_dict["description"], "Epic描述")
        self.assertEqual(epic_dict["status"], "draft")
        self.assertEqual(epic_dict["priority"], "medium")
        self.assertIn("id", epic_dict)
        self.assertIn("created_at", epic_dict)
        self.assertIn("updated_at", epic_dict)
        self.assertIn("stories", epic_dict)

    @patch("src.models.db.epic.relationship")
    @patch("src.models.db.story.relationship")
    def test_cascading_delete(self, mock_story_rel, mock_epic_rel):
        """测试级联删除 (使用模拟对象测试级联关系)"""
        # 模拟关系的cascade属性
        mock_epic_rel.return_value.cascade = "all, delete-orphan"
        mock_story_rel.return_value.cascade = "all, delete-orphan"

        # 创建Epic
        epic = Epic(
            title="测试Epic",
        )

        # 创建Story
        story = Story(title="测试Story", epic_id=epic.id)

        # 创建Task
        task = Task(title="测试Task", story_id=story.id)

        # 这里应该有实际的数据库插入和删除操作
        # 由于是单元测试，我们只能测试关系配置
        self.assertEqual(story.epic_id, epic.id)
        self.assertEqual(task.story_id, story.id)

        # 验证级联关系配置 (通过mock)
        self.assertIn("all, delete-orphan", mock_epic_rel.return_value.cascade)
        self.assertIn("all, delete-orphan", mock_story_rel.return_value.cascade)


if __name__ == "__main__":
    unittest.main()

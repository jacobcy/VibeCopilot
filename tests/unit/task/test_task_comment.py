#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task评论单元测试
"""

import unittest
from datetime import datetime

from src.models.db.task import Task, TaskComment


class TestTaskComment(unittest.TestCase):
    """测试Task评论"""

    def setUp(self):
        """测试前准备"""
        self.task = Task(id="task_12345678", title="测试任务", description="这是一个测试任务", status="todo")

    def test_create_comment(self):
        """测试创建评论"""
        # 创建评论
        comment = TaskComment(task_id=self.task.id, author="test_user", content="这是一条测试评论")

        # 验证评论属性
        self.assertTrue(comment.id.startswith("comment_"))
        self.assertEqual(comment.task_id, "task_12345678")
        self.assertEqual(comment.author, "test_user")
        self.assertEqual(comment.content, "这是一条测试评论")
        self.assertIsNotNone(comment.created_at)

    def test_comment_to_dict(self):
        """测试评论转换为字典"""
        # 创建评论
        created_at = datetime.now().isoformat()
        comment = TaskComment(id="comment_12345678", task_id=self.task.id, author="test_user", content="这是一条测试评论", created_at=created_at)

        # 转换为字典
        comment_dict = comment.to_dict()

        # 验证字典内容
        self.assertEqual(comment_dict["id"], "comment_12345678")
        self.assertEqual(comment_dict["task_id"], self.task.id)
        self.assertEqual(comment_dict["author"], "test_user")
        self.assertEqual(comment_dict["content"], "这是一条测试评论")
        self.assertEqual(comment_dict["created_at"], created_at)

    def test_task_comments_relationship(self):
        """测试任务和评论的关系"""
        # 创建评论
        comment1 = TaskComment(task_id=self.task.id, author="test_user1", content="评论1")
        comment2 = TaskComment(task_id=self.task.id, author="test_user2", content="评论2")

        # 添加评论到任务
        self.task.comments.append(comment1)
        self.task.comments.append(comment2)

        # 验证关系
        self.assertEqual(len(self.task.comments), 2)
        self.assertEqual(self.task.comments[0].content, "评论1")
        self.assertEqual(self.task.comments[1].content, "评论2")
        self.assertEqual(comment1.task, self.task)
        self.assertEqual(comment2.task, self.task)


if __name__ == "__main__":
    unittest.main()

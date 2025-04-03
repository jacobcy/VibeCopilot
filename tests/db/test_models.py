"""
测试数据库模型

验证数据模型定义、关系以及转换功能
"""

import os
import tempfile
import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Epic, Label, Story, Task, task_label_association


class TestModels(unittest.TestCase):
    """测试数据库模型类"""

    def setUp(self):
        """创建临时数据库和会话"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # 连接数据库
        self.engine = create_engine(f"sqlite:///{self.temp_db.name}")

        # 创建表
        Base.metadata.create_all(self.engine)

        # 创建会话
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        """清理临时数据库"""
        self.session.close()
        os.unlink(self.temp_db.name)

    def test_epic_creation(self):
        """测试创建Epic"""
        # 创建Epic
        epic = Epic(id="E1001", name="测试Epic", description="Epic描述", status="backlog")

        # 添加到会话并提交
        self.session.add(epic)
        self.session.commit()

        # 查询
        saved_epic = self.session.query(Epic).filter_by(id="E1001").first()

        # 断言
        self.assertIsNotNone(saved_epic)
        self.assertEqual(saved_epic.name, "测试Epic")
        self.assertEqual(saved_epic.description, "Epic描述")
        self.assertEqual(saved_epic.status, "backlog")

    def test_story_creation(self):
        """测试创建Story和与Epic的关联"""
        # 创建Epic
        epic = Epic(id="E1001", name="测试Epic")

        # 创建Story并关联Epic
        story = Story(
            id="S1001", name="测试Story", description="Story描述", status="backlog", epic_id="E1001"
        )

        # 添加到会话并提交
        self.session.add(epic)
        self.session.add(story)
        self.session.commit()

        # 查询
        saved_story = self.session.query(Story).filter_by(id="S1001").first()

        # 断言
        self.assertIsNotNone(saved_story)
        self.assertEqual(saved_story.name, "测试Story")
        self.assertEqual(saved_story.epic_id, "E1001")
        self.assertEqual(saved_story.epic.name, "测试Epic")

    def test_task_creation(self):
        """测试创建Task和与Story的关联"""
        # 创建Story
        story = Story(id="S1001", name="测试Story")

        # 创建Task并关联Story
        task = Task(
            id="T1001", name="测试Task", description="Task描述", status="todo", story_id="S1001"
        )

        # 添加到会话并提交
        self.session.add(story)
        self.session.add(task)
        self.session.commit()

        # 查询
        saved_task = self.session.query(Task).filter_by(id="T1001").first()

        # 断言
        self.assertIsNotNone(saved_task)
        self.assertEqual(saved_task.name, "测试Task")
        self.assertEqual(saved_task.story_id, "S1001")
        self.assertEqual(saved_task.story.name, "测试Story")

    def test_label_association(self):
        """测试Task和Label的多对多关联"""
        # 创建Labels
        label1 = Label(id="L1001", name="Bug")
        label2 = Label(id="L1002", name="Feature")

        # 创建Task
        task = Task(id="T1001", name="测试Task")

        # 关联Labels
        task.labels.append(label1)
        task.labels.append(label2)

        # 添加到会话并提交
        self.session.add_all([label1, label2, task])
        self.session.commit()

        # 查询
        saved_task = self.session.query(Task).filter_by(id="T1001").first()

        # 断言
        self.assertIsNotNone(saved_task)
        self.assertEqual(len(saved_task.labels), 2)
        self.assertEqual(saved_task.labels[0].name, "Bug")
        self.assertEqual(saved_task.labels[1].name, "Feature")

    def test_cascading_delete(self):
        """测试级联删除"""
        # 创建数据
        epic = Epic(id="E1001", name="测试Epic")
        story = Story(id="S1001", name="测试Story", epic_id="E1001")
        task = Task(id="T1001", name="测试Task", story_id="S1001")

        # 添加到会话并提交
        self.session.add_all([epic, story, task])
        self.session.commit()

        # 删除Epic
        self.session.delete(epic)
        self.session.commit()

        # 查询
        saved_story = self.session.query(Story).filter_by(id="S1001").first()
        saved_task = self.session.query(Task).filter_by(id="T1001").first()

        # 断言 (级联删除应该删除了相关Story和Task)
        self.assertIsNone(saved_story)
        self.assertIsNone(saved_task)

    def test_to_dict(self):
        """测试to_dict方法"""
        # 创建数据
        epic = Epic(id="E1001", name="测试Epic", description="Epic描述")

        # 转换为字典
        epic_dict = epic.to_dict()

        # 断言
        self.assertEqual(epic_dict["id"], "E1001")
        self.assertEqual(epic_dict["name"], "测试Epic")
        self.assertEqual(epic_dict["description"], "Epic描述")

    def test_from_dict(self):
        """测试from_dict方法"""
        # 创建字典
        data = {"id": "E1001", "name": "测试Epic", "description": "Epic描述", "status": "in_progress"}

        # 从字典创建Epic
        epic = Epic.from_dict(data)

        # 断言
        self.assertEqual(epic.id, "E1001")
        self.assertEqual(epic.name, "测试Epic")
        self.assertEqual(epic.description, "Epic描述")
        self.assertEqual(epic.status, "in_progress")


if __name__ == "__main__":
    unittest.main()

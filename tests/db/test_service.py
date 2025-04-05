"""
测试数据库服务

验证数据库服务的各种操作，包括CRUD和查询功能
"""

import json
import os
import tempfile
import unittest
from datetime import datetime

from src.db.service import DatabaseService
from src.models.db import Epic, Label, Story, Task


class TestDatabaseService(unittest.TestCase):
    """测试数据库服务类"""

    def setUp(self):
        """创建临时数据库和服务实例"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # 创建数据库服务
        self.db_service = DatabaseService(self.temp_db.name)

    def tearDown(self):
        """清理临时数据库"""
        os.unlink(self.temp_db.name)

    def test_epic_crud(self):
        """测试Epic的CRUD操作"""
        # 创建Epic
        epic_data = {"name": "测试Epic", "description": "Epic描述", "status": "backlog"}
        epic = self.db_service.create_epic(epic_data)

        # 获取Epic
        retrieved_epic = self.db_service.get_epic(epic.id)

        # 断言
        self.assertIsNotNone(retrieved_epic)
        self.assertEqual(retrieved_epic.name, "测试Epic")

        # 更新Epic
        update_data = {"status": "in_progress"}
        updated_epic = self.db_service.update_epic(epic.id, update_data)

        # 断言
        self.assertEqual(updated_epic.status, "in_progress")

        # 删除Epic
        success = self.db_service.delete_epic(epic.id)

        # 断言
        self.assertTrue(success)
        self.assertIsNone(self.db_service.get_epic(epic.id))

    def test_story_crud(self):
        """测试Story的CRUD操作"""
        # 创建Epic
        epic_data = {"name": "测试Epic"}
        epic = self.db_service.create_epic(epic_data)

        # 创建Story
        story_data = {
            "name": "测试Story",
            "description": "Story描述",
            "status": "backlog",
            "epic_id": epic.id,
        }
        story = self.db_service.create_story(story_data)

        # 获取Story
        retrieved_story = self.db_service.get_story(story.id)

        # 断言
        self.assertIsNotNone(retrieved_story)
        self.assertEqual(retrieved_story.name, "测试Story")
        self.assertEqual(retrieved_story.epic_id, epic.id)

        # 更新Story
        update_data = {"status": "in_progress"}
        updated_story = self.db_service.update_story(story.id, update_data)

        # 断言
        self.assertEqual(updated_story.status, "in_progress")

        # 删除Story
        success = self.db_service.delete_story(story.id)

        # 断言
        self.assertTrue(success)
        self.assertIsNone(self.db_service.get_story(story.id))

    def test_task_crud(self):
        """测试Task的CRUD操作"""
        # 创建Story
        story_data = {"name": "测试Story"}
        story = self.db_service.create_story(story_data)

        # 创建Label
        label_data = {"name": "Bug"}
        label = self.db_service.create_label(label_data)

        # 创建Task
        task_data = {
            "name": "测试Task",
            "description": "Task描述",
            "status": "todo",
            "story_id": story.id,
        }
        task = self.db_service.create_task(task_data, [label.id])

        # 获取Task
        retrieved_task = self.db_service.get_task(task.id)

        # 断言
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.name, "测试Task")
        self.assertEqual(retrieved_task.story_id, story.id)
        self.assertEqual(len(retrieved_task.labels), 1)
        self.assertEqual(retrieved_task.labels[0].name, "Bug")

        # 更新Task
        update_data = {"status": "in_progress"}
        updated_task = self.db_service.update_task(task.id, update_data)

        # 断言
        self.assertEqual(updated_task.status, "in_progress")

        # 删除Task
        success = self.db_service.delete_task(task.id)

        # 断言
        self.assertTrue(success)
        self.assertIsNone(self.db_service.get_task(task.id))

    def test_list_functions(self):
        """测试列表查询功能"""
        # 创建测试数据
        epic1 = self.db_service.create_epic({"name": "Epic 1"})
        epic2 = self.db_service.create_epic({"name": "Epic 2"})

        story1 = self.db_service.create_story({"name": "Story 1", "epic_id": epic1.id})
        story2 = self.db_service.create_story({"name": "Story 2", "epic_id": epic1.id})
        story3 = self.db_service.create_story({"name": "Story 3", "epic_id": epic2.id})

        task1 = self.db_service.create_task({"name": "Task 1", "story_id": story1.id})
        task2 = self.db_service.create_task({"name": "Task 2", "story_id": story1.id})
        task3 = self.db_service.create_task({"name": "Task 3", "story_id": story2.id})

        # 测试列出所有Epic
        epics = self.db_service.list_epics()
        self.assertEqual(len(epics), 2)

        # 测试列出特定Epic的Story
        stories = self.db_service.list_stories({"epic_id": epic1.id})
        self.assertEqual(len(stories), 2)

        # 测试列出特定Story的Task
        tasks = self.db_service.list_tasks({"story_id": story1.id})
        self.assertEqual(len(tasks), 2)

    def test_progress_statistics(self):
        """测试进度统计功能"""
        # 创建测试数据
        epic = self.db_service.create_epic({"name": "Epic"})
        story = self.db_service.create_story({"name": "Story", "epic_id": epic.id})

        # 创建4个任务，2个完成，1个进行中，1个待办
        self.db_service.create_task({"name": "Task 1", "story_id": story.id, "status": "done"})
        self.db_service.create_task({"name": "Task 2", "story_id": story.id, "status": "done"})
        self.db_service.create_task(
            {"name": "Task 3", "story_id": story.id, "status": "in_progress"}
        )
        self.db_service.create_task({"name": "Task 4", "story_id": story.id, "status": "todo"})

        # 测试Story进度
        progress = self.db_service.get_story_progress(story.id)
        self.assertEqual(progress["total"], 4)
        self.assertEqual(progress["done"], 2)
        self.assertEqual(progress["in_progress"], 1)
        self.assertEqual(progress["percent_complete"], 50.0)

        # 测试Epic进度
        progress = self.db_service.get_epic_progress(epic.id)
        self.assertEqual(progress["total"], 4)
        self.assertEqual(progress["done"], 2)
        self.assertEqual(progress["in_progress"], 1)
        self.assertEqual(progress["percent_complete"], 50.0)

    def test_yaml_import_export(self):
        """测试YAML导入导出功能"""
        # 准备YAML数据
        yaml_data = {
            "milestones": [
                {
                    "name": "里程碑1",
                    "description": "描述1",
                    "tasks": [
                        {"name": "任务1", "description": "任务描述1"},
                        {"name": "任务2", "description": "任务描述2"},
                    ],
                },
                {
                    "name": "里程碑2",
                    "description": "描述2",
                    "tasks": [{"name": "任务3", "description": "任务描述3"}],
                },
            ]
        }

        # 创建临时YAML文件
        temp_yaml = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
        temp_yaml.close()

        # 写入YAML数据
        with open(temp_yaml.name, "w") as f:
            import yaml

            yaml.dump(yaml_data, f)

        try:
            # 导入YAML
            self.db_service.import_from_yaml(temp_yaml.name)

            # 验证导入结果
            epics = self.db_service.list_epics()
            self.assertEqual(len(epics), 2)

            stories = self.db_service.list_stories()
            self.assertEqual(len(stories), 3)  # 每个任务一个Story

            tasks = self.db_service.list_tasks()
            self.assertEqual(len(tasks), 3)

            # 导出到新YAML
            export_yaml = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
            export_yaml.close()

            self.db_service.export_to_yaml(export_yaml.name)

            # 验证导出结果
            with open(export_yaml.name, "r") as f:
                exported_data = yaml.safe_load(f)

            self.assertIsNotNone(exported_data)
            self.assertIn("milestones", exported_data)
            self.assertEqual(len(exported_data["milestones"]), 2)

            # 清理导出文件
            os.unlink(export_yaml.name)

        finally:
            # 清理YAML文件
            os.unlink(temp_yaml.name)


if __name__ == "__main__":
    unittest.main()

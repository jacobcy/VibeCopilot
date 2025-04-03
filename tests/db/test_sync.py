"""
测试数据同步功能

验证数据库与文件系统之间的同步操作
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from src.db.service import DatabaseService
from src.db.sync import DataSynchronizer


class TestDataSynchronizer(unittest.TestCase):
    """测试数据同步类"""

    def setUp(self):
        """创建临时数据库、目录和同步器实例"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.temp_dir, "stories")
        self.tasks_dir = os.path.join(self.temp_dir, "tasks")
        os.makedirs(self.stories_dir)
        os.makedirs(self.tasks_dir)

        # 创建数据库服务
        self.db_service = DatabaseService(self.temp_db.name)

        # 创建同步器
        self.synchronizer = DataSynchronizer(self.db_service)

        # 设置临时目录
        self.synchronizer.stories_dir = self.stories_dir
        self.synchronizer.tasks_dir = self.tasks_dir

    def tearDown(self):
        """清理临时文件和目录"""
        os.unlink(self.temp_db.name)
        shutil.rmtree(self.temp_dir)

    def test_sync_task_to_filesystem(self):
        """测试将任务同步到文件系统"""
        # 创建Story和Task
        story = self.db_service.create_story({"name": "测试Story", "description": "Story描述"})

        task = self.db_service.create_task(
            {"name": "测试Task", "description": "Task描述", "status": "todo", "story_id": story.id}
        )

        # 同步Task到文件系统
        task_path = self.synchronizer.sync_task_to_filesystem(task.id)

        # 断言
        self.assertTrue(os.path.exists(task_path))

        # 读取文件内容
        with open(task_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 验证内容
        self.assertIn("---", content)  # 验证有YAML前置数据
        self.assertIn("id: " + task.id, content)  # 验证ID
        self.assertIn("Task描述", content)  # 验证描述

    def test_sync_story_to_filesystem(self):
        """测试将故事同步到文件系统"""
        # 创建Story
        story = self.db_service.create_story(
            {"name": "测试Story", "description": "Story描述", "status": "backlog"}
        )

        # 同步Story到文件系统
        story_path = self.synchronizer.sync_story_to_filesystem(story.id)

        # 断言
        self.assertTrue(os.path.exists(story_path))

        # 读取文件内容
        with open(story_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 验证内容
        self.assertIn("---", content)  # 验证有YAML前置数据
        self.assertIn("id: " + story.id, content)  # 验证ID
        self.assertIn("Story描述", content)  # 验证描述

    def test_sync_all_to_filesystem(self):
        """测试将所有数据同步到文件系统"""
        # 创建Epic, Story和Task
        epic = self.db_service.create_epic({"name": "测试Epic"})

        story = self.db_service.create_story({"name": "测试Story", "epic_id": epic.id})

        task1 = self.db_service.create_task({"name": "测试Task 1", "story_id": story.id})

        task2 = self.db_service.create_task({"name": "测试Task 2", "story_id": story.id})

        # 同步所有数据
        story_count, task_count = self.synchronizer.sync_all_to_filesystem()

        # 断言
        self.assertEqual(story_count, 1)
        self.assertEqual(task_count, 2)

        # 验证文件是否创建
        story_files = os.listdir(self.stories_dir)
        task_files = os.listdir(self.tasks_dir)

        self.assertEqual(len(story_files), 1)
        self.assertEqual(len(task_files), 2)

    def test_sync_task_from_filesystem(self):
        """测试从文件系统同步任务数据"""
        # 创建Story
        story = self.db_service.create_story({"name": "测试Story"})

        # 创建Task
        task = self.db_service.create_task(
            {"name": "测试Task", "description": "初始描述", "story_id": story.id}
        )

        # 同步Task到文件系统
        task_path = self.synchronizer.sync_task_to_filesystem(task.id)

        # 修改文件内容
        with open(task_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 替换描述
        content = content.replace("初始描述", "修改后的描述")

        with open(task_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 从文件系统同步回数据库
        updated_task = self.synchronizer.sync_task_from_filesystem(task_path)

        # 断言
        self.assertEqual(updated_task.id, task.id)
        self.assertEqual(updated_task.description, "修改后的描述")

    def test_sync_from_roadmap_yaml(self):
        """测试从YAML文件同步数据"""
        # 准备YAML数据
        yaml_content = """
milestones:
  - name: 里程碑1
    description: 描述1
    tasks:
      - name: 任务1
        description: 任务描述1
      - name: 任务2
        description: 任务描述2
  - name: 里程碑2
    description: 描述2
    tasks:
      - name: 任务3
        description: 任务描述3
"""

        # 创建临时YAML文件
        yaml_file = os.path.join(self.temp_dir, "roadmap.yaml")
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 从YAML同步数据
        epic_count, story_count, task_count = self.synchronizer.sync_from_roadmap_yaml(yaml_file)

        # 断言
        self.assertEqual(epic_count, 2)  # 两个里程碑
        self.assertEqual(story_count, 3)  # 总共三个任务，每个创建一个Story
        self.assertEqual(task_count, 3)  # 三个任务

        # 验证数据库数据
        epics = self.db_service.list_epics()
        stories = self.db_service.list_stories()
        tasks = self.db_service.list_tasks()

        self.assertEqual(len(epics), 2)
        self.assertEqual(len(stories), 3)
        self.assertEqual(len(tasks), 3)

    def test_sync_to_roadmap_yaml(self):
        """测试同步数据到YAML文件"""
        # 创建测试数据
        epic1 = self.db_service.create_epic({"name": "Epic 1", "description": "Epic 描述1"})

        epic2 = self.db_service.create_epic({"name": "Epic 2", "description": "Epic 描述2"})

        story1 = self.db_service.create_story({"name": "Story 1", "epic_id": epic1.id})

        task1 = self.db_service.create_task({"name": "Task 1", "story_id": story1.id})

        # 同步到YAML
        yaml_file = os.path.join(self.temp_dir, "output.yaml")
        self.synchronizer.sync_to_roadmap_yaml(yaml_file)

        # 验证YAML文件是否创建
        self.assertTrue(os.path.exists(yaml_file))

        # 读取YAML内容
        with open(yaml_file, "r", encoding="utf-8") as f:
            import yaml

            yaml_data = yaml.safe_load(f)

        # 断言
        self.assertIn("milestones", yaml_data)
        self.assertEqual(len(yaml_data["milestones"]), 2)  # 两个Epic

        # 验证第一个里程碑的任务
        milestone1 = yaml_data["milestones"][0]
        self.assertEqual(milestone1["name"], "Epic 1")
        self.assertEqual(len(milestone1["tasks"]), 1)  # 一个任务


if __name__ == "__main__":
    unittest.main()

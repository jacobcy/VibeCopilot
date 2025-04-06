"""
基本导入测试模块

测试项目核心模块的导入是否正常，确保项目结构完整。
"""

import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestBasicImports(unittest.TestCase):
    """基本导入测试"""

    def test_import_roadmap_modules(self):
        """测试导入路线图模块"""
        try:
            from src.roadmap.core import RoadmapManager, RoadmapStatus, RoadmapUpdater
            from src.roadmap.service import RoadmapService

            self.assertTrue(True, "成功导入路线图模块")
        except ImportError as e:
            self.fail(f"导入路线图模块失败: {e}")

    def test_repository_import(self):
        """测试导入数据库仓库模块"""
        try:
            from src.db.repositories.roadmap_repository import (
                EpicRepository,
                StoryRepository,
                TaskRepository,
            )

            self.assertTrue(True, "成功导入数据库仓库模块")
        except ImportError as e:
            self.fail(f"导入数据库仓库模块失败: {e}")

    def test_model_import(self):
        """测试导入数据库模型模块"""
        try:
            from src.models.db import Epic, Milestone, Roadmap, Story, Task

            self.assertTrue(True, "成功导入数据库模型模块")
        except ImportError as e:
            self.fail(f"导入数据库模型模块失败: {e}")

    def test_sync_services_import(self):
        """测试导入同步服务模块"""
        try:
            from src.roadmap.sync import GitHubSyncService, YamlSyncService

            self.assertTrue(True, "成功导入同步服务模块")
        except ImportError as e:
            self.fail(f"导入同步服务模块失败: {e}")


if __name__ == "__main__":
    unittest.main()

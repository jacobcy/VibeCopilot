"""
路线图集成测试模块

测试路线图模块的核心组件集成，验证功能正确性。
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.db.service import DatabaseService
from src.db.sync import DataSynchronizer
from src.roadmap import RoadmapService


class TestRoadmapIntegration(unittest.TestCase):
    """路线图集成测试"""

    def setUp(self):
        """测试准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 设置环境变量
        self.original_project_root = os.environ.get("PROJECT_ROOT")
        os.environ["PROJECT_ROOT"] = self.temp_dir

        # 创建.ai/roadmap目录
        self.roadmap_dir = os.path.join(self.temp_dir, ".ai", "roadmap")
        os.makedirs(self.roadmap_dir, exist_ok=True)

        # 模拟数据库会话
        self.session_mock = MagicMock(spec=Session)

        # 模拟数据库服务
        with patch("sqlalchemy.orm.Session") as session_patch:
            session_patch.return_value = self.session_mock
            self.db_service = DatabaseService(self.session_mock)
            self.data_sync = DataSynchronizer(self.db_service)

        # 模拟活跃路线图
        self.db_service._active_roadmap_id = "roadmap-test"

        # 创建服务实例
        self.service = RoadmapService(self.db_service, self.data_sync)

    def tearDown(self):
        """测试清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)

        # 恢复环境变量
        if self.original_project_root:
            os.environ["PROJECT_ROOT"] = self.original_project_root
        else:
            os.environ.pop("PROJECT_ROOT", None)

    def test_create_and_update_roadmap(self):
        """测试创建和更新路线图"""
        # 模拟数据库服务方法
        self.db_service.create_roadmap = MagicMock(return_value="roadmap-new")
        self.db_service.get_roadmap = MagicMock(
            return_value={
                "id": "roadmap-new",
                "name": "测试路线图",
                "description": "测试描述",
                "version": "1.0",
            }
        )
        self.db_service.get_milestones = MagicMock(
            return_value=[
                {"id": "milestone-1", "name": "里程碑1", "status": "planned", "progress": 0},
                {"id": "milestone-2", "name": "里程碑2", "status": "planned", "progress": 0},
            ]
        )
        self.db_service.list_tasks = MagicMock(return_value=[])

        # 1. 创建新路线图
        create_result = self.service.create_roadmap("测试路线图", "测试描述", "1.0")
        self.assertTrue(create_result["success"])
        self.assertEqual(create_result["roadmap_id"], "roadmap-new")

        # 2. 切换到新路线图
        switch_result = self.service.switch_roadmap("roadmap-new")
        self.assertTrue(switch_result["success"])

        # 3. 检查路线图状态
        check_result = self.service.check_roadmap_status()
        self.assertTrue(check_result["success"])

        # 4. 导出到YAML文件
        # 模拟导出成功
        yaml_path = os.path.join(self.roadmap_dir, "测试路线图.yaml")
        self.data_sync.export_to_file = MagicMock(
            return_value={"success": True, "file_path": yaml_path, "roadmap_id": "roadmap-new"}
        )

        export_result = self.service.export_to_yaml()
        self.assertTrue(export_result["success"])

    def test_multiple_roadmap_management(self):
        """测试多路线图管理"""
        # 模拟数据库服务方法
        self.db_service.get_roadmaps = MagicMock(
            return_value=[
                {"id": "roadmap-1", "name": "路线图1"},
                {"id": "roadmap-2", "name": "路线图2"},
                {"id": "roadmap-3", "name": "路线图3"},
            ]
        )
        self.db_service.get_roadmap = MagicMock(
            return_value={
                "id": "roadmap-2",
                "name": "路线图2",
                "description": "这是路线图2",
                "version": "1.0",
            }
        )

        # 1. 列出所有路线图
        list_result = self.service.list_roadmaps()
        self.assertTrue(list_result["success"])
        self.assertEqual(len(list_result["roadmaps"]), 3)

        # 2. 切换到其他路线图
        switch_result = self.service.switch_roadmap("roadmap-2")
        self.assertTrue(switch_result["success"])
        self.assertEqual(switch_result["roadmap_name"], "路线图2")

        # 3. 获取当前路线图信息
        # 模拟附加数据
        self.db_service.get_epics = MagicMock(return_value=[])
        self.db_service.get_milestones = MagicMock(return_value=[])
        self.db_service.get_stories = MagicMock(return_value=[])

        info_result = self.service.get_roadmap_info()
        self.assertTrue(info_result["success"])
        self.assertEqual(info_result["roadmap"]["name"], "路线图2")


if __name__ == "__main__":
    unittest.main()

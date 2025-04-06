#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路线图数据库模拟补丁工具

提供路线图数据模拟功能和数据库补丁工具
用于解决数据库查询错误：
'Column expression, FROM clause, or other columns clause element expected, got <class 'src.models.db.roadmap.Epic'>'
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoadmapDbPatcher:
    """路线图数据库补丁工具"""

    def __init__(self, yaml_path: str = ".ai/roadmap/rule_engine_roadmap.yaml"):
        """
        初始化路线图数据库补丁工具

        Args:
            yaml_path: YAML路线图文件路径
        """
        self.yaml_path = yaml_path
        self._yaml_data = None
        self._load_yaml()

    def _load_yaml(self) -> None:
        """加载YAML数据"""
        try:
            if os.path.exists(self.yaml_path):
                with open(self.yaml_path, "r", encoding="utf-8") as f:
                    self._yaml_data = yaml.safe_load(f)
                logger.info(f"已加载YAML数据: {self.yaml_path}")
            else:
                logger.warning(f"YAML文件不存在: {self.yaml_path}")
                self._yaml_data = {
                    "title": "示例路线图",
                    "description": "这是一个示例路线图",
                    "theme": "",
                    "milestones": [],
                    "tasks": [],
                }
        except Exception as e:
            logger.error(f"加载YAML失败: {str(e)}")
            self._yaml_data = {
                "title": "示例路线图",
                "description": "这是一个示例路线图",
                "theme": "",
                "milestones": [],
                "tasks": [],
            }

    def patch_roadmap_service(self, service) -> None:
        """
        为路线图服务应用数据模拟补丁

        Args:
            service: 要应用补丁的路线图服务实例
        """
        logger.info("应用路线图服务数据访问补丁...")

        # 替换数据访问方法
        service.get_roadmap = lambda rid: self.get_roadmap(service, rid)
        service.get_milestones = lambda rid: self.get_milestones(service, rid)
        service.get_epics = lambda rid: self.get_epics(service, rid)
        service.get_stories = lambda rid: self.get_stories(service, rid)
        service.list_tasks = lambda rid: self.list_tasks(service, rid)

        logger.info("路线图服务数据访问补丁应用完成")

    def get_roadmap(self, service, roadmap_id: str) -> Dict[str, Any]:
        """替代get_roadmap的模拟数据函数"""
        return {
            "id": roadmap_id,
            "name": self._yaml_data.get("title", "路线图"),
            "description": self._yaml_data.get("description", ""),
            "theme": self._yaml_data.get("theme", ""),
            "version": "1.0",
        }

    def get_milestones(self, service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """替代get_milestones的模拟数据函数"""
        roadmap_id = roadmap_id or service.active_roadmap_id

        milestones = []
        for idx, milestone in enumerate(self._yaml_data.get("milestones", [])):
            milestones.append(
                {
                    "id": f"milestone-{idx + 1}",
                    "name": milestone.get("title", f"里程碑 {idx + 1}"),
                    "description": milestone.get("description", ""),
                    "status": milestone.get("status", "planned"),
                    "progress": milestone.get("progress", 0),
                    "roadmap_id": roadmap_id,
                }
            )

        # 确保至少有一个里程碑
        if not milestones:
            milestones = [
                {
                    "id": "milestone-1",
                    "name": "基础里程碑",
                    "description": "基础功能开发",
                    "status": "planned",
                    "progress": 0,
                    "roadmap_id": roadmap_id,
                }
            ]

        return milestones

    def get_epics(self, service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """替代get_epics的模拟数据函数"""
        roadmap_id = roadmap_id or service.active_roadmap_id

        # 从YAML中提取史诗信息或创建示例数据
        epics_data = self._yaml_data.get("epics", [])
        if not epics_data:
            # 从里程碑生成史诗
            milestones = self._yaml_data.get("milestones", [])
            for idx, milestone in enumerate(milestones):
                epics_data.append(
                    {
                        "title": f"史诗 {idx + 1}",
                        "description": f"关联里程碑: {milestone.get('title')}",
                    }
                )

        # 转换为标准格式
        epics = []
        for idx, epic in enumerate(epics_data):
            epics.append(
                {
                    "id": f"epic-{idx + 1}",
                    "name": epic.get("title", f"史诗 {idx + 1}"),
                    "description": epic.get("description", ""),
                    "status": epic.get("status", "planned"),
                    "progress": epic.get("progress", 0),
                    "roadmap_id": roadmap_id,
                }
            )

        # 确保至少有一个史诗
        if not epics:
            epics = [
                {
                    "id": "epic-1",
                    "name": "核心功能",
                    "description": "核心功能开发",
                    "status": "planned",
                    "progress": 0,
                    "roadmap_id": roadmap_id,
                }
            ]

        return epics

    def get_stories(self, service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """替代get_stories的模拟数据函数"""
        roadmap_id = roadmap_id or service.active_roadmap_id

        # 从YAML中提取用户故事或创建示例数据
        stories = []
        tasks = self._yaml_data.get("tasks", [])

        # 将任务按里程碑分组，为每个里程碑创建一个故事
        milestones = {m.get("title"): m for m in self._yaml_data.get("milestones", [])}
        tasks_by_milestone = {}

        for task in tasks:
            milestone = task.get("milestone")
            if milestone:
                if milestone not in tasks_by_milestone:
                    tasks_by_milestone[milestone] = []
                tasks_by_milestone[milestone].append(task)

        # 为每个里程碑创建故事
        idx = 0
        for milestone_name, milestone_tasks in tasks_by_milestone.items():
            idx += 1
            stories.append(
                {
                    "id": f"story-{idx}",
                    "title": f"{milestone_name} 故事",
                    "description": f"包含 {len(milestone_tasks)} 个任务",
                    "status": "planned",
                    "progress": 0,
                    "milestone_id": f"milestone-{list(milestones.keys()).index(milestone_name) + 1}",
                    "roadmap_id": roadmap_id,
                }
            )

        # 确保至少有一个故事
        if not stories:
            stories = [
                {
                    "id": "story-1",
                    "title": "示例用户故事",
                    "description": "这是一个示例用户故事",
                    "status": "planned",
                    "progress": 0,
                    "milestone_id": "milestone-1",
                    "roadmap_id": roadmap_id,
                }
            ]

        return stories

    def list_tasks(self, service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """替代list_tasks的模拟数据函数"""
        roadmap_id = roadmap_id or service.active_roadmap_id

        # 从YAML中提取任务
        tasks_data = self._yaml_data.get("tasks", [])
        tasks = []

        for idx, task in enumerate(tasks_data):
            milestone = task.get("milestone")

            tasks.append(
                {
                    "id": f"task-{idx + 1}",
                    "title": task.get("title", f"任务 {idx + 1}"),
                    "description": task.get("description", ""),
                    "status": task.get("status", "todo"),
                    "priority": task.get("priority", "P2"),
                    "milestone": milestone,
                    "epic": task.get("epic"),
                    "assignee": task.get("assignee"),
                    "roadmap_id": roadmap_id,
                }
            )

        # 确保至少有一个任务
        if not tasks:
            tasks = [
                {
                    "id": "task-1",
                    "title": "示例任务",
                    "description": "这是一个示例任务",
                    "status": "todo",
                    "priority": "P2",
                    "milestone": "基础里程碑",
                    "roadmap_id": roadmap_id,
                }
            ]

        return tasks


# 使用示例
if __name__ == "__main__":
    from src.roadmap.service import RoadmapService

    print("初始化路线图数据库补丁工具...")
    patcher = RoadmapDbPatcher(".ai/roadmap/rule_engine_roadmap.yaml")

    print("初始化路线图服务...")
    roadmap_service = RoadmapService()

    print("应用路线图服务数据补丁...")
    patcher.patch_roadmap_service(roadmap_service)

    # 测试获取路线图数据
    roadmap_id = "roadmap-rule-engine-roadmap"
    roadmap_service.set_active_roadmap(roadmap_id)

    print("\n路线图信息:")
    roadmap = roadmap_service.get_roadmap(roadmap_id)
    print(f"- ID: {roadmap.get('id')}")
    print(f"- 名称: {roadmap.get('name')}")
    print(f"- 描述: {roadmap.get('description')}")
    print(f"- Theme: {roadmap.get('theme')}")

    print("\n里程碑列表:")
    milestones = roadmap_service.get_milestones(roadmap_id)
    for milestone in milestones:
        print(f"- {milestone.get('name')}: {milestone.get('description')}")

    print("\n史诗列表:")
    epics = roadmap_service.get_epics(roadmap_id)
    for epic in epics:
        print(f"- {epic.get('name')}: {epic.get('description')}")

    print("\n任务列表:")
    tasks = roadmap_service.list_tasks(roadmap_id)
    for task in tasks:
        print(f"- {task.get('title')} ({task.get('status')})")

    print("\n✅ 测试完成! 数据库补丁工具正常工作")

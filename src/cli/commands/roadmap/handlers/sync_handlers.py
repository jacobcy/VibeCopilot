"""
路线图同步和状态相关处理函数

提供路线图同步、切换和状态查询相关功能实现。
"""

import logging
from typing import Any, Dict

from src.cli.commands.roadmap.handlers.utils import count_status

logger = logging.getLogger(__name__)


class RoadmapSyncHandlers:
    """路线图同步和状态处理类"""

    def __init__(self, service, db_service):
        """初始化路线图同步和状态处理类

        Args:
            service: 路线图服务实例
            db_service: 数据库服务实例
        """
        self.service = service
        self.db_service = db_service

    @staticmethod
    def sync_roadmap(roadmap_service, args: Dict) -> Dict[str, Any]:
        """同步路线图数据

        Args:
            roadmap_service: 路线图服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            source = args.get("source", "github")
            if source not in ["github", "yaml"]:
                return {"success": False, "error": f"不支持的同步来源: {source}，支持的来源有: github, yaml"}

            if source == "github":
                # 与GitHub同步
                result = roadmap_service.sync_with_github()
                if not result.get("success", False):
                    return {"success": False, "error": result.get("error", "与GitHub同步失败")}

                return {
                    "success": True,
                    "message": "成功与GitHub同步路线图数据",
                    "data": result.get("stats", {}),
                }
            else:
                # 与YAML同步
                result = roadmap_service.sync_with_yaml()
                if not result.get("success", False):
                    return {"success": False, "error": result.get("error", "与YAML同步失败")}

                return {
                    "success": True,
                    "message": "成功与YAML同步路线图数据",
                    "data": result.get("stats", {}),
                }

        except Exception as e:
            logger.error("同步路线图失败: %s", str(e))
            return {"success": False, "error": f"同步路线图失败: {str(e)}"}

    @staticmethod
    def switch_roadmap(roadmap_service, db_service, args: Dict) -> Dict[str, Any]:
        """切换活动路线图

        Args:
            roadmap_service: 路线图服务实例
            db_service: 数据库服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            roadmap_id = args.get("id")
            if not roadmap_id:
                return {"success": False, "error": "缺少路线图ID参数"}

            # 验证路线图是否存在
            roadmap = db_service.get_roadmap(roadmap_id)
            if not roadmap:
                return {"success": False, "error": f"找不到ID为 {roadmap_id} 的路线图"}

            # 切换活动路线图
            result = roadmap_service.switch_active_roadmap(roadmap_id)
            if not result.get("success", False):
                return {"success": False, "error": result.get("error", "切换活动路线图失败")}

            return {"success": True, "message": f"成功切换活动路线图为: {roadmap['name']} (ID: {roadmap_id})"}

        except Exception as e:
            logger.error("切换活动路线图失败: %s", str(e))
            return {"success": False, "error": f"切换活动路线图失败: {str(e)}"}

    @staticmethod
    def roadmap_status(roadmap_service, db_service, args: Dict) -> Dict[str, Any]:
        """查看路线图状态

        Args:
            roadmap_service: 路线图服务实例
            db_service: 数据库服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            roadmap_id = args.get("id")
            if not roadmap_id:
                # 如果没有指定ID，使用活动路线图
                active_roadmap = db_service.get_active_roadmap()
                if not active_roadmap:
                    return {"success": False, "error": "没有活动路线图，请指定路线图ID或先设置活动路线图"}
                roadmap_id = active_roadmap["id"]

            # 验证路线图是否存在
            roadmap = db_service.get_roadmap(roadmap_id)
            if not roadmap:
                return {"success": False, "error": f"找不到ID为 {roadmap_id} 的路线图"}

            # 获取路线图状态
            status = roadmap_service.get_roadmap_status(roadmap_id)
            if not status.get("success", False):
                return {"success": False, "error": status.get("error", "获取路线图状态失败")}

            # 计算进度统计
            epics = db_service.list_epics(roadmap_id)
            milestones = db_service.list_milestones(roadmap_id)
            stories = db_service.list_stories(roadmap_id)
            tasks = db_service.list_tasks(roadmap_id)

            # 统计各种状态
            epic_stats = count_status(epics)
            milestone_stats = count_status(milestones)
            story_stats = count_status(stories)
            task_stats = count_status(tasks)

            return {
                "success": True,
                "data": {
                    "roadmap": {
                        "id": roadmap["id"],
                        "name": roadmap["name"],
                        "status": roadmap["status"],
                        "is_active": roadmap["is_active"],
                    },
                    "progress": status.get("progress", {}),
                    "stats": {
                        "epics": epic_stats,
                        "milestones": milestone_stats,
                        "stories": story_stats,
                        "tasks": task_stats,
                    },
                },
            }

        except Exception as e:
            logger.error("查看路线图状态失败: %s", str(e))
            return {"success": False, "error": f"查看路线图状态失败: {str(e)}"}

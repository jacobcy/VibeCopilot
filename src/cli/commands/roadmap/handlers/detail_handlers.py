"""
路线图详情相关处理函数

提供路线图详情查看相关功能实现。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RoadmapDetailHandlers:
    """路线图详情处理类"""

    def __init__(self, service=None, db_service=None):
        """
        初始化路线图详情处理器

        Args:
            service: 路线图服务
            db_service: 数据库服务
        """
        self.service = service
        self.db_service = db_service

    @staticmethod
    def show_roadmap(db_service, args: Dict) -> Dict[str, Any]:
        """显示路线图详情

        Args:
            db_service: 数据库服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            roadmap_id = args.get("id")
            if not roadmap_id:
                return {"success": False, "error": "缺少路线图ID参数"}

            roadmap = db_service.get_roadmap(roadmap_id)
            if not roadmap:
                return {"success": False, "error": f"找不到ID为 {roadmap_id} 的路线图"}

            # 获取路线图详细信息
            epics = db_service.list_epics(roadmap["id"])
            milestones = db_service.list_milestones(roadmap["id"])
            stories = db_service.list_stories(roadmap["id"])
            tasks = db_service.list_tasks(roadmap["id"])

            format_type = args.get("format", "text")
            if format_type == "json":
                return {
                    "success": True,
                    "data": {
                        "roadmap": roadmap,
                        "epics": epics,
                        "milestones": milestones,
                        "stories": stories,
                        "tasks": tasks,
                        "stats": {
                            "epics_count": len(epics),
                            "milestones_count": len(milestones),
                            "stories_count": len(stories),
                            "tasks_count": len(tasks),
                        },
                    },
                }
            else:
                # 文本格式输出
                result = {
                    "success": True,
                    "data": {
                        "ID": roadmap["id"],
                        "名称": roadmap["name"],
                        "描述": roadmap["description"],
                        "状态": roadmap["status"],
                        "是否活动": "是" if roadmap["is_active"] else "否",
                        "创建时间": roadmap["created_at"],
                        "更新时间": roadmap["updated_at"],
                        "统计信息": f"Epic数量: {len(epics)}, 里程碑数量: {len(milestones)}, " f"故事数量: {len(stories)}, 任务数量: {len(tasks)}",
                    },
                }
                return result

        except Exception as e:
            logger.error("查看路线图失败: %s", str(e))
            return {"success": False, "error": f"查看路线图失败: {str(e)}"}

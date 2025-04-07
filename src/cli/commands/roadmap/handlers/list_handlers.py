"""
路线图列表相关处理函数

提供路线图列表查询相关功能实现。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RoadmapListHandlers:
    """路线图列表处理类"""

    @staticmethod
    def list_roadmaps(db_service, args: Dict) -> Dict[str, Any]:
        """列出所有路线图

        Args:
            db_service: 数据库服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            verbose = args.get("verbose", False)
            roadmaps = db_service.list_roadmaps()

            if not roadmaps:
                return {"success": True, "message": "没有找到任何路线图", "data": []}

            # 获取当前活动路线图
            active_roadmap = db_service.get_active_roadmap()
            active_id = active_roadmap["id"] if active_roadmap else None

            result_data = []
            for roadmap in roadmaps:
                is_active = "是" if roadmap["is_active"] else "否"
                if verbose:
                    result_data.append(
                        {
                            "id": roadmap["id"],
                            "name": roadmap["name"],
                            "status": roadmap["status"],
                            "active": is_active,
                            "description": roadmap["description"],
                            "created_at": roadmap["created_at"],
                            "updated_at": roadmap["updated_at"],
                        }
                    )
                else:
                    description = (
                        roadmap["description"][:27] + "..."
                        if len(roadmap["description"]) > 30
                        else roadmap["description"]
                    )
                    result_data.append(
                        f"{roadmap['id']}: {roadmap['name']} ({roadmap['status']})"
                        f" [{'活动' if roadmap['is_active'] else '非活动'}] - {description}"
                    )

            if active_id:
                active_info = f"\n当前活动路线图: {active_roadmap['name']} (ID: {active_id})"
                if isinstance(result_data[0], str):
                    result_data.append(active_info)

            return {"success": True, "data": result_data}

        except Exception as e:
            logger.error("列出路线图失败: %s", str(e))
            return {"success": False, "error": f"列出路线图失败: {str(e)}"}

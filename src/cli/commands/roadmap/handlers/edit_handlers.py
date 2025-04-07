"""
路线图编辑相关处理函数

提供路线图创建、更新、删除相关功能实现。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RoadmapEditHandlers:
    """路线图编辑处理类"""

    @staticmethod
    def create_roadmap(roadmap_service, args: Dict) -> Dict[str, Any]:
        """创建路线图

        Args:
            roadmap_service: 路线图服务实例
            args: 命令参数

        Returns:
            处理结果
        """
        try:
            name = args.get("name")
            if not name:
                return {"success": False, "error": "缺少路线图名称参数"}

            description = args.get("description", "")

            # 创建新路线图
            new_roadmap = roadmap_service.create_roadmap(name, description)
            if not new_roadmap.get("success", False):
                return {"success": False, "error": new_roadmap.get("error", "创建路线图失败")}

            roadmap_id = new_roadmap.get("roadmap", {}).get("id")
            return {
                "success": True,
                "message": f"成功创建路线图: {name} (ID: {roadmap_id})",
                "data": {"id": roadmap_id, "name": name},
            }

        except Exception as e:
            logger.error("创建路线图失败: %s", str(e))
            return {"success": False, "error": f"创建路线图失败: {str(e)}"}

    @staticmethod
    def update_roadmap(roadmap_service, db_service, args: Dict) -> Dict[str, Any]:
        """更新路线图

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

            # 获取更新参数
            name = args.get("name")
            description = args.get("description")

            if not name and not description:
                return {"success": False, "error": "至少需要提供一个要更新的参数（name或description）"}

            # 更新路线图
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description

            result = roadmap_service.update_roadmap(roadmap_id, update_data)
            if not result.get("success", False):
                return {"success": False, "error": result.get("error", "更新路线图失败")}

            return {
                "success": True,
                "message": f"成功更新路线图: {roadmap_id}",
                "data": {"id": roadmap_id, "updated_fields": list(update_data.keys())},
            }

        except Exception as e:
            logger.error("更新路线图失败: %s", str(e))
            return {"success": False, "error": f"更新路线图失败: {str(e)}"}

    @staticmethod
    def delete_roadmap(roadmap_service, db_service, args: Dict) -> Dict[str, Any]:
        """删除路线图

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

            # 检查是否强制删除
            force = args.get("force", False)
            if not force:
                return {
                    "success": False,
                    "error": "删除路线图是危险操作，请添加--force参数确认执行",
                    "require_force": True,
                }

            # 删除路线图
            result = roadmap_service.delete_roadmap(roadmap_id)
            if not result.get("success", False):
                return {"success": False, "error": result.get("error", "删除路线图失败")}

            return {"success": True, "message": f"成功删除路线图: {roadmap_id}"}

        except Exception as e:
            logger.error("删除路线图失败: %s", str(e))
            return {"success": False, "error": f"删除路线图失败: {str(e)}"}

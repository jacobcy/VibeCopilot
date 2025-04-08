"""
路线图编辑相关处理函数

提供路线图创建、更新、删除相关功能实现。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RoadmapEditHandlers:
    """路线图编辑处理类"""

    def __init__(self, service=None, db_service=None):
        """
        初始化路线图编辑处理器

        Args:
            service: 路线图服务
            db_service: 数据库服务
        """
        self.service = service
        self.db_service = db_service

    def create_roadmap(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        创建新路线图

        Args:
            name: 路线图名称
            description: 路线图描述

        Returns:
            创建结果
        """
        try:
            if not name:
                return {"success": False, "error": "缺少路线图名称"}

            # 创建路线图数据
            roadmap_data = {"name": name, "description": description}

            # 使用路线图服务创建
            if self.service:
                result = self.service.create_roadmap(roadmap_data)
                return {"success": True, "message": f"成功创建路线图: {name}", "data": result}
            else:
                return {"success": False, "error": "路线图服务不可用"}

        except Exception as e:
            logger.error(f"创建路线图失败: {str(e)}")
            return {"success": False, "error": f"创建路线图失败: {str(e)}"}

    def update_roadmap(self, roadmap_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新路线图

        Args:
            roadmap_id: 路线图ID
            update_data: 更新数据

        Returns:
            更新结果
        """
        try:
            if not roadmap_id:
                return {"success": False, "error": "缺少路线图ID"}

            if not update_data:
                return {"success": False, "error": "没有提供更新数据"}

            # 检查路线图是否存在
            if self.service:
                roadmap = self.service.get_roadmap(roadmap_id)
                if not roadmap:
                    return {"success": False, "error": f"路线图不存在: {roadmap_id}"}

                # 更新路线图
                result = self.service.update_roadmap(roadmap_id, update_data)

                return {"success": True, "message": f"成功更新路线图: {roadmap_id}", "data": result}
            else:
                return {"success": False, "error": "路线图服务不可用"}

        except Exception as e:
            logger.error(f"更新路线图失败: {str(e)}")
            return {"success": False, "error": f"更新路线图失败: {str(e)}"}

    def switch_roadmap(self, roadmap_id: str) -> Dict[str, Any]:
        """
        切换当前活动路线图

        Args:
            roadmap_id: 路线图ID

        Returns:
            切换结果
        """
        try:
            if not roadmap_id:
                return {"success": False, "error": "缺少路线图ID"}

            if self.service:
                # 调用服务的切换方法
                result = self.service.switch_roadmap(roadmap_id)
                return result
            else:
                return {"success": False, "error": "路线图服务不可用"}

        except Exception as e:
            logger.error(f"切换路线图失败: {str(e)}")
            return {"success": False, "error": f"切换路线图失败: {str(e)}"}

    def delete_roadmap(self, roadmap_id: str, force: bool = False) -> Dict[str, Any]:
        """
        删除路线图

        Args:
            roadmap_id: 路线图ID
            force: 是否强制删除

        Returns:
            删除结果
        """
        try:
            if not roadmap_id:
                return {"success": False, "error": "缺少路线图ID"}

            # 检查是否强制删除
            if not force:
                return {
                    "success": False,
                    "error": "删除路线图是危险操作，请添加--force参数确认执行",
                    "require_force": True,
                }

            if self.service:
                # 检查路线图是否存在
                roadmap = self.service.get_roadmap(roadmap_id)
                if not roadmap:
                    return {"success": False, "error": f"路线图不存在: {roadmap_id}"}

                # 删除路线图
                result = self.service.delete_roadmap(roadmap_id)

                return {"success": True, "message": f"成功删除路线图: {roadmap_id}", "data": result}
            else:
                return {"success": False, "error": "路线图服务不可用"}

        except Exception as e:
            logger.error(f"删除路线图失败: {str(e)}")
            return {"success": False, "error": f"删除路线图失败: {str(e)}"}

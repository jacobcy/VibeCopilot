"""
数据库删除处理模块

处理数据库删除相关命令
"""

from typing import Any, Dict

from .base import BaseDatabaseCommand, logger


class DeleteHandler:
    """数据库删除处理器"""

    @staticmethod
    def handle(command: BaseDatabaseCommand, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理删除操作

        Args:
            command: 数据库命令实例
            args: 命令参数
                - type: 实体类型
                - id: 实体ID

        Returns:
            执行结果
        """
        entity_type = args.get("type")
        entity_id = args.get("id")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not entity_id:
            return {"success": False, "error": "请指定实体ID(--id=xxx)"}

        try:
            # 删除实体
            if entity_type == "epic":
                result = command.db_service.delete_epic(entity_id)
            elif entity_type == "story":
                result = command.db_service.delete_story(entity_id)
            elif entity_type == "task":
                result = command.db_service.delete_task(entity_id)
            elif entity_type == "label":
                result = command.db_service.delete_label(entity_id)
            elif entity_type == "template":
                result = command.db_service.delete_template(entity_id)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            if not result:
                return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

            return {
                "success": True,
                "message": f"已删除{entity_type}: {entity_id}",
            }
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return {"success": False, "error": f"删除失败: {e}"}

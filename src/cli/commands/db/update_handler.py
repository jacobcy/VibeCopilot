"""
数据库更新处理模块

处理数据库更新相关命令
"""

import json
from typing import Any, Dict

from .base import BaseDatabaseCommand, logger


class UpdateHandler:
    """数据库更新处理器"""

    @staticmethod
    def handle(command: BaseDatabaseCommand, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新操作

        Args:
            command: 数据库命令实例
            args: 命令参数
                - type: 实体类型
                - id: 实体ID
                - data: JSON格式的更新数据

        Returns:
            执行结果
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        data_str = args.get("data")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not entity_id:
            return {"success": False, "error": "请指定实体ID(--id=xxx)"}

        if not data_str:
            return {"success": False, "error": "请提供数据(--data='json字符串')"}

        try:
            # 解析JSON数据
            data = json.loads(data_str)

            # 更新实体
            if entity_type == "epic":
                result = command.db_service.update_epic(entity_id, data)
            elif entity_type == "story":
                result = command.db_service.update_story(entity_id, data)
            elif entity_type == "task":
                result = command.db_service.update_task(entity_id, data)
            elif entity_type == "label":
                result = command.db_service.update_label(entity_id, data)
            elif entity_type == "template":
                result = command.db_service.update_template(entity_id, data)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            if not result:
                return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

            return {
                "success": True,
                "message": f"已更新{entity_type}: {entity_id}",
                "data": result,
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析失败: {e}"}
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return {"success": False, "error": f"更新失败: {e}"}

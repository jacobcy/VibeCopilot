"""
数据库创建处理模块

处理数据库创建相关命令
"""

import json
from typing import Any, Dict

from .base import BaseDatabaseCommand, logger


class CreateHandler:
    """数据库创建处理器"""

    @staticmethod
    def handle(command: BaseDatabaseCommand, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理创建操作

        Args:
            command: 数据库命令实例
            args: 命令参数
                - type: 实体类型
                - data: JSON格式的数据

        Returns:
            执行结果
        """
        entity_type = args.get("type")
        data_str = args.get("data")

        if not entity_type:
            return {
                "success": False,
                "error": "请指定实体类型(--type=epic/story/task/label/template)",
            }

        if not data_str:
            return {"success": False, "error": "请提供数据(--data='json字符串')"}

        try:
            # 解析JSON数据
            data = json.loads(data_str)

            # 创建实体
            if entity_type == "epic":
                result = command.db_service.create_epic(data)
            elif entity_type == "story":
                result = command.db_service.create_story(data)
            elif entity_type == "task":
                result = command.db_service.create_task(data)
            elif entity_type == "label":
                result = command.db_service.create_label(data)
            elif entity_type == "template":
                result = command.db_service.create_template(data)
            else:
                return {"success": False, "error": f"未知实体类型: {entity_type}"}

            return {"success": True, "message": f"已创建{entity_type}", "data": result}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析失败: {e}"}
        except Exception as e:
            logger.error(f"创建失败: {e}")
            return {"success": False, "error": f"创建失败: {e}"}

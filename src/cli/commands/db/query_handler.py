"""
数据库查询处理模块

处理数据库查询相关命令
"""

from typing import Any, Dict, List

from .base import BaseDatabaseCommand, logger


class QueryHandler:
    """数据库查询处理器"""

    @staticmethod
    def handle(command: BaseDatabaseCommand, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询操作

        Args:
            command: 数据库命令实例
            args: 命令参数
                - type: 实体类型
                - id: 实体ID(可选)
                - query: 查询字符串(可选)
                - tags: 标签列表，逗号分隔(可选)

        Returns:
            执行结果
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        query = args.get("query")
        tags_str = args.get("tags")

        # 处理标签
        tags = None
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(",")]

        if not entity_type:
            return {
                "success": False,
                "error": "请指定查询类型(--type=epic/story/task/label/template)",
            }

        try:
            # 特殊处理模板查询
            if entity_type == "template" and query:
                data = command.db_service.search_templates(query=query, tags=tags)
                return {
                    "success": True,
                    "message": f"已查询模板列表",
                    "count": len(data),
                    "data": data,
                }

            if entity_id:
                # 查询单个实体
                return QueryHandler._query_single_entity(command, entity_type, entity_id)
            else:
                # 查询列表
                return QueryHandler._query_entity_list(command, entity_type)
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {"success": False, "error": f"查询失败: {e}"}

    @staticmethod
    def _query_single_entity(
        command: BaseDatabaseCommand, entity_type: str, entity_id: str
    ) -> Dict[str, Any]:
        """查询单个实体

        Args:
            command: 数据库命令实例
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            执行结果
        """
        if entity_type == "epic":
            data = command.db_service.get_epic(entity_id)
        elif entity_type == "story":
            data = command.db_service.get_story(entity_id)
        elif entity_type == "task":
            data = command.db_service.get_task(entity_id)
        elif entity_type == "label":
            data = command.db_service.get_label(entity_id)
        elif entity_type == "template":
            data = command.db_service.get_template(entity_id)
        else:
            return {"success": False, "error": f"未知实体类型: {entity_type}"}

        if not data:
            return {"success": False, "error": f"未找到{entity_type}: {entity_id}"}

        return {
            "success": True,
            "message": f"已查询{entity_type}: {entity_id}",
            "data": data,
        }

    @staticmethod
    def _query_entity_list(command: BaseDatabaseCommand, entity_type: str) -> Dict[str, Any]:
        """查询实体列表

        Args:
            command: 数据库命令实例
            entity_type: 实体类型

        Returns:
            执行结果
        """
        if entity_type == "epic":
            data = command.db_service.list_epics()
        elif entity_type == "story":
            data = command.db_service.list_stories()
        elif entity_type == "task":
            data = command.db_service.list_tasks()
        elif entity_type == "label":
            data = command.db_service.list_labels()
        elif entity_type == "template":
            data = command.db_service.list_templates()
        else:
            return {"success": False, "error": f"未知实体类型: {entity_type}"}

        return {
            "success": True,
            "message": f"已查询{entity_type}列表",
            "count": len(data),
            "data": data,
        }

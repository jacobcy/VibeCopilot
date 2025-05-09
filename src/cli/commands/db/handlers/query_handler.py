"""
数据库查询处理模块

处理数据库查询相关命令
"""

import json
import logging
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from src.cli.core.decorators import pass_service
from src.db.session_manager import session_scope
from src.services.task.query import TaskQueryService

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class QueryBaseHandler(ClickBaseHandler):
    """查询命令基础处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}
    VALID_FORMATS = {"text", "json", "yaml"}

    def __init__(self):
        super().__init__()

    def _format_and_display_entities(self, entities: List[Dict], entity_type: str, output_format: str = "yaml") -> int:
        """格式化并显示实体列表"""
        if not entities:
            console.print(f"[yellow]未找到 {entity_type} 类型的条目[/yellow]")
            return 0

        # 始终使用YAML格式输出
        print(yaml.dump(entities, allow_unicode=True, sort_keys=False))
        return 0

    def _format_and_display_entity(self, entity: Dict, entity_type: str, entity_id: str, output_format: str = "yaml") -> int:
        """格式化并显示单个实体"""
        if not entity:
            console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
            return 1

        # 始终使用YAML格式输出
        print(yaml.dump(entity, allow_unicode=True, sort_keys=False))
        return 0


class GetEntityHandler(QueryBaseHandler):
    """获取单个实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证获取实体参数"""
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理获取实体命令"""
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询 {entity_type} (ID: {entity_id})")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entity = service.get_entity(entity_type, entity_id)
            return self._format_and_display_entity(entity, entity_type, entity_id, output_format)
        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


class SearchEntitiesHandler(QueryBaseHandler):
    """搜索实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证搜索实体参数"""
        entity_type = kwargs.get("entity_type")
        query_string = kwargs.get("query_string")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not query_string:
            raise ValidationError("搜索条件不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理搜索实体命令"""
        entity_type = kwargs.get("entity_type")
        query_string = kwargs.get("query_string")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"搜索 {entity_type}，查询: {query_string}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entities = service.search_entities(entity_type, query_string)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"搜索 {entity_type} 失败: {str(e)}")


class ListEntitiesHandler(QueryBaseHandler):
    """列出所有实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证列出实体参数"""
        entity_type = kwargs.get("entity_type")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理列出实体命令"""
        entity_type = kwargs.get("entity_type")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询所有 {entity_type}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entities = service.get_entities(entity_type)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


class QueryHandler(QueryBaseHandler):
    """通用查询处理器，用于处理db query命令"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证查询参数"""
        entity_type = kwargs.get("type")
        output_format = kwargs.get("format", "table")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理查询命令"""
        entity_type = kwargs.get("type")
        entity_id = kwargs.get("id")
        query_string = kwargs.get("query")
        output_format = kwargs.get("format", "table")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询 {entity_type}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 如果提供了ID，查询单个实体
            if entity_id:
                # For TaskService, use get_task directly
                if isinstance(service, TaskQueryService) or hasattr(service, "get_task"):
                    with session_scope() as session:
                        entity = service.get_task(session, entity_id)
                    return self._format_and_display_entity(entity, entity_type, entity_id, output_format)
                else:  # Fallback for other potential service types
                    entity = service.get_entity(entity_type, entity_id)
                    return self._format_and_display_entity(entity, entity_type, entity_id, output_format)

            # 如果提供了查询字符串，搜索实体
            elif query_string:
                # Check if the service is TaskService or TaskQueryService
                if isinstance(service, TaskQueryService) or hasattr(service, "get_task_by_identifier"):
                    logger.debug(f"Using TaskService.get_task_by_identifier for query: {query_string}")
                    entity = service.get_task_by_identifier(query_string)
                    # get_task_by_identifier returns a single result or None
                    if entity:
                        return self._format_and_display_entity(entity, entity_type, entity.get("id", query_string), output_format)
                    else:
                        console.print(f"[yellow]未找到名称或ID为 '{query_string}' 的任务[/yellow]")
                        return 0
                # 对于 roadmap 类型，使用简单的标题匹配
                elif entity_type == "roadmap":
                    logger.debug(f"使用简单标题匹配搜索 roadmap: {query_string}")
                    with session_scope() as session:
                        from src.models.db.roadmap import Roadmap

                        # 使用 LIKE 查询匹配标题或描述
                        roadmaps = (
                            session.query(Roadmap)
                            .filter((Roadmap.title.like(f"%{query_string}%")) | (Roadmap.description.like(f"%{query_string}%")))
                            .all()
                        )

                        # 转换为字典列表
                        entities = []
                        for roadmap in roadmaps:
                            # 创建简化的字典
                            entity_dict = {
                                "id": roadmap.id,
                                "title": roadmap.title,
                                "description": roadmap.description,
                                "version": roadmap.version,
                                "status": roadmap.status,
                                "tags": roadmap.tags,
                                "created_at": str(roadmap.created_at),
                                "updated_at": str(roadmap.updated_at),
                                "epics_count": len(roadmap.epics) if roadmap.epics else 0,
                                "milestones_count": len(roadmap.milestones) if roadmap.milestones else 0,
                            }
                            entities.append(entity_dict)

                        return self._format_and_display_entities(entities, entity_type, output_format)

                # 对于 task 类型，使用简单的标题匹配
                elif entity_type == "task":
                    logger.debug(f"使用简单标题匹配搜索 task: {query_string}")
                    with session_scope() as session:
                        from src.models.db.task import Task

                        # 使用 LIKE 查询匹配标题或描述
                        tasks = (
                            session.query(Task).filter((Task.title.like(f"%{query_string}%")) | (Task.description.like(f"%{query_string}%"))).all()
                        )

                        # 转换为字典列表
                        entities = []
                        for task in tasks:
                            # 使用 to_dict 方法转换为字典
                            if hasattr(task, "to_dict"):
                                entity_dict = task.to_dict()
                            else:
                                # 手动创建字典
                                entity_dict = {
                                    "id": task.id,
                                    "title": task.title,
                                    "description": task.description,
                                    "status": task.status,
                                    "priority": task.priority,
                                    "estimated_hours": task.estimated_hours,
                                    "is_completed": task.is_completed,
                                    "story_id": task.story_id,
                                    "assignee": task.assignee,
                                    "labels": task.labels,
                                    "created_at": str(task.created_at) if task.created_at else None,
                                    "updated_at": str(task.updated_at) if task.updated_at else None,
                                    "completed_at": str(task.completed_at) if task.completed_at else None,
                                    "due_date": str(task.due_date) if task.due_date else None,
                                }
                            entities.append(entity_dict)

                        return self._format_and_display_entities(entities, entity_type, output_format)
                # Fallback for other service types using search_entities (if available)
                elif hasattr(service, "search_entities"):
                    logger.debug(f"Using generic service.search_entities for query: {query_string}")
                    entities = service.search_entities(entity_type, query_string)
                    return self._format_and_display_entities(entities, entity_type, output_format)
                else:
                    raise NotImplementedError(f"服务 '{type(service).__name__}' 不支持基于查询字符串 '{query_string}' 的搜索操作。")

            # 否则，列出所有实体
            else:
                # Check if the service is TaskService or TaskQueryService
                if isinstance(service, TaskQueryService) or hasattr(service, "list_tasks"):
                    logger.debug(f"Using TaskService.list_tasks to list all tasks")
                    with session_scope() as session:
                        entities = service.list_tasks(session)  # Assuming list_tasks exists and takes session
                    return self._format_and_display_entities(entities, entity_type, output_format)
                # Fallback for other service types using get_entities (if available)
                elif hasattr(service, "get_entities"):
                    logger.debug(f"Using generic service.get_entities to list all {entity_type}")
                    entities = service.get_entities(entity_type)
                    return self._format_and_display_entities(entities, entity_type, output_format)
                else:
                    raise NotImplementedError(f"服务 '{type(service).__name__}' 不支持列出所有 '{entity_type}' 实体的操作。")

        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


@click.command(name="query", help="查询数据")
@click.argument("query_keywords", required=False)
@click.option("-t", "--type", "entity_type", required=True, help="实体类型 (e.g., roadmap, epic, milestone, story, task)")
@click.option("-q", "--query", help="查询字符串")
@click.option("-v", "--verbose", is_flag=True, default=False, help="显示详细信息")
@pass_service(service_type="db")
def query_db_cli(service, query_keywords, entity_type: str, query: str, verbose: bool):
    """查询数据的Click命令入口"""
    # 优先使用位置参数，如果没有则使用--query选项
    final_query = query_keywords or query

    handler = QueryHandler()
    params: Dict[str, Any] = {
        "type": entity_type,
        "query": final_query,
        "format": "yaml",  # 始终使用YAML格式
        "verbose": verbose,
        "service": service,  # 传递服务实例
    }
    try:
        handler.handle(**params)
    except Exception as e:
        # handler.error_handler(e) # error_handler 现在是 handler 的一部分
        # 或者直接处理
        console.print(f"[red]查询数据时出错: {str(e)}[/red]")
        logger.error(f"查询数据时出错 (Type={entity_type}, Query={final_query}): {e}", exc_info=True)
        raise click.Abort()

"""
数据库表结构和统计工具模块

提供查询数据库表信息、结构和统计数据的工具函数。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import MetaData, inspect, text
from sqlalchemy.orm import Session

from src.db.utils.entity_mapping import get_model_class

logger = logging.getLogger(__name__)


def get_all_tables(session: Session) -> List[str]:
    """获取数据库中所有表的名称

    Args:
        session: SQLAlchemy会话对象

    Returns:
        List[str]: 所有表名列表
    """
    try:
        inspector = inspect(session.bind)
        table_names = inspector.get_table_names()
        logger.info(f"获取到{len(table_names)}个数据库表")
        return table_names
    except Exception as e:
        logger.error(f"获取数据库表列表失败: {str(e)}", exc_info=True)
        return []


def get_db_stats(session: Session) -> Dict[str, int]:
    """获取数据库表记录统计信息

    Args:
        session: SQLAlchemy会话对象

    Returns:
        Dict[str, int]: 包含各实体类型记录数的字典
    """
    try:
        result = {}

        # 获取所有表名
        table_names = get_all_tables(session)

        # 查询每个表的记录数
        for table_name in table_names:
            try:
                # 使用正确的SQLAlchemy查询方式（使用text()函数）
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                count_result = session.execute(count_query).scalar()
                result[table_name] = count_result or 0
            except Exception as table_e:
                logger.warning(f"获取表 {table_name} 的记录数失败: {str(table_e)}")
                result[table_name] = 0

        # 如果没有找到任何表，回退到硬编码表列表
        if not result:
            logger.warning("未找到任何表，使用硬编码表列表")

            # Epic表
            try:
                from src.models.db import Epic

                epic_count = session.query(Epic).count()
                result["epic"] = epic_count
            except Exception:
                result["epic"] = 0

            # Story表
            try:
                from src.models.db import Story

                story_count = session.query(Story).count()
                result["story"] = story_count
            except Exception:
                result["story"] = 0

            # Task表
            try:
                from src.models.db.task import Task

                task_count = session.query(Task).count()
                result["task"] = task_count
            except Exception:
                result["task"] = 0

            # Label模型可能不存在，设置为0
            result["label"] = 0

            # Template模型
            try:
                from src.models.db import Template

                template_count = session.query(Template).count()
                result["template"] = template_count
            except Exception:
                result["template"] = 0

        logger.info(f"获取数据库统计信息成功: {result}")
        return result
    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {str(e)}", exc_info=True)
        # 返回默认值，避免前端报错
        return {"epic": 0, "story": 0, "task": 0, "label": 0, "template": 0}


def get_table_stats(session: Session, table_name: str) -> Dict[str, Any]:
    """获取指定表的统计信息

    Args:
        session: SQLAlchemy会话对象
        table_name: 表名称

    Returns:
        Dict[str, Any]: 包含表统计信息的字典
    """
    try:
        # 检查表是否存在
        all_tables = get_all_tables(session)
        if table_name not in all_tables and table_name.lower() not in all_tables:
            # 尝试使用模型类查找
            model_class = get_model_class(table_name)
            if model_class and hasattr(model_class, "__tablename__"):
                actual_table_name = model_class.__tablename__
                if actual_table_name in all_tables:
                    table_name = actual_table_name
                else:
                    return {"error": f"表 '{table_name}' 在数据库中不存在"}
            else:
                return {"error": f"表 '{table_name}' 在数据库中不存在"}

        # 获取记录总数
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count = session.execute(count_query).scalar() or 0

        # 尝试获取数据分布情况(如果有status字段)
        status_counts = {}
        try:
            # 先检查表是否有status列
            inspector = inspect(session.bind)
            columns = inspector.get_columns(table_name)
            column_names = [col["name"] for col in columns]

            if "status" in column_names:
                # 获取状态分布
                status_query = text(
                    f"""
                    SELECT status, COUNT(*)
                    FROM {table_name}
                    GROUP BY status
                """
                )
                status_results = session.execute(status_query).fetchall()
                status_counts = {status: count for status, count in status_results if status is not None}
        except Exception as e:
            logger.warning(f"获取表 {table_name} 的状态分布失败: {str(e)}")

        return {"table_name": table_name, "total_count": count, "status_distribution": status_counts}
    except Exception as e:
        logger.error(f"获取表统计信息失败: {str(e)}", exc_info=True)
        return {"error": str(e)}


def get_table_schema(session: Session, table_name: str) -> Dict[str, Any]:
    """获取数据库表结构信息

    Args:
        session: SQLAlchemy会话对象
        table_name: 表名称，如 'task', 'epic', 'story' 等

    Returns:
        Dict[str, Any]: 包含表结构信息的字典
    """
    try:
        inspector = inspect(session.bind)

        # 检查表是否存在
        all_tables = get_all_tables(session)
        if table_name not in all_tables and table_name.lower() not in all_tables:
            # 尝试使用模型类查找
            model_class = get_model_class(table_name)
            if model_class and hasattr(model_class, "__tablename__"):
                actual_table_name = model_class.__tablename__
                if actual_table_name in all_tables:
                    table_name = actual_table_name
                else:
                    return {"error": f"表 '{table_name}' 在数据库中不存在"}
            else:
                return {"error": f"表 '{table_name}' 在数据库中不存在"}

        # 获取表信息
        columns = inspector.get_columns(table_name)

        # 查询表记录数量
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count = session.execute(count_query).scalar() or 0

        # 获取几条示例数据
        examples = []
        try:
            sample_query = text(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = session.execute(sample_query).fetchall()
            for row in sample_rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    col_name = column["name"]
                    row_dict[col_name] = str(row[i]) if row[i] is not None else None
                examples.append(row_dict)
        except Exception as e:
            logger.warning(f"获取表 {table_name} 的示例数据失败: {str(e)}")

        return {
            "table_name": table_name,
            "count": count,
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col["default"]) if col["default"] is not None else None,
                }
                for col in columns
            ],
            "examples": examples,
        }
    except Exception as e:
        logger.error(f"获取表结构信息失败: {str(e)}", exc_info=True)
        return {"error": str(e)}

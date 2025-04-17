"""
实体映射工具模块

提供数据库表名与实体类型之间的映射转换功能。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 常见的表名与实体类型的映射关系
TABLE_TO_ENTITY_MAP = {
    "tasks": "task",
    "epics": "epic",
    "stories": "story",
    "templates": "template",
    "rules": "rule",
    "workflows": "workflow",
    "comments": "comment",
    "stages": "stage",
    "flow_sessions": "flow_session",
    "stage_instances": "stage_instance",
    "transitions": "transition",
    "memory_items": "memory_item",
}

# 实体类型到表名的映射
ENTITY_TO_TABLE_MAP = {
    "task": "tasks",
    "epic": "epics",
    "story": "stories",
    "template": "templates",
    "rule": "rules",
    "workflow": "workflows",
    "comment": "comments",
    "stage": "stages",
    "flow_session": "flow_sessions",
    "stage_instance": "stage_instances",
    "transition": "transitions",
    "memory_item": "memory_items",
}


def get_model_class(table_name: str):
    """获取指定表名对应的模型类

    Args:
        table_name: 表名称

    Returns:
        模型类或None
    """
    # 常见模型的映射
    model_map = {
        "epic": ("Epic", "src.models.db"),
        "story": ("Story", "src.models.db"),
        "task": ("Task", "src.models.db.task"),
        "template": ("Template", "src.models.db"),
    }

    # 尝试从映射中查找
    table_name_lower = table_name.lower()

    # 如果输入是表名（复数形式），先转换为实体类型（单数形式）
    if table_name_lower in TABLE_TO_ENTITY_MAP:
        table_name_lower = TABLE_TO_ENTITY_MAP[table_name_lower]

    if table_name_lower in model_map:
        class_name, module_path = model_map[table_name_lower]
        try:
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.warning(f"从映射加载模型类失败: {str(e)}")
            return None

    # 如果映射中没有，尝试从表名推断模型类
    # 通常表名是小写复数形式，模型类是单数PascalCase形式
    try:
        # 去除可能的复数形式并转为Pascal命名
        singular = table_name.rstrip("s")  # 简单去除复数
        pascal_case = "".join(word.capitalize() for word in singular.split("_"))

        # 尝试从src.models.db导入该类
        try:
            module = __import__("src.models.db", fromlist=[pascal_case])
            if hasattr(module, pascal_case):
                return getattr(module, pascal_case)
        except (ImportError, AttributeError):
            pass

        # 尝试从更具体的模块导入
        try:
            module_path = f"src.models.db.{singular}"
            module = __import__(module_path, fromlist=[pascal_case])
            if hasattr(module, pascal_case):
                return getattr(module, pascal_case)
        except (ImportError, AttributeError):
            pass
    except Exception as e:
        logger.warning(f"推断模型类失败: {str(e)}")

    return None


def get_valid_entity_types(session: Session, include_tables: bool = False) -> List[str]:
    """获取所有有效的实体类型

    Args:
        session: SQLAlchemy会话对象
        include_tables: 是否包含所有数据库表（即使没有对应的实体类型）

    Returns:
        List[str]: 所有有效的实体类型列表
    """
    from src.db.utils.schema import get_all_tables

    valid_entities = set()

    # 从已知的实体映射中获取
    valid_entities.update(ENTITY_TO_TABLE_MAP.keys())

    # 如果需要包含所有表
    if include_tables:
        try:
            tables = get_all_tables(session)
            # 对表名应用映射转换
            for table in tables:
                entity_type = map_table_to_entity(table)
                if entity_type:
                    valid_entities.add(entity_type)
                else:
                    # 如果没有映射关系，可以考虑将表名添加为可能的实体类型
                    # 例如去掉复数's'后的形式
                    if table.endswith("s"):
                        valid_entities.add(table[:-1])
                    else:
                        valid_entities.add(table)
        except Exception as e:
            logger.warning(f"获取所有表名失败: {str(e)}")

    return sorted(list(valid_entities))


def map_table_to_entity(table_name: str) -> Optional[str]:
    """将表名映射为实体类型

    Args:
        table_name: 数据库表名

    Returns:
        Optional[str]: 对应的实体类型，如果没有映射关系则返回None
    """
    table_name_lower = table_name.lower()

    # 1. 直接从映射表中查找
    if table_name_lower in TABLE_TO_ENTITY_MAP:
        return TABLE_TO_ENTITY_MAP[table_name_lower]

    # 2. 尝试使用简单的复数->单数转换规则
    if table_name_lower.endswith("s"):
        entity_type = table_name_lower[:-1]
        if entity_type in ENTITY_TO_TABLE_MAP.values():
            return entity_type

    # 3. 如果没有找到映射关系，返回原表名
    return table_name


def map_entity_to_table(entity_type: str) -> str:
    """将实体类型映射为表名

    Args:
        entity_type: 实体类型名称

    Returns:
        str: 对应的数据库表名
    """
    entity_type_lower = entity_type.lower()

    # 1. 从映射表中查找
    if entity_type_lower in ENTITY_TO_TABLE_MAP:
        return ENTITY_TO_TABLE_MAP[entity_type_lower]

    # 2. 尝试使用简单的单数->复数转换规则
    if not entity_type_lower.endswith("s"):
        table_name = f"{entity_type_lower}s"
        return table_name

    # 3. 如果以上都不匹配，返回原实体类型名称
    return entity_type

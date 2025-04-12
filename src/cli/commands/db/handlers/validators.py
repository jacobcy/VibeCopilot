"""
参数验证器模块
"""
import os
import re
from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    """验证错误异常"""

    pass


def validate_db_name(db_name: str) -> bool:
    """
    验证数据库名称

    Args:
        db_name: 数据库名称

    Returns:
        bool: 验证是否通过

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not db_name:
        raise ValidationError("数据库名称不能为空")

    if not re.match(r"^[a-zA-Z0-9_-]+$", db_name):
        raise ValidationError("数据库名称只能包含字母、数字、下划线和连字符")

    return True


def validate_table_name(table_name: str) -> bool:
    """
    验证表名

    Args:
        table_name: 表名

    Returns:
        bool: 验证是否通过

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not table_name:
        raise ValidationError("表名不能为空")

    if not re.match(r"^[a-zA-Z0-9_-]+$", table_name):
        raise ValidationError("表名只能包含字母、数字、下划线和连字符")

    return True


def validate_file_path(file_path: str, should_exist: bool = True) -> bool:
    """
    验证文件路径

    Args:
        file_path: 文件路径
        should_exist: 文件是否应该存在

    Returns:
        bool: 验证是否通过

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not file_path:
        raise ValidationError("文件路径不能为空")

    if should_exist and not os.path.exists(file_path):
        raise ValidationError(f"文件 {file_path} 不存在")

    return True


def validate_query(query: str) -> bool:
    """
    验证SQL查询语句

    Args:
        query: SQL查询语句

    Returns:
        bool: 验证是否通过

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not query:
        raise ValidationError("查询语句不能为空")

    # 这里可以添加更多的SQL语法验证
    return True


def validate_fields(fields: Dict[str, Any]) -> bool:
    """
    验证字段定义

    Args:
        fields: 字段定义字典

    Returns:
        bool: 验证是否通过

    Raises:
        ValidationError: 验证失败时抛出
    """
    if not fields:
        raise ValidationError("字段定义不能为空")

    valid_types = {"string", "integer", "float", "boolean", "date", "datetime"}

    for field_name, field_type in fields.items():
        if not re.match(r"^[a-zA-Z0-9_]+$", field_name):
            raise ValidationError(f"字段名 {field_name} 格式不正确")

        if field_type not in valid_types:
            raise ValidationError(f"字段类型 {field_type} 不支持")

    return True

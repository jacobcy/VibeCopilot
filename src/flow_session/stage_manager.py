"""
阶段实例管理器模块 (向下兼容包装器)

提供工作流阶段实例的创建、查询、更新和删除功能。
此模块为了向下兼容而保留，新代码应直接使用 src.flow_session.stage.manager 模块。
"""

from src.flow_session.stage.manager import StageInstanceManager
from src.flow_session.stage.operations import (
    add_completed_item,
    complete_instance,
    create_instance,
    fail_instance,
    get_instance,
    get_instance_progress,
    list_instances,
    start_instance,
    update_context,
    update_deliverables,
    update_instance,
)

# 导出所有内容以保持向下兼容性
__all__ = [
    "StageInstanceManager",
    "create_instance",
    "get_instance",
    "list_instances",
    "update_instance",
    "start_instance",
    "complete_instance",
    "fail_instance",
    "add_completed_item",
    "update_context",
    "update_deliverables",
    "get_instance_progress",
]

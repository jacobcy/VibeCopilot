"""
阶段实例管理器操作模块

提供阶段实例高级操作的功能实现。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import get_session_factory, init_db
from src.flow_session.stage.manager import StageInstanceManager
from src.models.db import StageInstance


def get_db_session():
    """获取数据库会话"""
    init_db()  # 确保数据库已初始化
    SessionFactory = get_session_factory()
    return SessionFactory()


def create_instance(session_id: str, stage_id: str, name: Optional[str] = None) -> Optional[StageInstance]:
    """创建新的阶段实例的便捷函数

    Args:
        session_id: 会话ID
        stage_id: 阶段ID
        name: 阶段名称，如果不指定则使用阶段ID

    Returns:
        新创建的阶段实例或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        try:
            return manager.create_instance(session_id, stage_id, name)
        except ValueError as e:
            print(f"创建阶段实例失败: {str(e)}")
            return None


def get_instance(instance_id: str) -> Optional[StageInstance]:
    """获取阶段实例详情的便捷函数

    Args:
        instance_id: 阶段实例ID

    Returns:
        阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.get_instance(instance_id)


def list_instances(session_id: Optional[str] = None, status: Optional[str] = None) -> List[StageInstance]:
    """列出阶段实例的便捷函数

    Args:
        session_id: 会话ID
        status: 阶段状态

    Returns:
        阶段实例列表
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.list_instances(session_id, status)


def update_instance(instance_id: str, data: Dict[str, Any]) -> Optional[StageInstance]:
    """更新阶段实例数据的便捷函数

    Args:
        instance_id: 阶段实例ID
        data: 更新数据

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.update_instance(instance_id, data)


def start_instance(instance_id: str) -> Optional[StageInstance]:
    """开始阶段实例的便捷函数

    Args:
        instance_id: 阶段实例ID

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.start_instance(instance_id)


def complete_instance(instance_id: str, deliverables: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
    """完成阶段实例的便捷函数

    Args:
        instance_id: 阶段实例ID
        deliverables: 交付物数据

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.complete_instance(instance_id, deliverables)


def fail_instance(instance_id: str, error: str = None) -> Optional[StageInstance]:
    """标记阶段实例为失败的便捷函数

    Args:
        instance_id: 阶段实例ID
        error: 错误信息

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.fail_instance(instance_id, error)


def add_completed_item(instance_id: str, item_id: str) -> Optional[StageInstance]:
    """添加已完成项的便捷函数

    Args:
        instance_id: 阶段实例ID
        item_id: 项目ID

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.add_completed_item(instance_id, item_id)


def update_context(instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
    """更新阶段实例上下文的便捷函数

    Args:
        instance_id: 阶段实例ID
        context: 上下文数据

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.update_context(instance_id, context)


def update_deliverables(instance_id: str, deliverables: Dict[str, Any]) -> Optional[StageInstance]:
    """更新阶段实例交付物的便捷函数

    Args:
        instance_id: 阶段实例ID
        deliverables: 交付物数据

    Returns:
        更新后的阶段实例对象或None
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        return manager.update_deliverables(instance_id, deliverables)


def get_instance_progress(instance_id: str) -> Dict[str, Any]:
    """获取阶段实例进度信息的便捷函数

    Args:
        instance_id: 阶段实例ID

    Returns:
        包含进度信息的字典
    """
    with get_db_session() as session:
        manager = StageInstanceManager(session)
        instance = manager.get_instance(instance_id)
        if not instance:
            return {"error": "阶段实例不存在"}

        # 获取检查项定义
        workflow_repo = manager.workflow_repo
        session_repo = manager.session_repo

        flow_session = session_repo.get_by_id(instance.session_id)
        if not flow_session:
            return {"error": "会话不存在"}

        workflow = workflow_repo.get_by_id(flow_session.workflow_id)
        if not workflow or not workflow.stages:
            return {"error": "工作流定义不存在或不包含阶段信息"}

        # 查找阶段定义
        stage_def = next((s for s in workflow.stages if s.get("id") == instance.stage_id), None)
        if not stage_def:
            return {"error": "找不到阶段定义"}

        # 获取检查项列表
        checklist = stage_def.get("checklist", [])
        completed_items = instance.completed_items or []

        # 构造进度信息
        items = []
        for item in checklist:
            item_id = item.get("id", "")
            item_name = item.get("name", "未命名项目")
            item_status = "COMPLETED" if item_id in completed_items else "PENDING"

            items.append({"id": item_id, "name": item_name, "status": item_status})

        # 计算进度百分比
        total_count = len(checklist)
        completed_count = len(completed_items)
        progress_percentage = (completed_count / total_count * 100) if total_count > 0 else 0

        return {
            "instance_id": instance_id,
            "stage_id": instance.stage_id,
            "name": instance.name,
            "status": instance.status,
            "items": items,
            "total_count": total_count,
            "completed_count": completed_count,
            "progress_percentage": round(progress_percentage, 2),
        }

"""
工作流会话操作模块

提供工作流会话高级操作的功能实现。
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from src.db import get_session_factory, init_db
from src.flow_session.session.manager import FlowSessionManager
from src.models.db import FlowSession, StageInstance, WorkflowDefinition


def get_db_session():
    """获取数据库会话"""
    init_db()  # 确保数据库已初始化
    SessionFactory = get_session_factory()
    return SessionFactory()


def create_session(workflow_id: str, name: Optional[str] = None) -> Optional[FlowSession]:
    """创建新会话的便捷函数

    Args:
        workflow_id: 工作流定义ID
        name: 会话名称

    Returns:
        创建的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        try:
            return manager.create_session(workflow_id, name)
        except ValueError as e:
            print(f"创建会话失败: {str(e)}")
            return None


def get_session(session_id: str) -> Optional[FlowSession]:
    """获取会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        会话对象或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.get_session(session_id)


def list_sessions(status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
    """列出会话的便捷函数

    Args:
        status: 会话状态
        workflow_id: 工作流ID

    Returns:
        会话列表
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.list_sessions(status, workflow_id)


def update_session(session_id: str, data: Dict[str, Any]) -> Optional[FlowSession]:
    """更新会话的便捷函数

    Args:
        session_id: 会话ID
        data: 更新数据

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.update_session(session_id, data)


def delete_session(session_id: str) -> bool:
    """删除会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        是否删除成功
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.delete_session(session_id)


def pause_session(session_id: str) -> Optional[FlowSession]:
    """暂停会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.pause_session(session_id)


def resume_session(session_id: str) -> Optional[FlowSession]:
    """恢复会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.resume_session(session_id)


def complete_session(session_id: str) -> Optional[FlowSession]:
    """完成会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.complete_session(session_id)


def abort_session(session_id: str) -> Optional[FlowSession]:
    """终止会话的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.abort_session(session_id)


def get_session_stages(session_id: str) -> List[StageInstance]:
    """获取会话的所有阶段实例的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        阶段实例列表
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        from src.flow_session.stage_manager import StageInstanceManager

        return manager.stage_repo.get_by_session_id(session_id)


def get_session_progress(session_id: str) -> Dict[str, Any]:
    """获取会话进度信息的便捷函数

    Args:
        session_id: 会话ID

    Returns:
        包含进度信息的字典
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        flow_session = manager.get_session(session_id)
        if not flow_session:
            return {"error": "会话不存在"}

        workflow = manager.workflow_repo.get_by_id(flow_session.workflow_id)
        if not workflow:
            return {"error": "工作流定义不存在"}

        stages = manager.stage_repo.get_by_session_id(session_id)

        # 获取工作流中定义的所有阶段
        all_stages = workflow.stages or []

        # 构造进度信息
        completed_stages = []
        current_stage = None
        pending_stages = []

        # 计算每个阶段的状态
        for stage_def in all_stages:
            stage_id = stage_def.get("id")
            stage_name = stage_def.get("name", "未命名阶段")

            # 查找对应的阶段实例
            stage_instance = next((s for s in stages if s.stage_id == stage_id), None)

            if not stage_instance:
                # 阶段尚未开始
                pending_stages.append({"id": stage_id, "name": stage_name, "status": "PENDING"})
                continue

            stage_info = {
                "id": stage_id,
                "name": stage_name,
                "status": stage_instance.status,
                "started_at": stage_instance.started_at.isoformat() if stage_instance.started_at else None,
                "completed_at": stage_instance.completed_at.isoformat() if stage_instance.completed_at else None,
            }

            if stage_instance.status == "COMPLETED":
                completed_stages.append(stage_info)
            elif stage_instance.status == "ACTIVE":
                from src.flow_session.stage_manager import StageInstanceManager

                stage_manager = StageInstanceManager(session)
                progress = stage_manager.get_instance_progress(stage_instance.id)

                stage_info["completed_items"] = progress.get("completed_count", 0)
                stage_info["total_items"] = progress.get("total_count", 0)

                current_stage = stage_info
            else:
                pending_stages.append(stage_info)

        return {
            "session_id": session_id,
            "workflow_id": flow_session.workflow_id,
            "name": flow_session.name,
            "status": flow_session.status,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "pending_stages": pending_stages,
        }


def set_current_stage(session_id: str, stage_id: str) -> Optional[FlowSession]:
    """设置会话当前阶段的便捷函数

    Args:
        session_id: 会话ID
        stage_id: 阶段ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.session_repo.update_current_stage(session_id, stage_id)


def complete_stage(session_id: str, stage_id: str) -> bool:
    """标记阶段为已完成的便捷函数

    Args:
        session_id: 会话ID
        stage_id: 阶段ID

    Returns:
        是否操作成功
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)

        # 获取阶段实例
        from src.flow_session.stage_manager import StageInstanceManager

        stage_manager = StageInstanceManager(session)
        instances = stage_manager.list_instances(session_id=session_id)
        instance = next((i for i in instances if i.stage_id == stage_id), None)

        if not instance:
            return False

        # 标记为已完成
        completed = stage_manager.complete_instance(instance.id)
        return completed is not None

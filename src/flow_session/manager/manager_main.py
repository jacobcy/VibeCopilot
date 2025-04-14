"""
工作流会话管理器主类

集成所有工作流会话管理功能的主类。
"""

from typing import Any, Dict, List, Optional

from src.db import get_session_factory
from src.flow_session.manager.current_session import CurrentSessionMixin
from src.flow_session.manager.manager_base import FlowSessionManagerBase
from src.flow_session.manager.session_context import SessionContextMixin
from src.flow_session.manager.session_crud import SessionCRUDMixin
from src.flow_session.manager.session_state import SessionStateMixin
from src.models.db import FlowSession, WorkflowDefinition


class FlowSessionManager(FlowSessionManagerBase, SessionCRUDMixin, SessionStateMixin, SessionContextMixin, CurrentSessionMixin):
    """工作流会话管理器，整合所有会话管理功能"""

    # 这里可以添加任何需要覆盖或增强的方法
    def fuzzy_search_workflow(self, workflow_id: str) -> List[WorkflowDefinition]:
        """模糊搜索工作流定义

        根据给定的工作流ID或名称，搜索数据库中与之匹配的工作流定义

        Args:
            workflow_id: 工作流ID或名称

        Returns:
            匹配的工作流定义列表
        """
        # 尝试直接获取与名称或ID部分匹配的工作流
        workflows = []

        # 查询名称包含给定字符串的工作流
        name_matches = self.session.query(WorkflowDefinition).filter(WorkflowDefinition.name.ilike(f"%{workflow_id}%")).all()
        if name_matches:
            workflows.extend(name_matches)

        # 查询ID包含给定字符串的工作流
        id_matches = self.session.query(WorkflowDefinition).filter(WorkflowDefinition.id.ilike(f"%{workflow_id}%")).all()
        if id_matches:
            # 添加未在name_matches中的结果
            for wf in id_matches:
                if wf not in workflows:
                    workflows.append(wf)

        # 查询描述包含给定字符串的工作流
        desc_matches = self.session.query(WorkflowDefinition).filter(WorkflowDefinition.description.ilike(f"%{workflow_id}%")).all()
        if desc_matches:
            # 添加未在之前结果中的结果
            for wf in desc_matches:
                if wf not in workflows:
                    workflows.append(wf)

        return workflows

    pass


# 移除全局的单例实例和数据库会话，避免连接池压力
# 以下代码替换为使用上下文管理器创建临时会话

# ============= 函数导出 =============
# 改为使用上下文管理器创建临时会话，确保会话使用后被正确关闭


# 会话CRUD操作
def create_session(workflow_id: str, name: Optional[str] = None, task_id: Optional[str] = None) -> FlowSession:
    """创建工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.create_session(workflow_id, name, task_id)
        db_session.commit()
        return result


def get_session(id_or_name: str) -> Optional[FlowSession]:
    """获取工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_session(id_or_name)


def list_sessions(status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
    """列出工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.list_sessions(status, workflow_id)


def update_session(id_or_name: str, data: Dict[str, Any]) -> Optional[FlowSession]:
    """更新工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.update_session(id_or_name, data)
        db_session.commit()
        return result


def delete_session(id_or_name: str) -> bool:
    """删除工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.delete_session(id_or_name)
        db_session.commit()
        return result


# 会话状态管理
def start_session(id_or_name: str) -> Optional[FlowSession]:
    """启动工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.start_session(id_or_name)
        db_session.commit()
        return result


def pause_session(id_or_name: str) -> Optional[FlowSession]:
    """暂停工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.pause_session(id_or_name)
        db_session.commit()
        return result


def resume_session(id_or_name: str) -> Optional[FlowSession]:
    """恢复工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.resume_session(id_or_name)
        db_session.commit()
        return result


def complete_session(id_or_name: str) -> Optional[FlowSession]:
    """完成工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.complete_session(id_or_name)
        db_session.commit()
        return result


def close_session(id_or_name: str) -> Optional[FlowSession]:
    """关闭工作流会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.close_session(id_or_name)
        db_session.commit()
        return result


# 会话上下文管理
def get_session_context(id_or_name: str) -> Dict[str, Any]:
    """获取会话上下文"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_session_context(id_or_name)


def update_session_context(id_or_name: str, context: Dict[str, Any]) -> bool:
    """更新会话上下文"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.update_session_context(id_or_name, context)
        db_session.commit()
        return result


def clear_session_context(id_or_name: str) -> bool:
    """清除会话上下文"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.clear_session_context(id_or_name)
        db_session.commit()
        return result


# 当前会话管理
def get_current_session() -> Optional[FlowSession]:
    """获取当前会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_current_session()


def switch_session(id_or_name: str) -> Optional[FlowSession]:
    """切换到指定会话"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.switch_session(id_or_name)
        db_session.commit()
        return result


def set_current_session(id_or_name: str) -> Optional[FlowSession]:
    """设置当前会话

    与switch_session功能相同，保留此命名以保持接口一致性

    Args:
        id_or_name: 会话ID或名称

    Returns:
        设置的会话对象
    """
    return switch_session(id_or_name)


# 阶段相关操作
def get_session_stages(id_or_name: str) -> List[Any]:
    """获取会话的所有阶段"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_session_stages(id_or_name)


def get_session_first_stage(id_or_name: str) -> Optional[Any]:
    """获取会话的第一个阶段"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_session_first_stage(id_or_name)


def get_session_progress(id_or_name: str) -> Dict[str, Any]:
    """获取会话的进度"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_session_progress(id_or_name)


def set_current_stage(id_or_name: str, stage_id: str) -> bool:
    """设置会话的当前阶段"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        result = manager.set_current_stage(id_or_name, stage_id)
        db_session.commit()
        return result


def get_next_stages(id_or_name: str, current_stage_id: Optional[str] = None) -> List[Any]:
    """获取会话的下一个阶段"""
    with get_session_factory()() as db_session:
        manager = FlowSessionManager(session=db_session)
        return manager.get_next_stages(id_or_name, current_stage_id)

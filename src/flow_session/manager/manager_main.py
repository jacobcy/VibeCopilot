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
from src.models.db import FlowSession


class FlowSessionManager(FlowSessionManagerBase, SessionCRUDMixin, SessionStateMixin, SessionContextMixin, CurrentSessionMixin):
    """工作流会话管理器，整合所有会话管理功能"""

    # 这里可以添加任何需要覆盖或增强的方法
    pass


# 创建数据库会话
db_session = get_session_factory()()

# 创建一个全局的单例实例，使用数据库会话
_manager = FlowSessionManager(session=db_session)

# ============= 函数导出 =============
# 这些函数是FlowSessionManager实例方法的包装器
# 提供函数式API，简化调用


# 会话CRUD操作
def create_session(workflow_id: str, name: Optional[str] = None, task_id: Optional[str] = None) -> FlowSession:
    """创建工作流会话"""
    return _manager.create_session(workflow_id, name, task_id)


def get_session(id_or_name: str) -> Optional[FlowSession]:
    """获取工作流会话"""
    return _manager.get_session(id_or_name)


def list_sessions(status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
    """获取工作流会话列表"""
    return _manager.list_sessions(status, workflow_id)


def update_session(id_or_name: str, data: Dict[str, Any]) -> Optional[FlowSession]:
    """更新工作流会话"""
    return _manager.update_session(id_or_name, data)


def delete_session(id_or_name: str) -> bool:
    """删除工作流会话"""
    return _manager.delete_session(id_or_name)


# 会话状态管理
def start_session(id_or_name: str) -> Optional[FlowSession]:
    """启动工作流会话"""
    return _manager.start_session(id_or_name)


def pause_session(id_or_name: str) -> Optional[FlowSession]:
    """暂停工作流会话"""
    return _manager.pause_session(id_or_name)


def resume_session(id_or_name: str) -> Optional[FlowSession]:
    """恢复工作流会话"""
    return _manager.resume_session(id_or_name)


def complete_session(id_or_name: str) -> Optional[FlowSession]:
    """完成工作流会话"""
    return _manager.complete_session(id_or_name)


def close_session(id_or_name: str) -> Optional[FlowSession]:
    """结束工作流会话"""
    return _manager.close_session(id_or_name)


# 会话上下文管理
def get_session_context(id_or_name: str) -> Dict[str, Any]:
    """获取会话上下文"""
    return _manager.get_session_context(id_or_name)


def update_session_context(id_or_name: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """更新会话上下文"""
    return _manager.update_session_context(id_or_name, context_data)


def clear_session_context(id_or_name: str) -> bool:
    """清除会话上下文"""
    return _manager.clear_session_context(id_or_name)


# 当前会话管理
def get_current_session() -> Optional[FlowSession]:
    """获取当前会话"""
    return _manager.get_current_session()


def switch_session(id_or_name: str) -> FlowSession:
    """切换当前会话"""
    return _manager.switch_session(id_or_name)


def set_current_session(id_or_name: str) -> Optional[FlowSession]:
    """设置当前会话

    与switch_session功能相同，保留此命名以保持接口一致性

    Args:
        id_or_name: 会话ID或名称

    Returns:
        设置的会话对象
    """
    return _manager.switch_session(id_or_name)


# 阶段相关操作
def get_session_stages(id_or_name: str) -> List[Any]:
    """获取会话阶段列表"""
    return _manager.get_session_stages(id_or_name)


def get_session_first_stage(id_or_name: str) -> Optional[str]:
    """获取会话的第一个阶段ID

    当会话没有当前阶段时，可用此方法获取第一个可用阶段。
    在解释会话场景特别有用。

    Args:
        id_or_name: 会话ID或名称

    Returns:
        第一个阶段ID，如果找不到则返回None
    """
    return _manager.get_session_first_stage(id_or_name)


def get_session_progress(id_or_name: str) -> Dict[str, Any]:
    """获取会话进度"""
    return _manager.get_session_progress(id_or_name)


def set_current_stage(id_or_name: str, stage_id: str) -> bool:
    """设置当前阶段"""
    return _manager.set_current_stage(id_or_name, stage_id)


def get_next_stages(id_or_name: str, current_stage_id: Optional[str] = None) -> List[Any]:
    """获取会话可能的下一阶段"""
    return _manager.get_next_stages(id_or_name, current_stage_id)

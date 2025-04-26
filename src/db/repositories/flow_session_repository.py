"""
Flow Session Repository Module

Provides data access functionality for FlowSession entities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import FlowSession  # Only import FlowSession model
from src.utils.id_generator import EntityType, IdGenerator

# 创建日志记录器
logger = logging.getLogger(__name__)


class FlowSessionRepository(Repository[FlowSession]):
    """工作流会话仓库 (无状态)"""

    def __init__(self):
        """初始化 (不再存储 session)"""
        super().__init__(FlowSession)

    def create_session(
        self,
        session: Session,
        workflow_id: str,
        name: str,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        flow_type: Optional[str] = None,
    ) -> FlowSession:
        """创建工作流会话

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流定义ID
            name: 会话名称
            task_id: 关联的任务ID (可选)
            context: 会话上下文 (可选)
            flow_type: 工作流类型 (可选)

        Returns:
            新创建的工作流会话

        Raises:
            ValueError: 如果提供的参数无效
        """
        logger.debug(f"创建工作流会话: workflow_id={workflow_id}, name={name}")

        # 使用ID生成器生成标准格式的ID
        session_id = IdGenerator.generate_session_id()

        # 准备会话数据
        session_data = {
            "id": session_id,
            "workflow_id": workflow_id,
            "name": name,
            "status": "ACTIVE",
            "task_id": task_id,
            "flow_type": flow_type,
            "context": context or {},
            # "is_current": True,  # 移除is_current字段
        }

        # 移除清除其他当前会话状态的代码
        # current_sessions = session.query(FlowSession).filter(FlowSession.is_current == True).all()
        # for current in current_sessions:
        #     current.is_current = False

        # 创建新会话
        try:
            # 使用Repository基类的create方法
            new_session = super().create(session, session_data)
            # session.flush() # Let caller manage transaction boundaries
            return new_session
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise ValueError(f"创建会话失败: {e}")

    def get_all(self, session: Session) -> List[FlowSession]:
        """获取所有会话

        重写父类的get_all方法，确保返回FlowSession对象列表而非字典列表

        Returns:
            会话对象列表
        """
        logger.debug("FlowSessionRepository.get_all() 被调用")
        sessions = super().get_all(session, as_dict=False)
        logger.debug(f"获取到 {len(sessions)} 个会话对象")

        for i, s in enumerate(sessions):
            logger.debug(f"会话 {i+1}: ID={s.id}, 名称={s.name}, 工作流={s.workflow_id}, 状态={s.status}")

        return sessions

    def get_active_sessions(self, session: Session) -> List[FlowSession]:
        """获取所有活动中的会话

        Returns:
            活动会话列表
        """
        return session.query(FlowSession).filter(FlowSession.status == "ACTIVE").all()

    def get_by_status(self, session: Session, status: str) -> List[FlowSession]:
        """根据状态获取会话列表

        Args:
            session: SQLAlchemy 会话对象
            status: 会话状态

        Returns:
            会话列表
        """
        return session.query(FlowSession).filter(FlowSession.status == status).all()

    def get_by_workflow_id(self, session: Session, workflow_id: str) -> List[FlowSession]:
        """根据工作流ID获取会话列表

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        # Assuming workflow_id refers to the definition ID/name stored on the session
        # Adjust field name if necessary (e.g., FlowSession.definition_id)
        return session.query(FlowSession).filter(FlowSession.workflow_id == workflow_id).all()

    def get_by_workflow_and_status(self, session: Session, workflow_id: str, status: str) -> List[FlowSession]:
        """根据工作流ID和状态获取会话列表

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流ID
            status: 会话状态

        Returns:
            会话列表
        """
        return session.query(FlowSession).filter(and_(FlowSession.workflow_id == workflow_id, FlowSession.status == status)).all()

    def exists_with_name(self, session: Session, name: str) -> bool:
        """检查是否存在具有完全相同名称的会话"""
        return session.query(session.query(FlowSession).filter(FlowSession.name == name).exists()).scalar()

    # get_with_stage_instances might be less useful now as StageInstanceRepository exists
    # Consider removing or adjusting if lazy loading isn't sufficient
    def get_with_stage_instances(self, session: Session, session_id: str) -> Optional[FlowSession]:
        """获取会话及其阶段实例 (using relationship loading)

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID

        Returns:
            会话对象或None
        """
        # This relies on the relationship defined in the FlowSession model
        return session.query(FlowSession).filter(FlowSession.id == session_id).first()

    def update_status(self, session: Session, session_id: str, status: str) -> Optional[FlowSession]:
        """更新会话状态

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            status: 新状态

        Returns:
            更新后的会话对象或None
        """
        flow_session_obj = self.get_by_id(session, session_id)
        if not flow_session_obj:
            return None

        flow_session_obj.status = status
        flow_session_obj.updated_at = datetime.utcnow()
        # session.flush() # Let caller manage transaction boundaries
        return flow_session_obj

    def update_current_stage(self, session: Session, session_id: str, stage_id_or_name: str) -> Optional[FlowSession]:
        """更新会话当前阶段 (by stage ID or name)

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_id_or_name: 阶段ID或名称

        Returns:
            更新后的会话对象或None
        """
        flow_session_obj = self.get_by_id(session, session_id)
        if not flow_session_obj:
            return None

        # Assuming the session model stores the current stage identifier
        # Adjust field name if necessary (e.g., current_stage_name)
        flow_session_obj.current_stage_id = stage_id_or_name
        flow_session_obj.updated_at = datetime.utcnow()
        # session.flush() # Let caller manage transaction boundaries
        return flow_session_obj

    def add_completed_stage(self, session: Session, session_id: str, stage_id_or_name: str) -> Optional[FlowSession]:
        """添加已完成阶段 (by stage ID or name)

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_id_or_name: 已完成阶段ID或名称

        Returns:
            更新后的会话对象或None
        """
        # Use passed session to get object
        flow_session_obj = self.get_by_id(session, session_id)
        if not flow_session_obj:
            return None

        # Use flow_session_obj, not session
        if not flow_session_obj.completed_stages:
            flow_session_obj.completed_stages = []

        if stage_id_or_name not in flow_session_obj.completed_stages:
            # Use flow_session_obj
            new_list = list(flow_session_obj.completed_stages)
            new_list.append(stage_id_or_name)
            flow_session_obj.completed_stages = new_list

            flow_session_obj.updated_at = datetime.utcnow()
            # self.session.commit() # Remove commit

        # Return the correct object
        return flow_session_obj

    def update_context(self, session: Session, session_id: str, context: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话上下文

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            context: 上下文数据

        Returns:
            更新后的会话对象或None
        """
        # Use passed session to get object
        flow_session_obj = self.get_by_id(session, session_id)
        if not flow_session_obj:
            return None

        # Use flow_session_obj, not session
        if not flow_session_obj.context:
            flow_session_obj.context = {}

        # Use flow_session_obj
        new_context = dict(flow_session_obj.context)
        new_context.update(context)
        flow_session_obj.context = new_context

        flow_session_obj.updated_at = datetime.utcnow()
        # self.session.commit() # Remove commit

        # Return the correct object
        return flow_session_obj

    def get_by_name(self, session: Session, name: str) -> Optional[FlowSession]:
        """根据会话名称获取会话

        Args:
            session: SQLAlchemy 会话对象
            name: 会话名称

        Returns:
            会话对象或None
        """
        return session.query(FlowSession).filter(FlowSession.name == name).first()

    def find_session_by_id_or_name(self, session: Session, id_or_name: str) -> Optional[FlowSession]:
        """根据ID或名称查找会话

        首先尝试按ID查找，如果没有找到，再按名称查找

        Args:
            session: SQLAlchemy 会话对象
            id_or_name: 会话ID或名称

        Returns:
            会话对象或None
        """
        # First try finding by ID
        session_obj = self.get_by_id(session, id_or_name)
        if session_obj:
            return session_obj
        # If not found by ID, try finding by name
        return self.get_by_name(session, id_or_name)

    def link_to_task(self, session: Session, session_id: str, task_id: Optional[str]) -> Optional[FlowSession]:
        """关联或取消关联会话到任务

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            task_id: 任务ID，None表示取消关联

        Returns:
            更新后的会话对象或None
        """
        flow_session_obj = self.get_by_id(session, session_id)
        if not flow_session_obj:
            return None
        flow_session_obj.task_id = task_id
        flow_session_obj.updated_at = datetime.utcnow()
        # self.session.commit() # Remove commit
        return flow_session_obj

    def get_by_task_id(self, session: Session, task_id: str) -> List[FlowSession]:
        """根据任务ID获取相关的所有会话

        Args:
            session: SQLAlchemy 会话对象
            task_id: 任务ID

        Returns:
            会话列表
        """
        return session.query(FlowSession).filter(FlowSession.task_id == task_id).all()

    # 注释掉 set_current_session 方法
    # def set_current_session(self, session: Session, session_id: str) -> bool:
    #    """设置当前会话
    #
    #    Args:
    #        session: SQLAlchemy 会话对象
    #        session_id: 会话ID
    #
    #    Returns:
    #        是否成功设置
    #    """
    #    try:
    #        # Clear other current sessions
    #        session.query(FlowSession).filter(FlowSession.is_current == True).update({"is_current": False})
    #        # Set the new current session
    #        flow_session_obj = self.get_by_id(session, session_id)
    #        if flow_session_obj:
    #            flow_session_obj.is_current = True
    #            # session.commit() # Remove commit
    #            return True
    #        return False
    #    except Exception as e:
    #        # session.rollback() # Let caller handle rollback
    #        logger.error(f"设置当前会话失败: {e}")
    #        return False

"""
工作流会话数据仓库模块

提供工作流会话相关的数据访问功能，包括会话和阶段实例的CRUD操作。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import FlowSession, StageInstance, WorkflowDefinition


class WorkflowDefinitionRepository(Repository[WorkflowDefinition]):
    """工作流定义仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowDefinition)

    def get_by_name(self, name: str) -> Optional[WorkflowDefinition]:
        """根据名称获取工作流定义

        Args:
            name: 工作流名称

        Returns:
            工作流定义对象或None
        """
        return (
            self.session.query(WorkflowDefinition).filter(WorkflowDefinition.name == name).first()
        )

    def get_by_type(self, type_name: str) -> List[WorkflowDefinition]:
        """根据类型获取工作流定义列表

        Args:
            type_name: 工作流类型

        Returns:
            工作流定义对象列表
        """
        return (
            self.session.query(WorkflowDefinition)
            .filter(WorkflowDefinition.type == type_name)
            .all()
        )


class FlowSessionRepository(Repository[FlowSession]):
    """工作流会话仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, FlowSession)

    def get_active_sessions(self) -> List[FlowSession]:
        """获取所有活动中的会话

        Returns:
            活动会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.status == "ACTIVE").all()

    def get_by_status(self, status: str) -> List[FlowSession]:
        """根据状态获取会话列表

        Args:
            status: 会话状态

        Returns:
            会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.status == status).all()

    def get_by_workflow_id(self, workflow_id: str) -> List[FlowSession]:
        """根据工作流ID获取会话列表

        Args:
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.workflow_id == workflow_id).all()

    def get_by_workflow_and_status(self, workflow_id: str, status: str) -> List[FlowSession]:
        """根据工作流ID和状态获取会话列表

        Args:
            workflow_id: 工作流ID
            status: 会话状态

        Returns:
            会话列表
        """
        return (
            self.session.query(FlowSession)
            .filter(and_(FlowSession.workflow_id == workflow_id, FlowSession.status == status))
            .all()
        )

    def get_with_stage_instances(self, session_id: str) -> Optional[FlowSession]:
        """获取会话及其阶段实例

        Args:
            session_id: 会话ID

        Returns:
            会话对象或None
        """
        return self.session.query(FlowSession).filter(FlowSession.id == session_id).first()

    def update_status(self, session_id: str, status: str) -> Optional[FlowSession]:
        """更新会话状态

        Args:
            session_id: 会话ID
            status: 新状态

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        session.status = status
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session

    def update_current_stage(self, session_id: str, stage_id: str) -> Optional[FlowSession]:
        """更新会话当前阶段

        Args:
            session_id: 会话ID
            stage_id: 阶段ID

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        session.current_stage_id = stage_id
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session

    def add_completed_stage(self, session_id: str, stage_id: str) -> Optional[FlowSession]:
        """添加已完成阶段

        Args:
            session_id: 会话ID
            stage_id: 已完成阶段ID

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        if not session.completed_stages:
            session.completed_stages = []

        if stage_id not in session.completed_stages:
            session.completed_stages.append(stage_id)
            session.updated_at = datetime.utcnow()
            self.session.commit()

        return session

    def update_context(self, session_id: str, context: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话上下文

        Args:
            session_id: 会话ID
            context: 上下文数据

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        if not session.context:
            session.context = {}

        session.context.update(context)
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session


class StageInstanceRepository(Repository[StageInstance]):
    """阶段实例仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, StageInstance)

    def get_by_session_id(self, session_id: str) -> List[StageInstance]:
        """根据会话ID获取阶段实例列表

        Args:
            session_id: 会话ID

        Returns:
            阶段实例列表
        """
        return (
            self.session.query(StageInstance).filter(StageInstance.session_id == session_id).all()
        )

    def get_by_session_and_stage(self, session_id: str, stage_id: str) -> Optional[StageInstance]:
        """根据会话ID和阶段ID获取阶段实例

        Args:
            session_id: 会话ID
            stage_id: 阶段ID

        Returns:
            阶段实例对象或None
        """
        return (
            self.session.query(StageInstance)
            .filter(
                and_(StageInstance.session_id == session_id, StageInstance.stage_id == stage_id)
            )
            .first()
        )

    def get_by_status(self, status: str) -> List[StageInstance]:
        """根据状态获取阶段实例列表

        Args:
            status: 阶段状态

        Returns:
            阶段实例列表
        """
        return self.session.query(StageInstance).filter(StageInstance.status == status).all()

    def get_by_session_and_status(self, session_id: str, status: str) -> List[StageInstance]:
        """根据会话ID和状态获取阶段实例列表

        Args:
            session_id: 会话ID
            status: 阶段状态

        Returns:
            阶段实例列表
        """
        return (
            self.session.query(StageInstance)
            .filter(and_(StageInstance.session_id == session_id, StageInstance.status == status))
            .all()
        )

    def update_status(self, instance_id: str, status: str) -> Optional[StageInstance]:
        """更新阶段实例状态

        Args:
            instance_id: 阶段实例ID
            status: 新状态

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        instance.status = status

        # 根据状态更新时间字段
        if status == "ACTIVE" and not instance.started_at:
            instance.started_at = datetime.utcnow()
        elif status in ["COMPLETED", "FAILED"] and not instance.completed_at:
            instance.completed_at = datetime.utcnow()

        self.session.commit()
        return instance

    def add_completed_item(self, instance_id: str, item_id: str) -> Optional[StageInstance]:
        """添加已完成项

        Args:
            instance_id: 阶段实例ID
            item_id: 已完成项ID

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.completed_items:
            instance.completed_items = []

        if item_id not in instance.completed_items:
            instance.completed_items.append(item_id)
            self.session.commit()

        return instance

    def update_context(self, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段上下文

        Args:
            instance_id: 阶段实例ID
            context: 上下文数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.context:
            instance.context = {}

        instance.context.update(context)
        self.session.commit()
        return instance

    def update_deliverables(
        self, instance_id: str, deliverables: Dict[str, Any]
    ) -> Optional[StageInstance]:
        """更新阶段交付物

        Args:
            instance_id: 阶段实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.deliverables:
            instance.deliverables = {}

        instance.deliverables.update(deliverables)
        self.session.commit()
        return instance

    def complete_instance(
        self, instance_id: str, deliverables: Optional[Dict[str, Any]] = None
    ) -> Optional[StageInstance]:
        """完成阶段实例

        Args:
            instance_id: 阶段实例ID
            deliverables: 可选的交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        instance.status = "COMPLETED"
        instance.completed_at = datetime.utcnow()

        if deliverables:
            if not instance.deliverables:
                instance.deliverables = {}
            instance.deliverables.update(deliverables)

        self.session.commit()
        return instance

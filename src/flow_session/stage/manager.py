"""
阶段实例管理器核心类模块

提供StageInstanceManager类的核心功能定义。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import get_session_factory  # 重新添加 get_session_factory 的导入

# from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository, get_session_factory # 旧导入
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db import StageInstance


class StageInstanceManager:
    """阶段实例管理器，处理阶段实例的CRUD操作 (无状态)"""

    def __init__(self):
        """初始化 (不再存储 session)"""
        # self.session = session # Removed
        # Initialize repos without session
        self.workflow_repo = WorkflowDefinitionRepository()
        self.session_repo = FlowSessionRepository()
        self.stage_repo = StageInstanceRepository()

    def create_instance(self, session: Session, session_id: str, stage_data: Dict[str, Any]) -> Optional[StageInstance]:
        """创建新的阶段实例

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_data: 阶段数据，包含stage_id和name等信息

        Returns:
            新创建的阶段实例或None

        Raises:
            ValueError: 如果找不到指定ID的会话
        """
        # Pass session to repo call
        flow_session = self.session_repo.get_by_id(session, session_id)
        if not flow_session:
            raise ValueError(f"找不到ID为 {session_id} 的会话")

        stage_id = stage_data.get("stage_id") or stage_data.get("id")
        name = stage_data.get("name", f"阶段-{stage_id}")

        # Pass session to repo call
        existing_instance = self.stage_repo.get_by_session_and_stage(session, session_id, stage_id)
        if existing_instance:
            return existing_instance

        # Pass session to repo call
        workflow = self.workflow_repo.get_by_id(session, flow_session.workflow_id)
        if not workflow or not workflow.stages:
            raise ValueError(f"工作流定义无效或不包含阶段信息")

        # 查找阶段定义
        stage_def = next((s for s in workflow.stages if s.get("id") == stage_id), None)
        if not stage_def:
            raise ValueError(f"找不到ID为 {stage_id} 的阶段定义")

        # 生成实例ID
        instance_id = f"stage-{uuid.uuid4()}"

        # 创建阶段实例
        instance_data = {
            "id": instance_id,
            "session_id": session_id,
            "stage_id": stage_id,
            "name": name,
            "status": "PENDING",
            "completed_items": [],
            "context": {},
            "deliverables": {},
        }

        # Pass session to repo call
        stage_instance = self.stage_repo.create(session, instance_data)

        # Pass session to repo call
        self.session_repo.update_current_stage(session, session_id, stage_id)

        return stage_instance

    def get_instance(self, session: Session, instance_id: str) -> Optional[StageInstance]:
        """获取阶段实例详情

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID

        Returns:
            阶段实例对象或None
        """
        # Pass session to repo call
        return self.stage_repo.get_by_id(session, instance_id)

    def get_session_instances(self, session: Session, session_id: str) -> List[StageInstance]:
        """获取会话的所有阶段实例

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID

        Returns:
            阶段实例列表
        """
        # Pass session to repo call
        return self.stage_repo.get_by_session_id(session, session_id)

    def list_instances(self, session: Session, session_id: Optional[str] = None, status: Optional[str] = None) -> List[StageInstance]:
        """列出阶段实例，可按会话ID和状态过滤

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            status: 阶段状态

        Returns:
            阶段实例列表
        """
        # Pass session to repo calls
        if session_id and status:
            return self.stage_repo.get_by_session_and_status(session, session_id, status)
        elif session_id:
            return self.stage_repo.get_by_session_id(session, session_id)
        elif status:
            return self.stage_repo.get_by_status(session, status)
        else:
            return self.stage_repo.get_all(session)

    def update_instance(self, session: Session, instance_id: str, data: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例数据

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            data: 更新数据

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo call
        return self.stage_repo.update(session, instance_id, data)

    def start_instance(self, session: Session, instance_id: str) -> Optional[StageInstance]:
        """开始阶段实例

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo calls
        instance = self.stage_repo.get_by_id(session, instance_id)
        if not instance:
            return None

        # 更新状态为激活
        return self.stage_repo.update_status(session, instance_id, "ACTIVE")

    def complete_stage(self, session: Session, instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
        """完成阶段实例

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            context: 上下文数据 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo calls
        instance = self.stage_repo.get_by_id(session, instance_id)
        if not instance:
            return None

        # 如果有上下文，先更新上下文
        if context:
            self.stage_repo.update_context(session, instance_id, context)

        # 标记为已完成
        completed_instance = self.stage_repo.update_status(session, instance_id, "COMPLETED")

        # 更新会话中的已完成阶段列表
        if completed_instance:
            self.session_repo.add_completed_stage(session, completed_instance.session_id, completed_instance.stage_id)

        return completed_instance

    def fail_stage(self, session: Session, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
        """标记阶段实例为失败

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            reason: 失败原因 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo calls
        instance = self.stage_repo.get_by_id(session, instance_id)
        if not instance:
            return None

        # 更新错误信息
        if reason:
            context = instance.context or {}
            context["error"] = reason
            self.stage_repo.update_context(session, instance_id, context)

        # 标记为失败
        return self.stage_repo.update_status(session, instance_id, "FAILED")

    def skip_stage(self, session: Session, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
        """跳过阶段实例

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            reason: 跳过原因 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo calls
        instance = self.stage_repo.get_by_id(session, instance_id)
        if not instance:
            return None

        # 更新跳过信息
        if reason:
            context = instance.context or {}
            context["skip_reason"] = reason
            self.stage_repo.update_context(session, instance_id, context)

        # 标记为已跳过
        return self.stage_repo.update_status(session, instance_id, "SKIPPED")

    def add_completed_item(self, session: Session, instance_id: str, item_id: str) -> Optional[StageInstance]:
        """添加已完成项

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            item_id: 项目ID

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo call
        return self.stage_repo.add_completed_item(session, instance_id, item_id)

    def update_context(self, session: Session, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例上下文

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            context: 上下文数据

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo call
        return self.stage_repo.update_context(session, instance_id, context)

    def update_deliverables(self, session: Session, instance_id: str, deliverables: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例交付物

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        # Pass session to repo call
        return self.stage_repo.update_deliverables(session, instance_id, deliverables)

    def get_instance_progress(self, session: Session, instance_id: str) -> Dict[str, Any]:
        """获取阶段实例的进度信息

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 阶段实例ID

        Returns:
            包含阶段实例进度信息的字典

        Raises:
            ValueError: 如果找不到指定的阶段实例
        """
        # Pass session to repo call
        instance = self.stage_repo.get_by_id(session, instance_id)
        if not instance:
            return {"error": "找不到阶段实例"}

        # 获取工作流定义以获取总步骤数
        flow_session = self.session_repo.get_by_id(session, instance.session_id)
        if not flow_session:
            return {"error": "找不到关联的会话"}

        # Pass session to repo call
        workflow = self.workflow_repo.get_by_id(session, flow_session.workflow_id)
        if not workflow or not workflow.stages:
            return {"error": "找不到有效的工作流定义"}

        # 查找当前阶段定义
        stage_def = next((s for s in workflow.stages if s.get("id") == instance.stage_id), None)
        if not stage_def:
            return {"error": "找不到阶段定义"}

        # 获取总步骤数（假设定义中有steps字段）
        total_steps = len(stage_def.get("items", [])) or stage_def.get("total_steps", 1)  # Fallback
        completed_steps = len(instance.completed_items or [])
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0

        return {
            "instance_id": instance_id,
            "stage_id": instance.stage_id,
            "name": instance.name,
            "status": instance.status,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress": round(progress, 2),
            "context": instance.context or {},
        }


# 创建数据库会话
db_session = get_session_factory()()

# ============= 函数导出 =============
# 这些函数是StageInstanceManager实例方法的包装器
# 提供函数式API，简化调用


def get_stage_instance(session: Session, instance_id: str) -> Optional[StageInstance]:
    """便利函数: 获取阶段实例"""
    # Needs session scope outside
    # _manager = StageInstanceManager(session=session) # Old way
    _manager = StageInstanceManager()  # New way
    return _manager.get_instance(session, instance_id)


def get_stages_for_session(session: Session, session_id: str) -> List[StageInstance]:
    """便利函数: 获取会话的所有阶段实例"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.get_session_instances(session, session_id)


def create_stage_instance(session: Session, session_id: str, stage_data: Dict[str, Any]) -> Optional[StageInstance]:
    """便利函数: 创建阶段实例"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.create_instance(session, session_id, stage_data)


def complete_stage(session: Session, instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
    """便利函数: 完成阶段"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.complete_stage(session, instance_id, context)


def fail_stage(session: Session, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
    """便利函数: 失败阶段"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.fail_stage(session, instance_id, reason)


def skip_stage(session: Session, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
    """便利函数: 跳过阶段"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.skip_stage(session, instance_id, reason)


def update_stage_context(session: Session, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
    """便利函数: 更新阶段上下文"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.update_context(session, instance_id, context)


def get_stage_progress(session: Session, instance_id: str) -> Dict[str, Any]:
    """便利函数: 获取阶段进度"""
    # Needs session scope outside
    _manager = StageInstanceManager()
    return _manager.get_instance_progress(session, instance_id)

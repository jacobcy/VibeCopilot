"""
阶段实例管理器核心类模块

提供StageInstanceManager类的核心功能定义。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository, get_session_factory
from src.models.db import StageInstance


class StageInstanceManager:
    """阶段实例管理器，处理阶段实例的CRUD操作"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository(session)
        self.session_repo = FlowSessionRepository(session)
        self.stage_repo = StageInstanceRepository(session)

    def create_instance(self, session_id: str, stage_data: Dict[str, Any]) -> Optional[StageInstance]:
        """创建新的阶段实例

        Args:
            session_id: 会话ID
            stage_data: 阶段数据，包含stage_id和name等信息

        Returns:
            新创建的阶段实例或None

        Raises:
            ValueError: 如果找不到指定ID的会话
        """
        # 检查会话是否存在
        flow_session = self.session_repo.get_by_id(session_id)
        if not flow_session:
            raise ValueError(f"找不到ID为 {session_id} 的会话")

        stage_id = stage_data.get("stage_id") or stage_data.get("id")
        name = stage_data.get("name", f"阶段-{stage_id}")

        # 检查是否已存在相同阶段实例
        existing_instance = self.stage_repo.get_by_session_and_stage(session_id, stage_id)
        if existing_instance:
            return existing_instance

        # 获取工作流定义以验证阶段是否存在
        workflow = self.workflow_repo.get_by_id(flow_session.workflow_id)
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

        # 创建阶段实例
        stage_instance = self.stage_repo.create(instance_data)

        # 更新会话的当前阶段
        self.session_repo.update_current_stage(session_id, stage_id)

        return stage_instance

    def get_instance(self, instance_id: str) -> Optional[StageInstance]:
        """获取阶段实例详情

        Args:
            instance_id: 阶段实例ID

        Returns:
            阶段实例对象或None
        """
        return self.stage_repo.get_by_id(instance_id)

    def get_session_instances(self, session_id: str) -> List[StageInstance]:
        """获取会话的所有阶段实例

        Args:
            session_id: 会话ID

        Returns:
            阶段实例列表
        """
        return self.stage_repo.get_by_session_id(session_id)

    def list_instances(self, session_id: Optional[str] = None, status: Optional[str] = None) -> List[StageInstance]:
        """列出阶段实例，可按会话ID和状态过滤

        Args:
            session_id: 会话ID
            status: 阶段状态

        Returns:
            阶段实例列表
        """
        if session_id and status:
            return self.stage_repo.get_by_session_and_status(session_id, status)
        elif session_id:
            return self.stage_repo.get_by_session_id(session_id)
        elif status:
            return self.stage_repo.get_by_status(status)
        else:
            return self.stage_repo.get_all()

    def update_instance(self, instance_id: str, data: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例数据

        Args:
            instance_id: 阶段实例ID
            data: 更新数据

        Returns:
            更新后的阶段实例对象或None
        """
        return self.stage_repo.update(instance_id, data)

    def start_instance(self, instance_id: str) -> Optional[StageInstance]:
        """开始阶段实例

        Args:
            instance_id: 阶段实例ID

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 更新状态为激活
        return self.stage_repo.update_status(instance_id, "ACTIVE")

    def complete_stage(self, instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
        """完成阶段实例

        Args:
            instance_id: 阶段实例ID
            context: 上下文数据 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 如果有上下文，先更新上下文
        if context:
            self.stage_repo.update_context(instance_id, context)

        # 标记为已完成
        completed_instance = self.stage_repo.update_status(instance_id, "COMPLETED")

        # 更新会话中的已完成阶段列表
        if completed_instance:
            self.session_repo.add_completed_stage(completed_instance.session_id, completed_instance.stage_id)

        return completed_instance

    def fail_stage(self, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
        """标记阶段实例为失败

        Args:
            instance_id: 阶段实例ID
            reason: 失败原因 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 更新错误信息
        if reason:
            context = instance.context or {}
            context["error"] = reason
            self.stage_repo.update_context(instance_id, context)

        # 标记为失败
        return self.stage_repo.update_status(instance_id, "FAILED")

    def skip_stage(self, instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
        """跳过阶段实例

        Args:
            instance_id: 阶段实例ID
            reason: 跳过原因 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 更新跳过信息
        if reason:
            context = instance.context or {}
            context["skip_reason"] = reason
            self.stage_repo.update_context(instance_id, context)

        # 标记为已跳过
        return self.stage_repo.update_status(instance_id, "SKIPPED")

    def add_completed_item(self, instance_id: str, item_id: str) -> Optional[StageInstance]:
        """添加已完成项

        Args:
            instance_id: 阶段实例ID
            item_id: 项目ID

        Returns:
            更新后的阶段实例对象或None
        """
        return self.stage_repo.add_completed_item(instance_id, item_id)

    def update_context(self, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例上下文

        Args:
            instance_id: 阶段实例ID
            context: 上下文数据

        Returns:
            更新后的阶段实例对象或None
        """
        return self.stage_repo.update_context(instance_id, context)

    def update_deliverables(self, instance_id: str, deliverables: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例交付物

        Args:
            instance_id: 阶段实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        return self.stage_repo.update_deliverables(instance_id, deliverables)

    def get_instance_progress(self, instance_id: str) -> Dict[str, Any]:
        """获取阶段实例的进度信息

        Args:
            instance_id: 阶段实例ID

        Returns:
            包含阶段实例进度信息的字典

        Raises:
            ValueError: 如果找不到指定的阶段实例
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            raise ValueError(f"找不到ID为 {instance_id} 的阶段实例")

        # 获取进度信息
        progress = {
            "id": instance.id,
            "name": instance.name,
            "stage_id": instance.stage_id,
            "status": instance.status,
            "completed_items": instance.completed_items or [],
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
        }

        return progress


# 创建数据库会话
db_session = get_session_factory()()

# 创建一个全局的单例实例，使用数据库会话
_manager = StageInstanceManager(session=db_session)

# ============= 函数导出 =============
# 这些函数是StageInstanceManager实例方法的包装器
# 提供函数式API，简化调用


def get_stage_instance(instance_id: str) -> Optional[StageInstance]:
    """获取阶段实例详情"""
    return _manager.get_instance(instance_id)


def get_stages_for_session(session_id: str) -> List[StageInstance]:
    """获取会话的所有阶段实例"""
    return _manager.get_session_instances(session_id)


def create_stage_instance(session_id: str, stage_data: Dict[str, Any]) -> Optional[StageInstance]:
    """创建阶段实例"""
    return _manager.create_instance(session_id, stage_data)


def complete_stage(instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
    """完成阶段"""
    return _manager.complete_stage(instance_id, context)


def fail_stage(instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
    """标记阶段失败"""
    return _manager.fail_stage(instance_id, reason)


def skip_stage(instance_id: str, reason: Optional[str] = None) -> Optional[StageInstance]:
    """跳过阶段"""
    return _manager.skip_stage(instance_id, reason)


def update_stage_context(instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
    """更新阶段上下文"""
    return _manager.update_context(instance_id, context)


def get_stage_progress(instance_id: str) -> Dict[str, Any]:
    """获取阶段进度"""
    return _manager.get_instance_progress(instance_id)

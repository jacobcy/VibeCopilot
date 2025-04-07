"""
阶段实例管理器核心类模块

提供StageInstanceManager类的核心功能定义。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository
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

    def create_instance(
        self, session_id: str, stage_id: str, name: Optional[str] = None
    ) -> Optional[StageInstance]:
        """创建新的阶段实例

        Args:
            session_id: 会话ID
            stage_id: 阶段ID
            name: 阶段名称，如果不指定则使用阶段ID

        Returns:
            新创建的阶段实例或None

        Raises:
            ValueError: 如果找不到指定ID的会话
        """
        # 检查会话是否存在
        flow_session = self.session_repo.get_by_id(session_id)
        if not flow_session:
            raise ValueError(f"找不到ID为 {session_id} 的会话")

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

        if not name:
            name = stage_def.get("name", f"阶段-{stage_id}")

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

    def list_instances(
        self, session_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[StageInstance]:
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

    def complete_instance(
        self, instance_id: str, deliverables: Optional[Dict[str, Any]] = None
    ) -> Optional[StageInstance]:
        """完成阶段实例

        Args:
            instance_id: 阶段实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 如果有交付物，先更新交付物
        if deliverables:
            self.stage_repo.update_deliverables(instance_id, deliverables)

        # 标记为已完成
        completed_instance = self.stage_repo.update_status(instance_id, "COMPLETED")

        # 更新会话中的已完成阶段列表
        if completed_instance:
            self.session_repo.add_completed_stage(
                completed_instance.session_id, completed_instance.stage_id
            )

        return completed_instance

    def fail_instance(self, instance_id: str, error: str = None) -> Optional[StageInstance]:
        """标记阶段实例为失败

        Args:
            instance_id: 阶段实例ID
            error: 错误信息

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.stage_repo.get_by_id(instance_id)
        if not instance:
            return None

        # 更新错误信息
        if error and instance.context:
            context = instance.context
            context["error"] = error
            self.stage_repo.update_context(instance_id, context)

        # 标记为失败
        return self.stage_repo.update_status(instance_id, "FAILED")

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

    def update_deliverables(
        self, instance_id: str, deliverables: Dict[str, Any]
    ) -> Optional[StageInstance]:
        """更新阶段实例交付物

        Args:
            instance_id: 阶段实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        return self.stage_repo.update_deliverables(instance_id, deliverables)

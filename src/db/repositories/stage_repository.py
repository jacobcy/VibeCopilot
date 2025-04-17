"""
Stage Repository Module

提供对Stage模型的数据库操作，包括查询、创建、更新、删除等。
"""

from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Stage
from src.utils.id_generator import EntityType, IdGenerator


class StageRepository(Repository[Stage]):
    """阶段仓库"""

    def __init__(self):
        # 移除 session 参数，只传入模型类
        super().__init__(Stage)

    def get_all(self, session: Session) -> List[Stage]:
        """获取所有阶段

        Args:
            session: 数据库会话

        Returns:
            List[Stage]: 阶段列表
        """
        # 使用传入的 session
        return session.query(self.model_class).all()

    def get_by_workflow_id(self, session: Session, workflow_id: str) -> List[Stage]:
        """根据工作流ID获取阶段

        Args:
            session: 数据库会话
            workflow_id: 工作流ID

        Returns:
            List[Stage]: 阶段列表
        """
        # 使用传入的 session
        return session.query(self.model_class).filter(self.model_class.workflow_id == workflow_id).order_by(self.model_class.order_index).all()

    def get_by_id(self, session: Session, stage_id: str) -> Optional[Stage]:
        """根据ID获取阶段

        Args:
            session: 数据库会话
            stage_id: 阶段ID

        Returns:
            Optional[Stage]: 阶段，如果不存在则返回None
        """
        # 使用传入的 session
        return session.query(self.model_class).filter(self.model_class.id == stage_id).first()

    def create_stage(
        self,
        session: Session,  # 添加 session 参数
        name: str,
        workflow_id: str,
        order_index: int = 0,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Stage:
        """创建阶段

        Args:
            session: 数据库会话
            name: 阶段名称
            workflow_id: 工作流ID
            order_index: 阶段顺序索引
            description: 阶段描述
            config: 阶段配置

        Returns:
            Stage: 创建的阶段
        """
        # 使用ID生成器生成标准格式的ID
        stage_id = IdGenerator.generate_stage_id()

        # 准备阶段数据
        stage_data = {
            "id": stage_id,
            "name": name,
            "workflow_id": workflow_id,
            "order_index": order_index,
            "description": description or "",
            "config": config or {},
        }

        # 使用基类的create方法创建实例，并传递 session
        # 注意：假设基类的 create 也已被修改为接受 session
        return super().create(session, stage_data)

    def create(self, session: Session, stage_data: dict) -> Stage:
        """创建阶段

        Args:
            session: 数据库会话
            stage_data: 阶段数据

        Returns:
            Stage: 创建的阶段
        """
        stage = Stage(**stage_data)
        # 使用传入的 session 添加
        session.add(stage)
        # 移除 commit，由调用者管理事务
        # session.commit()
        return stage

    def update(self, session: Session, stage_id: str, stage_data: dict) -> Optional[Stage]:
        """更新阶段

        Args:
            session: 数据库会话
            stage_id: 阶段ID
            stage_data: 阶段数据

        Returns:
            Optional[Stage]: 更新后的阶段，如果不存在则返回None
        """
        # 使用传入的 session 调用 get_by_id
        stage = self.get_by_id(session, stage_id)
        if not stage:
            return None

        for key, value in stage_data.items():
            if hasattr(stage, key):
                setattr(stage, key, value)

        # 移除 commit，由调用者管理事务
        # session.commit()
        return stage

    def delete(self, session: Session, stage_id: str) -> bool:
        """删除阶段

        Args:
            session: 数据库会话
            stage_id: 阶段ID

        Returns:
            bool: 是否删除成功
        """
        # 使用传入的 session 调用 get_by_id
        stage = self.get_by_id(session, stage_id)
        if not stage:
            return False

        # 使用传入的 session 删除
        session.delete(stage)
        # 移除 commit，由调用者管理事务
        # session.commit()
        return True

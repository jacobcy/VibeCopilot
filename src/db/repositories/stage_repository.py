"""
Stage Repository Module

提供对Stage模型的数据库操作，包括查询、创建、更新、删除等。
"""

from typing import List, Optional

from sqlalchemy import and_

from src.db.repository import Repository
from src.models.db import Stage


class StageRepository(Repository[Stage]):
    """阶段仓库"""

    def __init__(self, session):
        super().__init__(session, Stage)

    def get_all(self) -> List[Stage]:
        """获取所有阶段

        Returns:
            List[Stage]: 阶段列表
        """
        return self.session.query(Stage).all()

    def get_by_workflow_id(self, workflow_id: str) -> List[Stage]:
        """根据工作流ID获取阶段

        Args:
            workflow_id: 工作流ID

        Returns:
            List[Stage]: 阶段列表
        """
        return self.session.query(Stage).filter(Stage.workflow_id == workflow_id).order_by(Stage.order_index).all()

    def get_by_id(self, stage_id: str) -> Optional[Stage]:
        """根据ID获取阶段

        Args:
            stage_id: 阶段ID

        Returns:
            Optional[Stage]: 阶段，如果不存在则返回None
        """
        return self.session.query(Stage).filter(Stage.id == stage_id).first()

    def create(self, stage_data: dict) -> Stage:
        """创建阶段

        Args:
            stage_data: 阶段数据

        Returns:
            Stage: 创建的阶段
        """
        stage = Stage(**stage_data)
        self.session.add(stage)
        self.session.commit()
        return stage

    def update(self, stage_id: str, stage_data: dict) -> Optional[Stage]:
        """更新阶段

        Args:
            stage_id: 阶段ID
            stage_data: 阶段数据

        Returns:
            Optional[Stage]: 更新后的阶段，如果不存在则返回None
        """
        stage = self.get_by_id(stage_id)
        if not stage:
            return None

        for key, value in stage_data.items():
            if hasattr(stage, key):
                setattr(stage, key, value)

        self.session.commit()
        return stage

    def delete(self, stage_id: str) -> bool:
        """删除阶段

        Args:
            stage_id: 阶段ID

        Returns:
            bool: 是否删除成功
        """
        stage = self.get_by_id(stage_id)
        if not stage:
            return False

        self.session.delete(stage)
        self.session.commit()
        return True

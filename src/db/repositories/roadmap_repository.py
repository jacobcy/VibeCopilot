"""
路线图数据访问对象模块

提供Roadmap、Epic、Milestone、Story、Task等实体的数据访问接口。
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Epic, Milestone, Roadmap, Story
from src.models.db.task import Task


class RoadmapRepository(Repository[Roadmap]):
    """Roadmap仓库 (无状态)"""

    def __init__(self):
        """初始化Roadmap仓库 (不再存储 session)"""
        super().__init__(Roadmap)

    def get_with_related(self, session: Session, roadmap_id: str) -> Optional[Roadmap]:
        """获取Roadmap及其所有关联数据

        Args:
            session: SQLAlchemy 会话对象
            roadmap_id: Roadmap ID

        Returns:
            Roadmap对象或None
        """
        return session.query(Roadmap).filter(Roadmap.id == roadmap_id).first()

    def get_by_name(self, session: Session, name: str) -> Optional[Roadmap]:
        """通过名称获取路线图

        Args:
            session: SQLAlchemy 会话对象
            name: 路线图名称

        Returns:
            Roadmap对象或None
        """
        return session.query(Roadmap).filter(Roadmap.name == name).first()

    def get_stats(self, session: Session, roadmap_id: str) -> Dict[str, Any]:
        """获取路线图统计信息"""
        try:
            # Placeholder - replace with actual queries using 'session'
            # 实际实现应查询数据库获取统计信息
            return {"milestones_count": 5, "epics_count": 8, "stories_count": 15, "tasks_count": 47, "completed_tasks": 23, "overall_progress": 48.9}
        except Exception as e:
            return {"error": str(e)}

    def get_milestones_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 里程碑列表
        """
        from src.models.db import Milestone

        try:
            return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图里程碑时出错: {e}")
            return []

    def get_stories_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有故事

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 故事列表
        """
        from src.models.db import Epic, Story

        try:
            # 通过Epic关联查询
            return self.session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图故事时出错: {e}")
            return []

    def get_tasks_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有任务

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 任务列表
        """
        from src.models.db import Epic, Story, Task

        try:
            # 通过Story和Epic关联查询
            return (
                self.session.query(Task)
                .join(Story, Task.story_id == Story.id)
                .join(Epic, Story.epic_id == Epic.id)
                .filter(Epic.roadmap_id == roadmap_id)
                .all()
            )
        except Exception as e:
            self.logger.error(f"获取路线图任务时出错: {e}")
            return []


class MilestoneRepository(Repository[Milestone]):
    """Milestone仓库"""

    def __init__(self, session: Session):
        """初始化Milestone仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Milestone)

    def get_by_roadmap(self, roadmap_id: str) -> List[Milestone]:
        """获取指定路线图下的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            Milestone对象列表
        """
        return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()

    def get_with_epics(self, milestone_id: str) -> Optional[Milestone]:
        """获取里程碑及其关联的Epics

        Args:
            milestone_id: 里程碑ID

        Returns:
            Milestone对象或None
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id).first()

    def get_by_roadmap_id(self, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 里程碑列表
        """
        try:
            return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图里程碑时出错: {e}")
            return []


class EpicRepository(Repository[Epic]):
    """Epic仓库 (无状态)"""

    def __init__(self):
        """初始化Epic仓库"""
        super().__init__(Epic)

    def get_with_stories(self, session: Session, epic_id: str) -> Optional[Epic]:
        """获取Epic及其关联的Stories"""
        return session.query(Epic).options(joinedload(Epic.stories)).filter(Epic.id == epic_id).first()

    def get_by_id(self, session: Session, entity_id: str) -> Optional[Epic]:
        """通过ID获取Epic (覆盖或实现基类方法)"""
        return session.query(self.model_class).filter(self.model_class.id == entity_id).first()

    def update(self, session: Session, entity_id: str, data: Dict[str, Any]) -> Optional[Epic]:
        """通过ID更新Epic (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model_class.__name__}")
            return entity
        return None

    def delete(self, session: Session, entity_id: str) -> bool:
        """通过ID删除Epic (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            session.delete(entity)
            return True
        return False

    def get_all(self, session: Session, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Epic]:
        """获取所有Epic (覆盖或实现基类方法)"""
        query = session.query(self.model_class)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def create(self, session: Session, **data: Any) -> Epic:
        """创建Epic (覆盖或实现基类方法)"""
        if "id" not in data:
            from src.utils.id_generator import EntityType, IdGenerator

            data["id"] = IdGenerator.generate_id(EntityType.EPIC)
        entity = self.model_class(**data)
        session.add(entity)
        return entity

    def get_progress(self, session: Session, epic_id: str) -> Dict[str, Any]:
        """获取Epic进度"""
        epic = self.get_by_id(session, epic_id)
        if not epic:
            return {"error": "Epic not found"}

        # Assuming Story relation is loaded or queried separately if needed
        story_count = len(epic.stories) if epic.stories else 0
        completed_stories = sum(1 for story in epic.stories if story and story.status == "completed") if epic.stories else 0

        return {
            "total_stories": story_count,
            "completed_stories": completed_stories,
            "progress": (completed_stories / story_count * 100) if story_count > 0 else 0,
        }

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有Epic"""
        try:
            return session.query(Epic).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            logger.error(f"获取路线图Epic时出错: {e}")
            return []


class StoryRepository(Repository[Story]):
    """Story仓库 (无状态)"""

    def __init__(self):
        """初始化Story仓库"""
        super().__init__(Story)

    def get_with_tasks(self, session: Session, story_id: str) -> Optional[Story]:
        """获取Story及其关联的Tasks"""
        return session.query(Story).options(joinedload(Story.tasks)).filter(Story.id == story_id).first()

    def get_by_epic(self, session: Session, epic_id: str) -> List[Story]:
        """获取指定Epic下的所有Stories"""
        return session.query(Story).filter(Story.epic_id == epic_id).all()

    def get_by_epic_id(self, session: Session, epic_id: str) -> List[Story]:
        """获取指定Epic ID的所有故事"""
        try:
            return session.query(Story).filter(Story.epic_id == epic_id).all()
        except Exception as e:
            logger.error(f"获取Epic故事时出错: {e}")
            return []

    def get_progress(self, session: Session, story_id: str) -> Dict[str, Any]:
        """获取Story进度"""
        story = self.get_by_id(session, story_id)
        if not story:
            return {"error": "Story not found"}

        # Assuming Task relation is loaded or queried separately if needed
        task_count = len(story.tasks) if story.tasks else 0
        completed_tasks = sum(1 for task in story.tasks if task and task.status in ["completed", "done"]) if story.tasks else 0

        return {
            "total_tasks": task_count,
            "completed_tasks": completed_tasks,
            "progress": (completed_tasks / task_count * 100) if task_count > 0 else 0,
        }

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有故事"""
        from src.models.db import Epic

        try:
            # 通过Epic关联查询
            return session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            logger.error(f"获取路线图故事时出错: {e}")
            return []

    def get_by_id(self, session: Session, entity_id: str) -> Optional[Story]:
        """通过ID获取Story (覆盖或实现基类方法)"""
        return session.query(self.model_class).filter(self.model_class.id == entity_id).first()

    def update(self, session: Session, entity_id: str, data: Dict[str, Any]) -> Optional[Story]:
        """通过ID更新Story (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model_class.__name__}")
            return entity
        return None

    def delete(self, session: Session, entity_id: str) -> bool:
        """通过ID删除Story (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            session.delete(entity)
            return True
        return False

    def get_all(self, session: Session, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Story]:
        """获取所有Story (覆盖或实现基类方法)"""
        query = session.query(self.model_class)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def create(self, session: Session, **data: Any) -> Story:
        """创建Story (覆盖或实现基类方法)"""
        if "id" not in data:
            from src.utils.id_generator import EntityType, IdGenerator

            data["id"] = IdGenerator.generate_id(EntityType.STORY)
        entity = self.model_class(**data)
        session.add(entity)
        return entity

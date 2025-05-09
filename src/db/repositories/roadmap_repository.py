"""
路线图数据访问对象模块

提供Roadmap、Epic、Milestone、Story、Task等实体的数据访问接口。
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from src.db.repositories.task_repository import TaskRepository
from src.db.repository import Repository
from src.models.db import Epic, Milestone, Roadmap, Story, Task

logger = logging.getLogger(__name__)


class RoadmapRepository(Repository[Roadmap]):
    """Roadmap仓库 (无状态)"""

    def __init__(self):
        """初始化Roadmap仓库 (不再存储 session)"""
        super().__init__(Roadmap)

    def get_with_related(self, session: Session, roadmap_id: str) -> Optional[Roadmap]:
        """获取Roadmap及其所有关联数据 (Load relationships)

        Args:
            session: SQLAlchemy 会话对象
            roadmap_id: Roadmap ID

        Returns:
            Roadmap对象或None
        """
        return (
            session.query(Roadmap)
            .options(joinedload(Roadmap.epics).joinedload(Epic.stories).joinedload(Story.tasks), joinedload(Roadmap.milestones))
            .filter(Roadmap.id == roadmap_id)
            .first()
        )

    def get_by_title(self, session: Session, title: str) -> Optional[Roadmap]:
        """通过名称(标题)获取路线图

        Args:
            session: SQLAlchemy 会话对象
            title: 路线图标题 (title)

        Returns:
            Roadmap对象或None
        """
        return session.query(Roadmap).filter(Roadmap.title == title).first()

    def get_stats(self, session: Session, roadmap_id: str) -> Dict[str, Any]:
        """获取路线图统计信息"""
        try:
            # Placeholder - replace with actual queries using 'session'
            return {"milestones_count": 5, "epics_count": 8, "stories_count": 15, "tasks_count": 47, "completed_tasks": 23, "overall_progress": 48.9}
        except Exception as e:
            return {"error": str(e)}

    def get_milestones_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有里程碑"""
        from src.models.db import Milestone

        try:
            # Placeholder for correct session usage
            # return session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()
            logger.warning("RoadmapRepository.get_milestones_by_roadmap called with self.session, needs refactoring")
            return []
        except Exception as e:
            logger.error(f"获取路线图里程碑时出错: {e}")
            return []

    def get_stories_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有故事"""
        from src.models.db import Epic, Story

        logger.warning("RoadmapRepository.get_stories_by_roadmap called without session, needs refactoring")
        return []

    def get_tasks_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有任务"""
        from src.models.db import Epic, Story, Task

        logger.warning("RoadmapRepository.get_tasks_by_roadmap called without session, needs refactoring")
        return []

    def create(self, session: Session, **data: Any) -> Roadmap:
        """创建 Roadmap (覆盖或实现基类方法)"""
        if "id" not in data:
            from src.utils.id_generator import IdGenerator

            data["id"] = IdGenerator.generate_roadmap_id()
        now_iso = datetime.now().isoformat()
        data.setdefault("status", "active")
        data.setdefault("created_at", now_iso)
        data.setdefault("updated_at", now_iso)

        # 确保 title 和 description 存在于 data 中
        # Roadmap 模型需要 title，description 是可选的但最好有
        if "title" not in data:
            # 根据实际情况，这里可能应该抛出错误或设置默认标题
            logger.warning("RoadmapRepository.create called without title in data.")
            data["title"] = "未命名路线图"  # 或者 raise ValueError("Title is required")

        entity = self.model_class(**data)
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity


class MilestoneRepository(Repository[Milestone]):
    """Milestone仓库 (无状态)"""

    def __init__(self):
        """初始化Milestone仓库 (无状态)"""
        super().__init__(Milestone)

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Milestone]:
        """根据路线图ID获取里程碑

        Args:
            session: SQLAlchemy 会话对象
            roadmap_id: 路线图ID

        Returns:
            Milestone对象列表
        """
        return session.query(self.model_class).filter(self.model_class.roadmap_id == roadmap_id).all()

    def get_by_title_and_roadmap_id(self, session: Session, title: str, roadmap_id: str) -> Optional[Milestone]:
        """根据标题和路线图ID获取里程碑

        Args:
            session: SQLAlchemy 会话对象
            title: 里程碑标题
            roadmap_id: 路线图ID

        Returns:
            Milestone对象或None
        """
        return session.query(self.model_class).filter(self.model_class.title == title, self.model_class.roadmap_id == roadmap_id).first()

    def get_with_epics(self, milestone_id: str) -> Optional[Milestone]:
        """获取里程碑及其关联的Epics

        Args:
            milestone_id: 里程碑ID

        Returns:
            Milestone对象或None
        """
        logger.warning("MilestoneRepository.get_with_epics is called without session and might be outdated.")
        return None  # Return None or raise error until fixed

    def create(self, session: Session, **data: Any) -> Milestone:
        """创建 Milestone (覆盖或实现基类方法)"""
        if "id" not in data:
            from src.utils.id_generator import IdGenerator

            data["id"] = IdGenerator.generate_milestone_id()
        # Add default values if needed
        now_iso = datetime.utcnow().isoformat()
        data.setdefault("status", "planned")
        data.setdefault("description", "")
        data.setdefault("created_at", now_iso)
        data.setdefault("updated_at", now_iso)

        entity = self.model_class(**data)
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity

    def update(self, session: Session, entity_id: str, data: Dict[str, Any]) -> Optional[Milestone]:
        """通过ID更新Milestone (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model_class.__name__}")
            # Add updated_at timestamp if not provided
            if "updated_at" not in data:
                setattr(entity, "updated_at", datetime.utcnow().isoformat())
            session.flush()
            session.refresh(entity)
            return entity
        return None


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
            # Add updated_at timestamp if not provided
            if "updated_at" not in data:
                setattr(entity, "updated_at", datetime.utcnow().isoformat())
            session.flush()
            session.refresh(entity)
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
            from src.utils.id_generator import IdGenerator

            data["id"] = IdGenerator.generate_epic_id()
        # Add default values
        now_iso = datetime.utcnow().isoformat()
        data.setdefault("status", "planned")
        data.setdefault("description", "")
        data.setdefault("created_at", now_iso)
        data.setdefault("updated_at", now_iso)

        # 生成本地显示编号
        if "local_display_number" not in data and "roadmap_id" in data:
            roadmap_id = data["roadmap_id"]
            # 获取当前路线图下最大的本地显示编号
            try:
                # 查询当前路线图下的所有Epic的local_display_number
                epics_with_number = session.query(Epic).filter(Epic.roadmap_id == roadmap_id, Epic.local_display_number.isnot(None)).all()

                # 提取编号部分，处理形如"E1", "E2"的编号
                max_number = 0
                for epic in epics_with_number:
                    # 尝试从local_display_number中提取数字部分
                    if epic.local_display_number and epic.local_display_number.startswith("E"):
                        try:
                            num = int(epic.local_display_number[1:])
                            max_number = max(max_number, num)
                        except ValueError:
                            pass  # 忽略无法解析为数字的部分

                # 生成新的编号
                data["local_display_number"] = f"E{max_number + 1}"
                logger.info(f"Epic: 生成本地显示编号 {data['local_display_number']}")
            except Exception as e:
                logger.error(f"生成Epic本地显示编号时出错: {e}", exc_info=True)
                # 如果出错，使用默认编号格式
                data["local_display_number"] = f"E{datetime.now().strftime('%m%d%H%M%S')}"

        entity = self.model_class(**data)
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity

    def get_progress(self, session: Session, epic_id: str) -> float:
        """计算Epic的进度

        Args:
            session: SQLAlchemy 会话对象
            epic_id: Epic ID

        Returns:
            float: 进度百分比
        """
        # Ensure StoryRepository is available or import locally if needed
        from .roadmap_repository import StoryRepository  # Assuming StoryRepository is in the same file or importable

        story_repo = StoryRepository()
        stories = story_repo.get_by_epic_id(session, epic_id)  # Use get_by_epic_id

        # Get epic status to handle case with no stories
        epic = self.get_by_id(session, epic_id)
        epic_status = epic.status if epic else "unknown"

        if not stories:
            # If epic status indicates completion, progress is 100%
            return 100.0 if epic_status == "completed" else 0.0

        completed_stories = sum(1 for story in stories if story.status in ["completed", "done"])
        return (completed_stories / len(stories)) * 100 if stories else 0.0

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Epic]:
        """根据路线图ID获取Epics"""
        return session.query(self.model_class).filter(self.model_class.roadmap_id == roadmap_id).all()

    def get_by_title_and_roadmap_id(self, session: Session, title: str, roadmap_id: str) -> Optional[Epic]:
        """根据标题和路线图ID获取Epic"""
        return session.query(self.model_class).filter(self.model_class.title == title, self.model_class.roadmap_id == roadmap_id).first()


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
        """根据Epic ID获取Stories"""
        return session.query(self.model_class).filter(self.model_class.epic_id == epic_id).all()

    def get_by_title_and_epic_id(self, session: Session, title: str, epic_id: str) -> Optional[Story]:
        """根据标题和Epic ID获取Story"""
        return session.query(self.model_class).filter(self.model_class.title == title, self.model_class.epic_id == epic_id).first()

    def get_by_title_and_roadmap_id(self, session: Session, title: str, roadmap_id: str) -> Optional[Story]:
        """根据标题和路线图ID获取Story

        注意：此方法通过Epic.roadmap_id关联查询，找到那些直接关联到特定路线图的Epic下的Story

        Args:
            session: SQLAlchemy 会话对象
            title: Story标题
            roadmap_id: 路线图ID

        Returns:
            匹配的Story对象或None
        """
        from src.models.db import Epic

        try:
            return session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Story.title == title, Epic.roadmap_id == roadmap_id).first()
        except Exception as e:
            logger.error(f"根据标题和路线图ID查询Story时出错: {e}", exc_info=True)
            return None

    def get_progress(self, session: Session, story_id: str) -> float:
        """计算Story的进度

        Args:
            session: SQLAlchemy 会话对象
            story_id: Story ID

        Returns:
            float: 进度百分比
        """
        # Ensure TaskRepository is available
        task_repo = TaskRepository()  # Assuming TaskRepository is imported
        tasks = task_repo.get_by_story_id(session, story_id)  # Assuming TaskRepository has get_by_story_id

        # Get story status to handle case with no tasks
        story = self.get_by_id(session, story_id)
        story_status = story.status if story else "unknown"

        if not tasks:
            return 100.0 if story_status in ["completed", "done"] else 0.0

        completed_tasks = sum(1 for task in tasks if task.status in ["completed", "done"])
        return (completed_tasks / len(tasks)) * 100 if tasks else 0.0

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有故事"""
        from src.models.db import Epic

        try:
            # 通过Epic关联查询
            return session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:  # 更具体的 OperationalError 可以在这里捕获，但为了通用性先用 Exception
            if "no such column: stories.is_implicit" in str(e):
                logger.error(f"获取路线图故事时出错 (可能是 stories.is_implicit 列缺失): {e}")
                # 不抛出异常，而是返回空列表，让程序继续，但记录错误
                return []
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
            # Add updated_at timestamp if not provided
            if "updated_at" not in data:
                setattr(entity, "updated_at", datetime.utcnow().isoformat())
            session.flush()
            session.refresh(entity)
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
            from src.utils.id_generator import IdGenerator

            data["id"] = IdGenerator.generate_story_id()
        # Add default values
        now_iso = datetime.utcnow().isoformat()
        data.setdefault("status", "planned")
        data.setdefault("description", "")
        data.setdefault("created_at", now_iso)
        data.setdefault("updated_at", now_iso)

        # 生成本地显示编号
        if "local_display_number" not in data and "epic_id" in data:
            epic_id = data["epic_id"]
            # 获取当前Epic下最大的本地显示编号
            try:
                # 查询当前Epic下的所有Story的local_display_number
                stories_with_number = session.query(Story).filter(Story.epic_id == epic_id, Story.local_display_number.isnot(None)).all()

                # 提取编号部分，处理形如"S1", "S2"的编号
                max_number = 0
                for story in stories_with_number:
                    # 尝试从local_display_number中提取数字部分
                    if story.local_display_number and story.local_display_number.startswith("S"):
                        try:
                            num = int(story.local_display_number[1:])
                            max_number = max(max_number, num)
                        except ValueError:
                            pass  # 忽略无法解析为数字的部分

                # 生成新的编号
                data["local_display_number"] = f"S{max_number + 1}"
                logger.info(f"Story: 生成本地显示编号 {data['local_display_number']}")
            except Exception as e:
                logger.error(f"生成Story本地显示编号时出错: {e}", exc_info=True)
                # 如果出错，使用默认编号格式
                data["local_display_number"] = f"S{datetime.now().strftime('%m%d%H%M%S')}"

        entity = self.model_class(**data)
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity

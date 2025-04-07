# src/models/db/roadmap.py (New Content)

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base  # Assuming Base is correctly defined elsewhere

# Import the new Task model for relationship typing hint, use string for relationship()
# from .task import Task # Not strictly needed for relationship string definition


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


# Association table for Epic <-> Task (if needed, maybe Task directly links to Epic/Story?)
# epic_task_association = Table('epic_task_association', Base.metadata,
#     Column('epic_id', String, ForeignKey('epics.id'), primary_key=True),
#     Column('task_id', String, ForeignKey('tasks.id'), primary_key=True)
# )

# Association table for Milestone <-> Task (if needed)
# milestone_task_association = Table('milestone_task_association', Base.metadata,
#     Column('milestone_id', String, ForeignKey('milestones.id'), primary_key=True),
#     Column('task_id', String, ForeignKey('tasks.id'), primary_key=True)
# )


class Roadmap(Base):
    """路线图 SQLAlchemy 模型"""

    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, archived
    owner = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    epics = relationship("Epic", back_populates="roadmap", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="roadmap", cascade="all, delete-orphan")
    stories = relationship("Story", back_populates="roadmap", cascade="all, delete-orphan")  # Direct relationship if stories belong to roadmap

    def __repr__(self):
        return f"<Roadmap(id='{self.id}', name='{self.name}')>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Milestone(Base):
    """里程碑 SQLAlchemy 模型"""

    __tablename__ = "milestones"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    roadmap_id = Column(String, ForeignKey("roadmaps.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="planned", nullable=False)  # planned, in_progress, completed
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roadmap = relationship("Roadmap", back_populates="milestones")
    stories = relationship("Story", back_populates="milestone")  # Stories assigned to this milestone
    # tasks = relationship("Task", secondary=milestone_task_association, back_populates="milestones") # If Task links to Milestone

    def __repr__(self):
        return f"<Milestone(id='{self.id}', title='{self.title}')>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Epic(Base):
    """史诗 SQLAlchemy 模型"""

    __tablename__ = "epics"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    roadmap_id = Column(String, ForeignKey("roadmaps.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft, in_progress, completed
    # milestone_id = Column(String, ForeignKey("milestones.id"), nullable=True) # Optional: If Epic belongs to a Milestone
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roadmap = relationship("Roadmap", back_populates="epics")
    stories = relationship("Story", back_populates="epic", cascade="all, delete-orphan")
    # milestone = relationship("Milestone", back_populates="epics") # If Epic belongs to a Milestone
    # tasks = relationship("Task", secondary=epic_task_association, back_populates="epics") # If Task links to Epic

    def __repr__(self):
        return f"<Epic(id='{self.id}', title='{self.title}')>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Story(Base):
    """用户故事 SQLAlchemy 模型"""

    __tablename__ = "stories"  # Changed from 'roadmap_items' used in Task foreign key? Align this. Let's assume 'stories' for now.

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    roadmap_id = Column(String, ForeignKey("roadmaps.id"), nullable=False, index=True)  # Story belongs to a Roadmap
    epic_id = Column(String, ForeignKey("epics.id"), nullable=True, index=True)  # Optional: Story belongs to an Epic
    milestone_id = Column(String, ForeignKey("milestones.id"), nullable=True, index=True)  # Optional: Story belongs to a Milestone
    description = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft, refinement, in_progress, completed, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roadmap = relationship("Roadmap", back_populates="stories")
    epic = relationship("Epic", back_populates="stories")
    milestone = relationship("Milestone", back_populates="stories")

    # Relationship to the NEW Task model
    # The foreign key 'roadmap_item_id' in Task points to Story.id
    # We need to ensure Task's ForeignKey targets 'stories.id'
    tasks = relationship("Task", back_populates="roadmap_item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Story(id='{self.id}', title='{self.title}')>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

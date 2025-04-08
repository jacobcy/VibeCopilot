"""
规则数据库模型

包含规则相关的数据库模型定义和与Pydantic模型的转换方法
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from ...models import rule_model as rule_models
from .base import Base, RuleType

# 规则与规则条目关联表
rule_item_association = Table(
    "rule_item_association",
    Base.metadata,
    Column("rule_id", String, ForeignKey("rules.id", ondelete="CASCADE")),
    Column("item_id", String, ForeignKey("rule_items.id", ondelete="CASCADE")),
)

# 规则与示例关联表
rule_example_association = Table(
    "rule_example_association",
    Base.metadata,
    Column("rule_id", String, ForeignKey("rules.id", ondelete="CASCADE")),
    Column("example_id", String, ForeignKey("rule_examples.id", ondelete="CASCADE")),
)


class RuleItem(Base):
    """规则条目数据库模型"""

    __tablename__ = "rule_items"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=0)
    category = Column(String, nullable=True)

    # 关系
    rules = relationship("Rule", secondary=rule_item_association, back_populates="items")

    def to_pydantic(self) -> rule_models.RuleItem:
        """转换为Pydantic模型"""
        return rule_models.RuleItem(content=self.content, priority=self.priority, category=self.category)

    @classmethod
    def from_pydantic(cls, model: rule_models.RuleItem, item_id: str) -> "RuleItem":
        """从Pydantic模型创建"""
        return cls(id=item_id, content=model.content, priority=model.priority, category=model.category)


class RuleExample(Base):
    """规则示例数据库模型"""

    __tablename__ = "rule_examples"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    is_valid = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    # 关系
    rules = relationship("Rule", secondary=rule_example_association, back_populates="examples")

    def to_pydantic(self) -> rule_models.Example:
        """转换为Pydantic模型"""
        return rule_models.Example(content=self.content, is_valid=self.is_valid, description=self.description)

    @classmethod
    def from_pydantic(cls, model: rule_models.Example, example_id: str) -> "RuleExample":
        """从Pydantic模型创建"""
        return cls(
            id=example_id,
            content=model.content,
            is_valid=model.is_valid,
            description=model.description,
        )


class RuleMetadata(Base):
    """规则元数据模型，扩展基础元数据"""

    __tablename__ = "rule_metadata"

    id = Column(String, primary_key=True)
    author = Column(String, nullable=False)
    tags = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    version = Column(String, default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    dependencies = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    usage_count = Column(Integer, default=0)
    effectiveness = Column(Integer, default=0)


class RuleApplication(Base):
    """规则应用记录"""

    __tablename__ = "rule_applications"

    id = Column(String, primary_key=True)
    rule_id = Column(String, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    applied_at = Column(DateTime, default=datetime.now)
    file_patterns = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    success = Column(Boolean, default=True)
    feedback = Column(Text, nullable=True)  # 存储为JSON格式的字符串

    # 关系
    rule = relationship("Rule", back_populates="applications")


class RuleDependency(Base):
    """规则依赖关系"""

    __tablename__ = "rule_dependencies"

    id = Column(String, primary_key=True)
    source_rule_id = Column(String, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    target_rule_id = Column(String, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # 关系
    source_rule = relationship("Rule", foreign_keys=[source_rule_id])
    target_rule = relationship("Rule", foreign_keys=[target_rule_id])


class Rule(Base):
    """规则数据库模型"""

    __tablename__ = "rules"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    globs = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    always_apply = Column(Boolean, default=False)
    content = Column(Text, nullable=False)

    # 元数据字段
    author = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    tags = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    dependencies = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    usage_count = Column(Integer, default=0)
    effectiveness = Column(Integer, default=0)

    # 关系
    items = relationship("RuleItem", secondary=rule_item_association, back_populates="rules", cascade="all, delete")
    examples = relationship(
        "RuleExample",
        secondary=rule_example_association,
        back_populates="rules",
        cascade="all, delete",
    )
    applications = relationship("RuleApplication", back_populates="rule")

    def to_pydantic(self) -> rule_models.Rule:
        """转换为Pydantic模型"""
        return rule_models.Rule(
            id=self.id,
            name=self.name,
            type=self.type,
            description=self.description,
            globs=json.loads(self.globs) if self.globs else [],
            always_apply=self.always_apply,
            items=[item.to_pydantic() for item in self.items],
            examples=[example.to_pydantic() for example in self.examples],
            content=self.content,
            metadata=rule_models.RuleMetadata(
                author=self.author,
                tags=json.loads(self.tags) if self.tags else [],
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at,
                dependencies=json.loads(self.dependencies) if self.dependencies else [],
                usage_count=self.usage_count,
                effectiveness=self.effectiveness,
            ),
        )

    @classmethod
    def from_pydantic(cls, model: rule_models.Rule) -> "Rule":
        """从Pydantic模型创建"""
        return cls(
            id=model.id,
            name=model.name,
            type=model.type,
            description=model.description,
            globs=json.dumps(model.globs),
            always_apply=model.always_apply,
            content=model.content,
            author=model.metadata.author,
            version=model.metadata.version,
            tags=json.dumps(model.metadata.tags),
            dependencies=json.dumps(model.metadata.dependencies),
            usage_count=model.metadata.usage_count,
            effectiveness=model.metadata.effectiveness,
        )


# 向后兼容别名
Example = RuleExample

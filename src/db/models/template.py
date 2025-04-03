"""
模板数据模型模块

从rule_templates模块迁移的数据模型，将Pydantic模型转换为SQLAlchemy模型。
"""

import json
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from . import Base


# 定义模板变量类型的枚举常量
class TemplateVariableType(str, Enum):
    """模板变量类型"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


# 注：标签现在直接存储在Template表中的tags字段中，不再使用关联表

# 模板与变量关联表
template_variable_association = Table(
    "template_variable_association",
    Base.metadata,
    Column("template_id", String, ForeignKey("templates.id", ondelete="CASCADE")),
    Column("variable_id", String, ForeignKey("template_variables.id", ondelete="CASCADE")),
)


class TemplateVariable(Base):
    """模板变量模型"""

    __tablename__ = "template_variables"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    required = Column(Boolean, default=True)
    enum_values = Column(Text, nullable=True)  # 存储为JSON格式的字符串

    # 关系
    templates = relationship(
        "Template", secondary=template_variable_association, back_populates="variables"
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default": json.loads(self.default_value) if self.default_value else None,
            "required": self.required,
            "enum_values": json.loads(self.enum_values) if self.enum_values else None,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            type=data.get("type", TemplateVariableType.STRING.value),
            description=data.get("description", ""),
            default_value=(
                json.dumps(data.get("default")) if data.get("default") is not None else None
            ),
            required=data.get("required", True),
            enum_values=json.dumps(data.get("enum_values")) if data.get("enum_values") else None,
        )


class Template(Base):
    """模板模型"""

    __tablename__ = "templates"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # agent, auto, manual等
    content = Column(Text, nullable=False)
    example = Column(Text, nullable=True)

    # 元数据字段
    author = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    variables = relationship(
        "TemplateVariable", secondary=template_variable_association, back_populates="templates"
    )

    # 标签存储为多对多关系，直接存储字符串
    tags = Column(Text, nullable=True)  # 存储为JSON格式的字符串列表

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "content": self.content,
            "example": self.example,
            "metadata": {
                "author": self.author,
                "tags": json.loads(self.tags) if self.tags else [],
                "version": self.version,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            },
            "variables": [var.to_dict() for var in self.variables],
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        metadata = data.get("metadata", {})

        template = cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", "agent"),
            content=data.get("content", ""),
            example=data.get("example"),
            author=metadata.get("author", "unknown"),
            version=metadata.get("version", "1.0.0"),
            tags=json.dumps(metadata.get("tags", [])),
        )

        # 处理创建和更新时间
        if "created_at" in metadata and metadata["created_at"]:
            if isinstance(metadata["created_at"], str):
                template.created_at = datetime.fromisoformat(metadata["created_at"])
            else:
                template.created_at = metadata["created_at"]

        if "updated_at" in metadata and metadata["updated_at"]:
            if isinstance(metadata["updated_at"], str):
                template.updated_at = datetime.fromisoformat(metadata["updated_at"])
            else:
                template.updated_at = metadata["updated_at"]

        return template

"""
模板数据库模型

包含模板相关的数据库模型定义和与Pydantic模型的转换方法
"""

import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from ...models import template as template_models
from .base import Base, BaseMetadata, TemplateVariableType

# 模板与变量关联表
template_variable_association = Table(
    "template_variable_association",
    Base.metadata,
    Column("template_id", String, ForeignKey("templates.id", ondelete="CASCADE")),
    Column("variable_id", String, ForeignKey("template_variables.id", ondelete="CASCADE")),
)


class TemplateVariable(Base):
    """模板变量数据库模型"""

    __tablename__ = "template_variables"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    required = Column(Boolean, default=True)
    enum_values = Column(Text, nullable=True)  # 存储为JSON格式的字符串

    # 关系
    templates = relationship(
        "Template", secondary=template_variable_association, back_populates="variables"
    )

    def to_pydantic(self) -> template_models.TemplateVariable:
        """转换为Pydantic模型"""
        return template_models.TemplateVariable(
            id=self.id,
            name=self.name,
            type=self.type,
            description=self.description,
            default=json.loads(self.default_value) if self.default_value else None,
            required=self.required,
            enum_values=json.loads(self.enum_values) if self.enum_values else None,
        )

    @classmethod
    def from_pydantic(
        cls, model: template_models.TemplateVariable, var_id: str
    ) -> "TemplateVariable":
        """从Pydantic模型创建"""
        return cls(
            id=var_id,
            name=model.name,
            type=model.type.value if hasattr(model.type, "value") else model.type,
            description=model.description,
            default_value=json.dumps(model.default) if model.default is not None else None,
            required=model.required,
            enum_values=json.dumps(model.enum_values) if model.enum_values else None,
        )


class Template(Base):
    """模板数据库模型"""

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
    tags = Column(Text, nullable=True)  # 存储为JSON格式的字符串列表
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    variables = relationship(
        "TemplateVariable",
        secondary=template_variable_association,
        back_populates="templates",
        cascade="all, delete",
    )

    def to_pydantic(self) -> template_models.Template:
        """转换为Pydantic模型"""
        return template_models.Template(
            id=self.id,
            name=self.name,
            description=self.description,
            type=self.type,
            content=self.content,
            example=self.example,
            variables=[var.to_pydantic() for var in self.variables],
            metadata=template_models.TemplateMetadata(
                author=self.author,
                tags=json.loads(self.tags) if self.tags else [],
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at,
            ),
        )

    @classmethod
    def from_pydantic(cls, model: template_models.Template) -> "Template":
        """从Pydantic模型创建"""
        return cls(
            id=model.id,
            name=model.name,
            description=model.description,
            type=model.type,
            content=model.content,
            example=model.example,
            author=model.metadata.author,
            version=model.metadata.version,
            tags=json.dumps(model.metadata.tags),
        )


class TemplateMetadata(BaseMetadata):
    """模板元数据模型，扩展基础元数据"""

    author: str = Field(..., description="作者")
    tags: List[str] = Field(default_factory=list, description="标签")
    version: str = Field(default="1.0.0", description="版本")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class TemplateRepository(BaseModel):
    """模板仓库设置"""

    id: str = Field(..., description="模板仓库ID")
    name: str = Field(..., description="仓库名称")
    url: str = Field(..., description="仓库URL")
    description: Optional[str] = Field(None, description="仓库描述")
    auth_required: bool = Field(default=False, description="是否需要认证")
    templates_path: str = Field(default="templates", description="模板在仓库中的路径")
    is_default: bool = Field(default=False, description="是否为默认仓库")

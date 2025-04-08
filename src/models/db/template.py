"""
模板数据库模型

定义模板和模板变量的数据库模型，确保ID字段正确定义
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, ForeignKey, String, Text, inspect
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Template(Base):
    """模板数据库模型"""

    __tablename__ = "templates"

    id = Column(String(50), primary_key=True, default=lambda: f"template_{uuid.uuid4().hex[:8]}")
    name = Column(String(100))
    description = Column(Text, nullable=True)
    type = Column(String(50))
    content = Column(Text)
    example = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    version = Column(String(20), nullable=True)
    tags = Column(Text, nullable=True)  # 存储为JSON字符串
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    variables = relationship("TemplateVariable", back_populates="template", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化模板，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"template_{uuid.uuid4().hex[:8]}"

        # 确保时间戳
        if not kwargs.get("created_at"):
            kwargs["created_at"] = datetime.now().isoformat()
        if not kwargs.get("updated_at"):
            kwargs["updated_at"] = datetime.now().isoformat()

        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "content": self.content,
            "example": self.example,
            "author": self.author,
            "version": self.version,
            "tags": json.loads(self.tags) if self.tags else [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "variables": [var.to_dict() for var in self.variables] if self.variables else [],
        }

    def to_pydantic(self):
        """转换为Pydantic模型"""
        # 延迟导入避免循环依赖
        from src.models import Template as TemplateModel
        from src.models import TemplateVariable as TemplateVariableModel

        template_dict = self.to_dict()

        # 处理变量
        variables = []
        for var_dict in template_dict.pop("variables", []):
            variables.append(TemplateVariableModel(**var_dict))

        # 创建模板模型
        template = TemplateModel(**template_dict, variables=variables)
        return template


class TemplateVariable(Base):
    """模板变量数据库模型"""

    __tablename__ = "template_variables"

    id = Column(String(50), primary_key=True, default=lambda: f"var_{uuid.uuid4().hex[:8]}")
    template_id = Column(String(50), ForeignKey("templates.id"))
    name = Column(String(100))
    type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)  # 存储为JSON字符串
    required = Column(Boolean, default=True)
    enum_values = Column(Text, nullable=True)  # 存储为JSON字符串

    # 关系
    template = relationship("Template", back_populates="variables")

    def __init__(self, **kwargs):
        """初始化模板变量，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"var_{uuid.uuid4().hex[:8]}"

        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
            "enum_values": json.loads(self.enum_values) if self.enum_values else None,
        }

    def to_pydantic(self):
        """转换为Pydantic模型"""
        # 延迟导入避免循环依赖
        from src.models import TemplateVariable as TemplateVariableModel

        var_dict = self.to_dict()

        # 解析JSON字符串
        if var_dict.get("default_value"):
            try:
                var_dict["default"] = json.loads(var_dict.pop("default_value"))
            except (json.JSONDecodeError, TypeError):
                var_dict["default"] = var_dict.pop("default_value")

        return TemplateVariableModel(**var_dict)

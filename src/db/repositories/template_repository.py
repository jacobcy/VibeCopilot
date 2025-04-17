"""
模板仓库模块

提供Template和TemplateVariable数据访问实现，使用统一的Repository模式。
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Template, TemplateVariable


class TemplateRepository(Repository[Template]):
    """Template仓库类 (无状态)"""

    def __init__(self):
        """初始化Template仓库"""
        super().__init__(Template)

    def get_template_by_id(self, session: Session, template_id: str) -> Optional[Template]:
        """根据ID获取模板

        Args:
            session: SQLAlchemy会话对象
            template_id: 模板ID

        Returns:
            Template对象或None
        """
        return self.get_by_id(session, template_id)

    def get_by_name(self, session: Session, name: str) -> Optional[Template]:
        """根据名称获取模板

        Args:
            session: SQLAlchemy会话对象
            name: 模板名称

        Returns:
            Template对象或None
        """
        return session.query(Template).filter(Template.name == name).first()

    def get_by_type(self, session: Session, template_type: str) -> List[Template]:
        """根据类型获取模板

        Args:
            session: SQLAlchemy会话对象
            template_type: 模板类型

        Returns:
            Template对象列表
        """
        return session.query(Template).filter(Template.type == template_type).all()

    def search_by_tags(self, session: Session, tags: List[str]) -> List[Template]:
        """根据标签搜索模板

        Args:
            session: SQLAlchemy会话对象
            tags: 标签列表

        Returns:
            匹配的Template对象列表
        """
        templates = self.get_all(session)
        if not tags:
            return templates

        results = []
        for template in templates:
            import json

            template_tags = json.loads(template.tags) if template.tags else []
            if any(tag in template_tags for tag in tags):
                results.append(template)

        return results

    def create_template(self, session: Session, template_data: Dict[str, Any], variables: List[Dict[str, Any]]) -> Template:
        """创建模板及其变量

        Args:
            session: SQLAlchemy会话对象
            template_data: 模板数据
            variables: 变量数据列表

        Returns:
            创建的Template对象
        """
        template = self.create(session, template_data)

        var_repo = TemplateVariableRepository()
        for var_data in variables:
            var_data["template_id"] = template.id
            variable = var_repo.create(session, var_data)
            template.variables.append(variable)

        return template


class TemplateVariableRepository(Repository[TemplateVariable]):
    """TemplateVariable仓库类 (无状态)"""

    def __init__(self):
        """初始化TemplateVariable仓库"""
        super().__init__(TemplateVariable)

    def get_by_template(self, session: Session, template_id: str) -> List[TemplateVariable]:
        """获取模板的所有变量

        Args:
            session: SQLAlchemy会话对象
            template_id: 模板ID

        Returns:
            TemplateVariable对象列表
        """
        return session.query(TemplateVariable).filter(TemplateVariable.templates.any(id=template_id)).all()

    def get_by_name_and_template(self, session: Session, name: str, template_id: str) -> Optional[TemplateVariable]:
        """根据名称和模板ID获取变量

        Args:
            session: SQLAlchemy会话对象
            name: 变量名称
            template_id: 模板ID

        Returns:
            TemplateVariable对象或None
        """
        return session.query(TemplateVariable).filter(TemplateVariable.name == name, TemplateVariable.templates.any(id=template_id)).first()

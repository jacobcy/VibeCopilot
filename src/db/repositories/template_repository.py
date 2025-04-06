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
    """Template仓库类"""

    def __init__(self, session: Session):
        """初始化Template仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Template)

    def get_by_name(self, name: str) -> Optional[Template]:
        """根据名称获取模板

        Args:
            name: 模板名称

        Returns:
            Template对象或None
        """
        return self.session.query(Template).filter(Template.name == name).first()

    def get_by_type(self, template_type: str) -> List[Template]:
        """根据类型获取模板

        Args:
            template_type: 模板类型

        Returns:
            Template对象列表
        """
        return self.session.query(Template).filter(Template.type == template_type).all()

    def search_by_tags(self, tags: List[str]) -> List[Template]:
        """根据标签搜索模板

        Args:
            tags: 标签列表

        Returns:
            匹配的Template对象列表
        """
        # 注意：因为tags存储为JSON字符串，这个实现需要根据实际情况调整
        # 简化实现，实际使用时可能需要更复杂的JSON查询
        templates = self.get_all()
        if not tags:
            return templates

        results = []
        for template in templates:
            import json

            template_tags = json.loads(template.tags) if template.tags else []
            if any(tag in template_tags for tag in tags):
                results.append(template)

        return results

    def create_template(
        self, template_data: Dict[str, Any], variables: List[Dict[str, Any]]
    ) -> Template:
        """创建模板及其变量

        Args:
            template_data: 模板数据
            variables: 变量数据列表

        Returns:
            创建的Template对象
        """
        # 创建模板
        template = self.create(template_data)

        # 创建变量
        var_repo = TemplateVariableRepository(self.session)
        for var_data in variables:
            var_data["template_id"] = template.id
            variable = var_repo.create(var_data)
            template.variables.append(variable)

        self.session.commit()
        return template


class TemplateVariableRepository(Repository[TemplateVariable]):
    """TemplateVariable仓库类"""

    def __init__(self, session: Session):
        """初始化TemplateVariable仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, TemplateVariable)

    def get_by_template(self, template_id: str) -> List[TemplateVariable]:
        """获取模板的所有变量

        Args:
            template_id: 模板ID

        Returns:
            TemplateVariable对象列表
        """
        return (
            self.session.query(TemplateVariable)
            .filter(TemplateVariable.templates.any(id=template_id))
            .all()
        )

    def get_by_name_and_template(self, name: str, template_id: str) -> Optional[TemplateVariable]:
        """根据名称和模板ID获取变量

        Args:
            name: 变量名称
            template_id: 模板ID

        Returns:
            TemplateVariable对象或None
        """
        return (
            self.session.query(TemplateVariable)
            .filter(TemplateVariable.name == name, TemplateVariable.templates.any(id=template_id))
            .first()
        )

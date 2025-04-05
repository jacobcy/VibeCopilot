"""
模板数据访问对象模块

提供Template和TemplateVariable等实体的数据访问接口。
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Template, TemplateVariable


class TemplateRepository(Repository[Template]):
    """Template仓库"""

    def __init__(self, session: Session):
        """初始化Template仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Template)

    def get_by_name(self, name: str) -> Optional[Template]:
        """通过名称获取模板

        Args:
            name: 模板名称

        Returns:
            Template对象或None
        """
        return self.session.query(Template).filter(Template.name == name).first()

    def search(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Template]:
        """搜索模板

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        search_query = self.session.query(Template)

        # 添加关键词过滤
        if query:
            search_query = search_query.filter(
                Template.name.ilike(f"%{query}%") | Template.description.ilike(f"%{query}%")
            )

        # 获取所有结果
        templates = search_query.all()

        # 如果需要根据标签过滤，则在Python中过滤
        # 这是因为我们将标签存储为JSON，无法在SQL层面直接过滤
        if tags and len(tags) > 0:
            import json

            filtered_templates = []
            for template in templates:
                if template.tags:
                    template_tags = json.loads(template.tags)
                    # 如果模板的标签与搜索标签有交集，则添加到结果中
                    if any(tag in template_tags for tag in tags):
                        filtered_templates.append(template)
            return filtered_templates

        return templates

    def create(self, data: Dict[str, Any]) -> Template:
        """创建模板

        Args:
            data: 模板数据

        Returns:
            创建的模板
        """
        # 生成ID如果不存在
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())

        # 创建模板实例
        template = Template.from_dict(data)

        # 处理变量
        if "variables" in data and data["variables"]:
            variable_repo = TemplateVariableRepository(self.session)
            for var_data in data["variables"]:
                # 生成变量ID如果不存在
                if not var_data.get("id"):
                    var_data["id"] = str(uuid.uuid4())

                # 创建或获取变量
                variable = variable_repo.get_by_id(var_data["id"])
                if not variable:
                    variable = variable_repo.create(var_data)
                else:
                    variable = variable_repo.update(var_data["id"], var_data)

                # 添加到模板的变量列表
                template.variables.append(variable)

        # 保存模板
        self.session.add(template)
        self.session.commit()

        return template


class TemplateVariableRepository(Repository[TemplateVariable]):
    """TemplateVariable仓库"""

    def __init__(self, session: Session):
        """初始化TemplateVariable仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, TemplateVariable)

    def get_by_name(self, name: str) -> Optional[TemplateVariable]:
        """通过名称获取模板变量

        Args:
            name: 变量名称

        Returns:
            TemplateVariable对象或None
        """
        return self.session.query(TemplateVariable).filter(TemplateVariable.name == name).first()

    def get_by_template(self, template_id: str) -> List[TemplateVariable]:
        """获取指定模板的所有变量

        Args:
            template_id: 模板ID

        Returns:
            变量列表
        """
        template = self.session.query(Template).filter(Template.id == template_id).first()
        if not template:
            return []

        return template.variables

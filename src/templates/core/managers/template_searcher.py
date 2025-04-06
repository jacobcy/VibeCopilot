"""
模板查询器模块

提供模板的查询和搜索功能
"""

import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.models import Template as TemplateModel

logger = logging.getLogger(__name__)


class TemplateSearcher:
    """模板查询器，负责查询和搜索模板"""

    def __init__(
        self,
        session: Session,
        template_repo: TemplateRepository,
        variable_repo: TemplateVariableRepository,
    ):
        """
        初始化模板查询器

        Args:
            session: 数据库会话
            template_repo: 模板仓库
            variable_repo: 模板变量仓库
        """
        self.session = session
        self.template_repo = template_repo
        self.variable_repo = variable_repo
        self.templates_cache: Dict[str, TemplateModel] = {}

    def get_template(self, template_id: str) -> Optional[TemplateModel]:
        """
        获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果未找到则返回None
        """
        # 先从缓存获取
        if template_id in self.templates_cache:
            return self.templates_cache[template_id]

        # 从数据库获取
        db_template = self.template_repo.get_by_id(template_id)
        if db_template:
            template_model = db_template.to_pydantic()
            self.templates_cache[template_id] = template_model
            return template_model

        logger.debug(f"未找到模板: {template_id}")
        return None

    def get_all_templates(self) -> List[TemplateModel]:
        """
        获取所有模板

        Returns:
            模板列表
        """
        # 从数据库获取所有模板
        db_templates = self.template_repo.get_all()

        # 转换为Pydantic模型并更新缓存
        templates = []
        for db_template in db_templates:
            template_model = db_template.to_pydantic()
            self.templates_cache[template_model.id] = template_model
            templates.append(template_model)

        logger.debug(f"获取到所有模板，共 {len(templates)} 个")
        return templates

    def search_templates(self, query: str = None, tags: List[str] = None) -> List[TemplateModel]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        # 如果有标签，使用标签搜索
        if tags:
            db_templates = self.template_repo.search_by_tags(tags)
            logger.debug(f"按标签搜索 {tags}，找到 {len(db_templates)} 个模板")
        else:
            # 否则获取所有模板
            db_templates = self.template_repo.get_all()
            logger.debug(f"获取所有模板，共 {len(db_templates)} 个")

        # 转换为Pydantic模型
        templates = [t.to_pydantic() for t in db_templates]

        # 如果有关键词，在Python中筛选（可以根据需要改为数据库筛选）
        if query:
            query = query.lower()
            filtered_templates = [
                t
                for t in templates
                if query in t.name.lower() or (t.description and query in t.description.lower())
            ]
            logger.debug(f"按关键词 '{query}' 筛选后剩余 {len(filtered_templates)} 个模板")
            templates = filtered_templates

        # 更新缓存
        for template in templates:
            self.templates_cache[template.id] = template

        return templates

    def get_templates_by_type(self, template_type: str) -> List[TemplateModel]:
        """
        按类型获取模板

        Args:
            template_type: 模板类型

        Returns:
            指定类型的模板列表
        """
        db_templates = self.template_repo.get_by_type(template_type)

        # 转换为Pydantic模型并更新缓存
        templates = []
        for db_template in db_templates:
            template_model = db_template.to_pydantic()
            self.templates_cache[template_model.id] = template_model
            templates.append(template_model)

        logger.debug(f"按类型 '{template_type}' 获取到 {len(templates)} 个模板")
        return templates

    def clear_cache(self) -> None:
        """
        清除模板缓存
        """
        self.templates_cache.clear()
        logger.debug("已清除模板缓存")

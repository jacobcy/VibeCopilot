"""
模板管理器模块

提供模板的加载、存储和检索功能。与统一数据库层集成。
此文件为重构后的版本，使用分离的模块实现功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.models import Template as TemplateModel
from src.templates.core.managers import TemplateLoader, TemplateSearcher, TemplateUpdater

logger = logging.getLogger(__name__)


class TemplateManager:
    """模板管理器，提供模板操作并与数据库集成"""

    def __init__(self, session: Session, templates_dir: str = None):
        """
        初始化模板管理器

        Args:
            session: 数据库会话
            templates_dir: 模板文件目录，用于从文件加载模板
        """
        self.session = session
        self.templates_dir = templates_dir

        # 初始化仓库
        self.template_repo = TemplateRepository(session)
        self.variable_repo = TemplateVariableRepository(session)

        # 初始化子模块
        self.loader = TemplateLoader(session, self.template_repo, self.variable_repo)
        self.searcher = TemplateSearcher(session, self.template_repo, self.variable_repo)
        self.updater = TemplateUpdater(session, self.template_repo, self.variable_repo)

        # 缓存引用
        self.templates_cache = self.searcher.templates_cache

        # 如果提供了模板目录，自动加载模板
        if templates_dir and os.path.exists(templates_dir):
            self.load_templates_from_directory()

    def load_templates_from_directory(self, directory: str = None) -> int:
        """
        从目录加载所有模板到数据库

        Args:
            directory: 模板目录，如果为None则使用初始化时设置的目录

        Returns:
            加载的模板数量
        """
        directory = directory or self.templates_dir
        return self.loader.load_templates_from_directory(directory)

    def get_template(self, template_id: str) -> Optional[TemplateModel]:
        """
        获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果未找到则返回None
        """
        return self.searcher.get_template(template_id)

    def get_all_templates(self) -> List[TemplateModel]:
        """
        获取所有模板

        Returns:
            模板列表
        """
        return self.searcher.get_all_templates()

    def add_template(self, template: TemplateModel) -> TemplateModel:
        """
        添加模板

        Args:
            template: 模板对象

        Returns:
            添加的模板对象
        """
        template_dict = template.dict()
        result = self.loader.import_template_from_dict(template_dict)
        self.templates_cache[result.id] = result
        return result

    def update_template(
        self, template_id: str, template_data: Dict[str, Any]
    ) -> Optional[TemplateModel]:
        """
        更新模板

        Args:
            template_id: 模板ID
            template_data: 更新的模板数据

        Returns:
            更新后的模板对象，如果未找到则返回None
        """
        result = self.updater.update_template(template_id, template_data)
        if result:
            self.templates_cache[template_id] = result
        return result

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        result = self.updater.delete_template(template_id)
        if result and template_id in self.templates_cache:
            del self.templates_cache[template_id]
        return result

    def search_templates(self, query: str = None, tags: List[str] = None) -> List[TemplateModel]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        return self.searcher.search_templates(query, tags)

    def get_templates_by_type(self, template_type: str) -> List[TemplateModel]:
        """
        按类型获取模板

        Args:
            template_type: 模板类型

        Returns:
            指定类型的模板列表
        """
        return self.searcher.get_templates_by_type(template_type)

    def clear_cache(self) -> None:
        """
        清除模板缓存
        """
        self.searcher.clear_cache()

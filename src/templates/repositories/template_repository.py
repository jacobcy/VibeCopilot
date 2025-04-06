"""
模板仓库模块

提供模板的持久化存储接口和实现，支持文件系统和数据库两种方式。
此模块作为模板存储的统一接口，提供一致的API来访问不同的存储后端。
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from src.db.repositories.template_repository import TemplateRepository as SQLTemplateRepository

from ..models.template import Template

logger = logging.getLogger(__name__)


class TemplateRepository(ABC):
    """模板仓库抽象基类"""

    @abstractmethod
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_all_templates(self) -> List[Template]:
        """
        获取所有模板

        Returns:
            模板列表
        """
        pass

    @abstractmethod
    def save_template(self, template: Template) -> Template:
        """
        保存模板

        Args:
            template: 模板对象

        Returns:
            保存的模板对象
        """
        pass

    @abstractmethod
    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    def search_templates(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Template]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        pass


class FileSystemTemplateRepository(TemplateRepository):
    """文件系统模板仓库实现"""

    def __init__(self, storage_dir: str):
        """
        初始化文件系统模板仓库

        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _get_template_path(self, template_id: str) -> str:
        """获取模板文件路径"""
        return os.path.join(self.storage_dir, f"{template_id}.json")

    def get_template(self, template_id: str) -> Optional[Template]:
        """
        获取模板

        Args:
            template_id: 模板ID

        Returns:
            模板对象，如果不存在则返回None
        """
        template_path = self._get_template_path(template_id)
        if not os.path.exists(template_path):
            return None

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Template.parse_obj(data)
        except Exception as e:
            logger.error(f"加载模板 {template_id} 失败: {str(e)}")
            return None

    def get_all_templates(self) -> List[Template]:
        """
        获取所有模板

        Returns:
            模板列表
        """
        templates = []

        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                template_id = os.path.splitext(filename)[0]
                template = self.get_template(template_id)
                if template:
                    templates.append(template)

        return templates

    def save_template(self, template: Template) -> Template:
        """
        保存模板

        Args:
            template: 模板对象

        Returns:
            保存的模板对象
        """
        template_path = self._get_template_path(template.id)

        try:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template.json(ensure_ascii=False, indent=2))
            return template
        except Exception as e:
            logger.error(f"保存模板 {template.id} 失败: {str(e)}")
            raise

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        template_path = self._get_template_path(template_id)
        if os.path.exists(template_path):
            try:
                os.remove(template_path)
                return True
            except Exception as e:
                logger.error(f"删除模板 {template_id} 失败: {str(e)}")
                return False

        return False

    def search_templates(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Template]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        templates = self.get_all_templates()
        results = []

        if not query and not tags:
            return templates

        for template in templates:
            # 关键词搜索
            if query:
                query_lower = query.lower()
                if (
                    query_lower in template.name.lower()
                    or query_lower in template.description.lower()
                ):
                    results.append(template)
                    continue

            # 标签过滤
            if tags and set(tags).intersection(set(template.metadata.tags)):
                results.append(template)

        return results


class SQLTemplateRepositoryAdapter(TemplateRepository):
    """
    数据库模板仓库适配器

    将标准SQLAlchemy实现适配到模板仓库接口。
    """

    def __init__(self, sql_repo: SQLTemplateRepository):
        """
        初始化适配器

        Args:
            sql_repo: SQLAlchemy模板仓库实例
        """
        self.sql_repo = sql_repo

    def get_template(self, template_id: str) -> Optional[Template]:
        """获取模板"""
        db_template = self.sql_repo.get_by_id(template_id)
        if not db_template:
            return None
        return db_template.to_pydantic()

    def get_all_templates(self) -> List[Template]:
        """获取所有模板"""
        db_templates = self.sql_repo.get_all()
        return [t.to_pydantic() for t in db_templates]

    def save_template(self, template: Template) -> Template:
        """保存模板"""
        from src.models.db.template import Template as DBTemplate

        db_template = DBTemplate.from_pydantic(template)
        if self.sql_repo.get_by_id(template.id):
            self.sql_repo.update(template.id, db_template.__dict__)
        else:
            self.sql_repo.create(db_template.__dict__)
        return template

    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if not self.sql_repo.get_by_id(template_id):
            return False
        self.sql_repo.delete(template_id)
        return True

    def search_templates(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Template]:
        """搜索模板"""
        # 使用标签搜索
        if tags:
            db_templates = self.sql_repo.search_by_tags(tags)
        else:
            db_templates = self.sql_repo.get_all()

        # 如果有查询条件，进一步过滤
        if query:
            filtered_templates = []
            for t in db_templates:
                if query.lower() in t.name.lower() or (
                    t.description and query.lower() in t.description.lower()
                ):
                    filtered_templates.append(t)
            db_templates = filtered_templates

        return [t.to_pydantic() for t in db_templates]


# 导出所有模板仓库类，便于使用
__all__ = ["TemplateRepository", "FileSystemTemplateRepository", "SQLTemplateRepositoryAdapter"]

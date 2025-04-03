"""
模板仓库模块

提供模板的持久化存储接口和实现。
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

import yaml

from ..models.template import Template

logger = logging.getLogger(__name__)


class TemplateRepository(ABC):
    """模板仓库抽象基类"""

    @abstractmethod
    def get_template(self, template_id: str) -> Optional[Template]:
        """获取模板"""
        pass

    @abstractmethod
    def get_all_templates(self) -> List[Template]:
        """获取所有模板"""
        pass

    @abstractmethod
    def save_template(self, template: Template) -> Template:
        """保存模板"""
        pass

    @abstractmethod
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        pass

    @abstractmethod
    def search_templates(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Template]:
        """搜索模板"""
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


try:
    import pymongo

    class MongoDBTemplateRepository(TemplateRepository):
        """MongoDB模板仓库实现"""

        def __init__(
            self, connection_string: str, db_name: str, collection_name: str = "templates"
        ):
            """
            初始化MongoDB模板仓库

            Args:
                connection_string: MongoDB连接字符串
                db_name: 数据库名称
                collection_name: 集合名称
            """
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]

            # 创建索引
            self.collection.create_index("id", unique=True)
            self.collection.create_index("name")
            self.collection.create_index("metadata.tags")

        def get_template(self, template_id: str) -> Optional[Template]:
            """
            获取模板

            Args:
                template_id: 模板ID

            Returns:
                模板对象，如果不存在则返回None
            """
            data = self.collection.find_one({"id": template_id})
            if not data:
                return None

            # 移除MongoDB的_id字段
            data.pop("_id", None)
            return Template.parse_obj(data)

        def get_all_templates(self) -> List[Template]:
            """
            获取所有模板

            Returns:
                模板列表
            """
            templates = []

            for data in self.collection.find():
                # 移除MongoDB的_id字段
                data.pop("_id", None)
                templates.append(Template.parse_obj(data))

            return templates

        def save_template(self, template: Template) -> Template:
            """
            保存模板

            Args:
                template: 模板对象

            Returns:
                保存的模板对象
            """
            data = json.loads(template.json())

            # 使用upsert操作，存在则更新，不存在则插入
            self.collection.update_one({"id": template.id}, {"$set": data}, upsert=True)

            return template

        def delete_template(self, template_id: str) -> bool:
            """
            删除模板

            Args:
                template_id: 模板ID

            Returns:
                是否成功删除
            """
            result = self.collection.delete_one({"id": template_id})
            return result.deleted_count > 0

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
            filter_query = {}

            # 构建查询条件
            if query:
                filter_query["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                ]

            if tags:
                filter_query["metadata.tags"] = {"$in": tags}

            templates = []

            for data in self.collection.find(filter_query):
                # 移除MongoDB的_id字段
                data.pop("_id", None)
                templates.append(Template.parse_obj(data))

            return templates

except ImportError:
    # 如果没有安装pymongo，提供一个占位实现
    class MongoDBTemplateRepository:
        def __init__(self, *args, **kwargs):
            raise ImportError("MongoDB存储需要安装pymongo: pip install pymongo")

"""
模板管理器模块

提供模板的加载、存储和检索功能。
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from ..models.template import Template, TemplateMetadata
from ..utils.template_utils import load_template_from_file, normalize_template_id

logger = logging.getLogger(__name__)


class TemplateManager:
    """模板管理器"""

    def __init__(self, templates_dir: str = None, storage_adapter=None):
        """
        初始化模板管理器

        Args:
            templates_dir: 模板文件目录
            storage_adapter: 存储适配器，用于持久化模板
        """
        self.templates_dir = templates_dir
        self.storage_adapter = storage_adapter
        self.templates_cache: Dict[str, Template] = {}

        # 如果提供了模板目录，自动加载模板
        if templates_dir and os.path.exists(templates_dir):
            self.load_templates_from_directory()

    def load_templates_from_directory(self, directory: str = None) -> int:
        """
        从目录加载所有模板

        Args:
            directory: 模板目录，如果为None则使用初始化时设置的目录

        Returns:
            加载的模板数量
        """
        directory = directory or self.templates_dir
        if not directory or not os.path.exists(directory):
            raise ValueError(f"模板目录不存在: {directory}")

        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".md", ".jinja", ".j2", ".template")):
                    file_path = os.path.join(root, file)
                    try:
                        template_data = load_template_from_file(file_path)
                        template_id = template_data.get("id") or normalize_template_id(
                            template_data["name"]
                        )

                        metadata = template_data.pop("metadata", {})
                        template_metadata = TemplateMetadata(
                            author=metadata.get("author", "未知"),
                            tags=metadata.get("tags", []),
                            version=metadata.get("version", "1.0.0"),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )

                        template = Template(
                            id=template_id, metadata=template_metadata, **template_data
                        )

                        self.templates_cache[template_id] = template
                        count += 1
                    except Exception as e:
                        logger.error(f"加载模板 {file_path} 失败: {str(e)}")

        logger.info(f"从目录 {directory} 加载了 {count} 个模板")
        return count

    def get_template(self, template_id: str) -> Optional[Template]:
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

        # 如果有存储适配器，尝试从存储加载
        if self.storage_adapter:
            template = self.storage_adapter.get_template(template_id)
            if template:
                self.templates_cache[template_id] = template
                return template

        return None

    def get_all_templates(self) -> List[Template]:
        """
        获取所有模板

        Returns:
            模板列表
        """
        # 如果有存储适配器，确保从存储同步最新数据
        if self.storage_adapter:
            templates = self.storage_adapter.get_all_templates()
            # 更新缓存
            for template in templates:
                self.templates_cache[template.id] = template
            return templates

        return list(self.templates_cache.values())

    def add_template(self, template: Template) -> Template:
        """
        添加模板

        Args:
            template: 模板对象

        Returns:
            添加的模板对象
        """
        if not template.id:
            template.id = normalize_template_id(template.name)

        # 确保更新时间
        template.metadata.updated_at = datetime.now()

        # 保存到缓存
        self.templates_cache[template.id] = template

        # 如果有存储适配器，保存到存储
        if self.storage_adapter:
            self.storage_adapter.save_template(template)

        return template

    def update_template(
        self, template_id: str, template_data: Dict[str, Any]
    ) -> Optional[Template]:
        """
        更新模板

        Args:
            template_id: 模板ID
            template_data: 更新的模板数据

        Returns:
            更新后的模板对象，如果未找到则返回None
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # 更新模板属性
        for key, value in template_data.items():
            if key == "metadata":
                # 更新元数据
                for meta_key, meta_value in value.items():
                    setattr(template.metadata, meta_key, meta_value)
            elif hasattr(template, key):
                setattr(template, key, value)

        # 更新更新时间
        template.metadata.updated_at = datetime.now()

        # 保存更新
        self.templates_cache[template_id] = template

        # 如果有存储适配器，保存到存储
        if self.storage_adapter:
            self.storage_adapter.save_template(template)

        return template

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        if template_id in self.templates_cache:
            del self.templates_cache[template_id]

            # 如果有存储适配器，从存储中删除
            if self.storage_adapter:
                return self.storage_adapter.delete_template(template_id)

            return True

        return False

    def search_templates(self, query: str = None, tags: List[str] = None) -> List[Template]:
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

        for template in templates:
            # 如果没有搜索条件，返回所有模板
            if not query and not tags:
                results.append(template)
                continue

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
            if tags and any(tag in template.metadata.tags for tag in tags):
                results.append(template)

        return results

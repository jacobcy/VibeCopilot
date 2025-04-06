"""
模板管理器模块

提供模板的加载、存储和检索功能。与统一数据库层集成。
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.models import Template as TemplateModel
from src.models import TemplateMetadata
from src.models.db import Template, TemplateVariable

from ..utils.template_utils import load_template_from_file, normalize_template_id

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
        self.template_repo = TemplateRepository(session)
        self.variable_repo = TemplateVariableRepository(session)
        self.templates_cache: Dict[str, TemplateModel] = {}

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
                        template_metadata = {
                            "author": metadata.get("author", "未知"),
                            "version": metadata.get("version", "1.0.0"),
                            "tags": json.dumps(metadata.get("tags", [])),
                            "created_at": datetime.now(),
                            "updated_at": datetime.now(),
                        }

                        # 准备模板数据
                        db_template_data = {
                            "id": template_id,
                            "name": template_data.get("name"),
                            "description": template_data.get("description", ""),
                            "type": template_data.get("type", "general"),
                            "content": template_data.get("content", ""),
                            "example": template_data.get("example", ""),
                            **template_metadata,
                        }

                        # 准备变量数据
                        variables_data = []
                        for var in template_data.get("variables", []):
                            var_data = {
                                "id": var.get("id") or str(uuid.uuid4()),
                                "name": var.get("name"),
                                "type": var.get("type"),
                                "description": var.get("description", ""),
                                "default_value": json.dumps(var.get("default"))
                                if var.get("default") is not None
                                else None,
                                "required": var.get("required", True),
                                "enum_values": json.dumps(var.get("enum_values"))
                                if var.get("enum_values")
                                else None,
                            }
                            variables_data.append(var_data)

                        # 保存到数据库
                        db_template = self.template_repo.create_template(
                            db_template_data, variables_data
                        )

                        # 转换为Pydantic模型并缓存
                        template_model = db_template.to_pydantic()
                        self.templates_cache[template_id] = template_model

                        count += 1
                    except Exception as e:
                        logger.error(f"加载模板 {file_path} 失败: {str(e)}")

        logger.info(f"从目录 {directory} 加载了 {count} 个模板")
        return count

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

        return templates

    def add_template(self, template: TemplateModel) -> TemplateModel:
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

        # 转换为数据库模型
        db_template = Template.from_pydantic(template)

        # 准备变量数据
        variables_data = []
        for var in template.variables:
            var_data = {
                "id": var.id or str(uuid.uuid4()),
                "name": var.name,
                "type": var.type.value if hasattr(var.type, "value") else var.type,
                "description": var.description or "",
                "default_value": json.dumps(var.default) if var.default is not None else None,
                "required": var.required,
                "enum_values": json.dumps(var.enum_values) if var.enum_values else None,
            }
            variables_data.append(var_data)

        # 保存到数据库
        template_data = {
            "id": template.id,
            "name": template.name,
            "description": template.description or "",
            "type": template.type,
            "content": template.content,
            "example": template.example or "",
            "author": template.metadata.author,
            "version": template.metadata.version,
            "tags": json.dumps(template.metadata.tags),
            "created_at": template.metadata.created_at,
            "updated_at": template.metadata.updated_at,
        }

        db_template = self.template_repo.create_template(template_data, variables_data)

        # 更新缓存
        result_template = db_template.to_pydantic()
        self.templates_cache[result_template.id] = result_template

        return result_template

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
        # 获取现有模板
        db_template = self.template_repo.get_by_id(template_id)
        if not db_template:
            return None

        # 更新模板属性
        update_data = {}
        for key, value in template_data.items():
            if key == "metadata":
                # 更新元数据
                for meta_key, meta_value in value.items():
                    if meta_key == "tags" and isinstance(meta_value, list):
                        update_data["tags"] = json.dumps(meta_value)
                    else:
                        update_data[meta_key] = meta_value
            elif key == "variables":
                # 变量更新在下面单独处理
                continue
            elif hasattr(db_template, key):
                update_data[key] = value

        # 更新更新时间
        update_data["updated_at"] = datetime.now()

        # 更新模板
        updated_template = self.template_repo.update(template_id, update_data)

        # 处理变量更新
        if "variables" in template_data:
            # 获取现有变量
            existing_variables = self.variable_repo.get_by_template(template_id)
            existing_var_dict = {var.id: var for var in existing_variables}

            # 处理每个变量
            for var_data in template_data["variables"]:
                var_id = var_data.get("id")
                if var_id and var_id in existing_var_dict:
                    # 更新现有变量
                    var_update = {
                        "name": var_data.get("name", existing_var_dict[var_id].name),
                        "type": var_data.get("type", existing_var_dict[var_id].type),
                        "description": var_data.get(
                            "description", existing_var_dict[var_id].description
                        ),
                        "default_value": json.dumps(var_data.get("default"))
                        if "default" in var_data
                        else existing_var_dict[var_id].default_value,
                        "required": var_data.get("required", existing_var_dict[var_id].required),
                        "enum_values": json.dumps(var_data.get("enum_values"))
                        if "enum_values" in var_data
                        else existing_var_dict[var_id].enum_values,
                    }
                    self.variable_repo.update(var_id, var_update)
                else:
                    # 添加新变量
                    new_var_id = var_id or str(uuid.uuid4())
                    new_var = {
                        "id": new_var_id,
                        "name": var_data.get("name"),
                        "type": var_data.get("type"),
                        "description": var_data.get("description", ""),
                        "default_value": json.dumps(var_data.get("default"))
                        if var_data.get("default") is not None
                        else None,
                        "required": var_data.get("required", True),
                        "enum_values": json.dumps(var_data.get("enum_values"))
                        if var_data.get("enum_values")
                        else None,
                    }
                    created_var = self.variable_repo.create(new_var)

                    # 关联到模板
                    if created_var:
                        db_template.variables.append(created_var)

        self.session.commit()

        # 刷新并获取更新后的模板
        self.session.refresh(updated_template)
        result_template = updated_template.to_pydantic()

        # 更新缓存
        self.templates_cache[template_id] = result_template

        return result_template

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        result = self.template_repo.delete(template_id)

        # 如果成功删除，从缓存中移除
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
        # 如果有标签，使用标签搜索
        if tags:
            db_templates = self.template_repo.search_by_tags(tags)
        else:
            # 否则获取所有模板
            db_templates = self.template_repo.get_all()

        # 转换为Pydantic模型
        templates = [t.to_pydantic() for t in db_templates]

        # 如果有关键词，在Python中筛选（可以根据需要改为数据库筛选）
        if query:
            query = query.lower()
            templates = [
                t
                for t in templates
                if query in t.name.lower() or (t.description and query in t.description.lower())
            ]

        # 更新缓存
        for template in templates:
            self.templates_cache[template.id] = template

        return templates

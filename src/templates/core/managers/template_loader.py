"""
模板加载器模块

负责从文件系统加载模板并转换为标准格式
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.models import Template as TemplateModel
from src.templates.utils.template_utils import load_template_from_file, normalize_template_id

logger = logging.getLogger(__name__)


class TemplateLoader:
    """模板加载器，负责从文件系统加载模板"""

    def __init__(
        self,
        session: Session,
        template_repo: TemplateRepository,
        variable_repo: TemplateVariableRepository,
    ):
        """
        初始化模板加载器

        Args:
            session: 数据库会话
            template_repo: 模板仓库
            variable_repo: 模板变量仓库
        """
        self.session = session
        self.template_repo = template_repo
        self.variable_repo = variable_repo

    def load_templates_from_directory(self, directory: str) -> int:
        """
        从目录加载所有模板到数据库

        Args:
            directory: 模板目录路径

        Returns:
            加载的模板数量
        """
        if not directory or not os.path.exists(directory):
            raise ValueError(f"模板目录不存在: {directory}")

        count = 0
        templates_cache = {}

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".md", ".jinja", ".j2", ".template")):
                    file_path = os.path.join(root, file)
                    try:
                        # 加载并处理单个模板
                        result = self._load_single_template(file_path)
                        if result:
                            templates_cache[result.id] = result
                            count += 1
                    except Exception as e:
                        logger.error(f"加载模板 {file_path} 失败: {str(e)}")

        logger.info(f"从目录 {directory} 加载了 {count} 个模板")
        return count

    def _load_single_template(self, file_path: str) -> TemplateModel:
        """
        加载单个模板文件

        Args:
            file_path: 模板文件路径

        Returns:
            加载的模板对象
        """
        template_data = load_template_from_file(file_path)
        template_id = template_data.get("id") or normalize_template_id(template_data["name"])

        # 确保始终有一个有效的ID
        if not template_id or template_id.strip() == "":
            # 使用文件名作为ID
            template_id = os.path.splitext(os.path.basename(file_path))[0]

            # 如果文件名不合适，使用UUID
            if not template_id or template_id.strip() == "":
                template_id = f"template_{str(uuid.uuid4())[:8]}"

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
            "name": template_data.get("name") or template_id,
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
                "default_value": json.dumps(var.get("default")) if var.get("default") is not None else None,
                "required": var.get("required", True),
                "enum_values": json.dumps(var.get("enum_values")) if var.get("enum_values") else None,
            }
            variables_data.append(var_data)

        # 保存到数据库
        db_template = self.template_repo.create_template(db_template_data, variables_data)

        # 返回Pydantic模型
        return db_template.to_pydantic()

    def import_template_from_dict(self, template_dict: Dict[str, Any], overwrite: bool = False) -> TemplateModel:
        """
        从字典导入模板

        Args:
            template_dict: 包含模板数据的字典
            overwrite: 是否覆盖已存在的模板

        Returns:
            导入的模板对象
        """
        # 处理元数据
        metadata = template_dict.pop("metadata", {})
        template_metadata = {
            "author": metadata.get("author", "未知"),
            "version": metadata.get("version", "1.0.0"),
            "tags": json.dumps(metadata.get("tags", [])),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # 确保模板ID
        template_id = template_dict.get("id")
        if not template_id or template_id.strip() == "":
            template_id = normalize_template_id(template_dict.get("name", f"template_{str(uuid.uuid4())[:8]}"))

        # 再次验证ID不为空
        if not template_id or template_id.strip() == "":
            template_id = f"template_{str(uuid.uuid4())[:8]}"

        # 检查模板是否已存在
        existing_template = self.template_repo.get_template_by_id(template_id)

        # 如果模板已存在且不允许覆盖，直接返回现有模板
        if existing_template and not overwrite:
            logger.info(f"模板已存在且不允许覆盖: {template_id}")
            return existing_template.to_pydantic()

        # 如果模板已存在且允许覆盖，先删除现有模板
        if existing_template and overwrite:
            logger.info(f"覆盖现有模板: {template_id}")
            self.template_repo.delete_template(template_id)

        # 准备模板数据
        db_template_data = {
            "id": template_id,
            "name": template_dict.get("name") or template_id,
            "description": template_dict.get("description", ""),
            "type": template_dict.get("type", "general"),
            "content": template_dict.get("content", ""),
            "example": template_dict.get("example", ""),
            **template_metadata,
        }

        # 准备变量数据
        variables_data = []
        for var in template_dict.get("variables", []):
            var_data = {
                "id": var.get("id") or str(uuid.uuid4()),
                "name": var.get("name"),
                "type": var.get("type"),
                "description": var.get("description", ""),
                "default_value": json.dumps(var.get("default")) if var.get("default") is not None else None,
                "required": var.get("required", True),
                "enum_values": json.dumps(var.get("enum_values")) if var.get("enum_values") else None,
            }
            variables_data.append(var_data)

        # 保存到数据库
        db_template = self.template_repo.create_template(db_template_data, variables_data)

        # 返回Pydantic模型
        return db_template.to_pydantic()

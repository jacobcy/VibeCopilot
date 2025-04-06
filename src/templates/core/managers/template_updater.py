"""
模板更新器模块

提供模板的更新和删除功能
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.db import TemplateRepository, TemplateVariableRepository
from src.models import Template as TemplateModel

logger = logging.getLogger(__name__)


class TemplateUpdater:
    """模板更新器，负责更新和删除模板"""

    def __init__(
        self,
        session: Session,
        template_repo: TemplateRepository,
        variable_repo: TemplateVariableRepository,
    ):
        """
        初始化模板更新器

        Args:
            session: 数据库会话
            template_repo: 模板仓库
            variable_repo: 模板变量仓库
        """
        self.session = session
        self.template_repo = template_repo
        self.variable_repo = variable_repo

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
            logger.warning(f"未找到要更新的模板: {template_id}")
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
            self._update_template_variables(template_id, template_data["variables"], db_template)

        self.session.commit()

        # 刷新并获取更新后的模板
        self.session.refresh(updated_template)
        result_template = updated_template.to_pydantic()

        return result_template

    def _update_template_variables(
        self, template_id: str, variables_data: list, db_template: Any
    ) -> None:
        """
        更新模板变量

        Args:
            template_id: 模板ID
            variables_data: 变量数据列表
            db_template: 数据库模板对象
        """
        # 获取现有变量
        existing_variables = self.variable_repo.get_by_template(template_id)
        existing_var_dict = {var.id: var for var in existing_variables}

        # 处理每个变量
        for var_data in variables_data:
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
                self._add_new_template_variable(var_data, db_template)

    def _add_new_template_variable(self, var_data: Dict[str, Any], db_template: Any) -> None:
        """
        向模板添加新变量

        Args:
            var_data: 变量数据
            db_template: 数据库模板对象
        """
        var_id = var_data.get("id") or str(uuid.uuid4())
        new_var = {
            "id": var_id,
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

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板ID

        Returns:
            是否成功删除
        """
        try:
            # 删除模板会级联删除相关的变量
            result = self.template_repo.delete(template_id)

            if result:
                logger.info(f"成功删除模板: {template_id}")
            else:
                logger.warning(f"删除模板失败，可能不存在此模板: {template_id}")

            return result
        except Exception as e:
            logger.exception(f"删除模板时发生错误: {str(e)}")
            return False

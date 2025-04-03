"""
模板服务模块

提供高级模板操作服务，如模板生成、校验和应用。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.template_engine import TemplateEngine
from ..core.template_manager import TemplateManager
from ..models.template import Template

logger = logging.getLogger(__name__)


class TemplateService:
    """模板服务类"""

    def __init__(self, template_manager: TemplateManager, template_engine: TemplateEngine):
        """
        初始化模板服务

        Args:
            template_manager: 模板管理器
            template_engine: 模板引擎
        """
        self.template_manager = template_manager
        self.template_engine = template_engine

    def create_rule_from_template(
        self, template_id: str, variables: Dict[str, Any], output_path: Optional[str] = None
    ) -> str:
        """
        从模板创建规则

        Args:
            template_id: 模板ID
            variables: 变量值字典
            output_path: 输出文件路径

        Returns:
            生成的规则内容
        """
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        return self.template_engine.apply_template(template, variables, output_path)

    def validate_template_variables(
        self, template_id: str, variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        验证模板变量

        Args:
            template_id: 模板ID
            variables: 变量值字典

        Returns:
            错误信息字典，如果验证通过则为空字典
        """
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        return template.validate_variable_values(variables)

    def get_template_with_defaults(self, template_id: str) -> Dict[str, Any]:
        """
        获取模板及其变量默认值

        Args:
            template_id: 模板ID

        Returns:
            包含模板信息和默认变量值的字典
        """
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")

        defaults = {}
        for var in template.variables:
            if var.default is not None:
                defaults[var.name] = var.default

        return {"template": template, "defaults": defaults}

    def batch_create_rules(
        self, templates_data: List[Dict[str, Any]], base_output_dir: str
    ) -> Dict[str, str]:
        """
        批量创建规则

        Args:
            templates_data: 模板数据列表，每项包含template_id和variables
            base_output_dir: 输出目录基路径

        Returns:
            文件路径与生成内容的字典
        """
        results = {}

        for item in templates_data:
            template_id = item.get("template_id")
            variables = item.get("variables", {})
            output_filename = item.get("output_filename")

            if not template_id or not output_filename:
                logger.warning(f"跳过无效的模板数据: {item}")
                continue

            try:
                template = self.template_manager.get_template(template_id)
                if not template:
                    logger.warning(f"模板不存在: {template_id}")
                    continue

                # 构建输出路径
                output_path = os.path.join(base_output_dir, output_filename)

                # 应用模板
                content = self.template_engine.apply_template(template, variables, output_path)
                results[output_path] = content

            except Exception as e:
                logger.error(f"应用模板 {template_id} 失败: {str(e)}")

        return results

    def find_templates_by_type(self, template_type: str) -> List[Template]:
        """
        按类型查找模板

        Args:
            template_type: 模板类型

        Returns:
            匹配的模板列表
        """
        all_templates = self.template_manager.get_all_templates()
        return [t for t in all_templates if t.type == template_type]

    def find_templates_by_tags(self, tags: List[str]) -> List[Template]:
        """
        按标签查找模板

        Args:
            tags: 标签列表

        Returns:
            匹配的模板列表
        """
        return self.template_manager.search_templates(tags=tags)

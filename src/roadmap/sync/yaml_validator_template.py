"""
路线图YAML验证器模板管理模块

负责加载和管理YAML模板
"""

import logging
import os
from typing import Any, Dict, Optional

import yaml

from src.roadmap.sync.yaml_validator_schema import get_default_template_data

logger = logging.getLogger(__name__)


class TemplateManager:
    """YAML模板管理器"""

    def __init__(self, template_path: Optional[str] = None):
        """
        初始化模板管理器

        Args:
            template_path: 模板文件路径，不提供则使用内置模板
        """
        self.template_path = template_path
        self.template_data = None
        self._load_template()

    def _load_template(self) -> None:
        """加载模板数据"""
        try:
            if self.template_path and os.path.exists(self.template_path):
                with open(self.template_path, "r", encoding="utf-8") as f:
                    self.template_data = yaml.safe_load(f)
                logger.info(f"已加载模板: {self.template_path}")
            else:
                # 查找默认模板路径
                default_template = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "templates",
                    "roadmap",
                    "standard_roadmap_template.yaml",
                )

                if os.path.exists(default_template):
                    with open(default_template, "r", encoding="utf-8") as f:
                        self.template_data = yaml.safe_load(f)
                    logger.info(f"已加载默认模板: {default_template}")
                else:
                    # 创建默认模板数据
                    self.template_data = get_default_template_data()
                    logger.info("使用默认模板数据")
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")
            self.template_data = {}

    def get_template(self) -> Dict[str, Any]:
        """
        获取模板数据

        Returns:
            Dict[str, Any]: 模板数据
        """
        if not self.template_data:
            return get_default_template_data()
        return self.template_data

    def format_template(self) -> str:
        """
        格式化模板为YAML字符串

        Returns:
            str: 格式化的YAML模板
        """
        if not self.template_data:
            return "模板数据不可用"

        return yaml.dump(
            self.template_data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

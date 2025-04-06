"""
路线图YAML验证器主模块

提供路线图YAML文件的格式验证和自动修复功能
该模块整合了各个验证逻辑子模块
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.roadmap.sync.yaml_validator_core import RoadmapValidator
from src.roadmap.sync.yaml_validator_output import ValidatorOutput
from src.roadmap.sync.yaml_validator_template import TemplateManager

logger = logging.getLogger(__name__)


class RoadmapYamlValidator:
    """路线图YAML验证器"""

    def __init__(self, template_path: str = None):
        """
        初始化验证器

        Args:
            template_path: 模板文件路径，不提供则使用内置模板
        """
        self.template_manager = TemplateManager(template_path)
        self.roadmap_validator = RoadmapValidator(self.template_manager)

    def validate(self, yaml_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证YAML文件格式

        Args:
            yaml_path: YAML文件路径

        Returns:
            Tuple[bool, List[str], Dict[str, Any]]:
                - 是否有效
                - 错误/警告消息列表
                - 验证后的数据（可能包含自动修复）
        """
        return self.roadmap_validator.validate_yaml(yaml_path)

    def generate_fixed_yaml(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        生成修复后的YAML文件

        Args:
            data: 修复后的数据
            output_path: 输出文件路径

        Returns:
            bool: 是否成功生成
        """
        # 确保data不为空
        if not data:
            data = self.template_manager.get_template()
            logger.info("使用模板数据生成修复文件")

        return ValidatorOutput.generate_fixed_yaml(data, output_path)

    def show_template(self) -> str:
        """
        显示标准模板

        Returns:
            str: 格式化的YAML模板
        """
        return self.template_manager.format_template()

    def check_and_suggest(self, yaml_path: str, fix: bool = False) -> Tuple[bool, str]:
        """
        检查YAML文件并给出建议

        Args:
            yaml_path: YAML文件路径
            fix: 是否生成修复后的文件

        Returns:
            Tuple[bool, str]:
                - 是否有效
                - 格式化的检查结果消息
        """
        if not os.path.exists(yaml_path):
            return False, f"❌ 错误: 文件 '{yaml_path}' 不存在"

        is_valid, messages, fixed_data = self.validate(yaml_path)

        # 生成格式化的报告
        report = ValidatorOutput.format_check_report(yaml_path, is_valid, messages, fixed_data, fix)

        return is_valid, report

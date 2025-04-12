"""
验证器工厂模块

根据需要创建不同类型的验证器
"""

import logging
import os
from typing import Any, Dict, Optional, Type

from src.validation.core.base_validator import BaseValidator
from src.validation.core.roadmap_validator import RoadmapCoreValidator
from src.validation.core.rule_validator import RuleValidator
from src.validation.core.template_validator import TemplateValidator
from src.validation.core.yaml_validator import YamlValidator
from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)


class ValidatorFactory:
    """验证器工厂类，用于创建各种类型的验证器"""

    # 验证器类型映射
    _validators: Dict[str, Type[BaseValidator]] = {
        "yaml": YamlValidator,
        "rule": RuleValidator,
        "template": TemplateValidator,
        "roadmap": RoadmapCoreValidator,
    }

    @classmethod
    def get_validator(cls, validator_type: str) -> BaseValidator:
        """
        获取指定类型的验证器

        Args:
            validator_type: 验证器类型，可以是 "yaml", "rule", "template", "roadmap" 等

        Returns:
            BaseValidator: 验证器实例
        """
        if validator_type not in cls._validators:
            raise ValueError(f"不支持的验证器类型: {validator_type}。支持的类型: {list(cls._validators.keys())}")

        # 创建并返回验证器实例
        return cls._validators[validator_type]()

    @classmethod
    def register_validator(cls, validator_type: str, validator_class: Type[BaseValidator]) -> None:
        """
        注册一个新的验证器类型

        Args:
            validator_type: 验证器类型名称
            validator_class: 验证器类
        """
        cls._validators[validator_type] = validator_class

    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取所有支持的验证器类型

        Returns:
            list: 支持的验证器类型列表
        """
        return list(cls._validators.keys())

    @classmethod
    def get_validator_for_file(cls, file_path: str, config: Optional[Dict[str, Any]] = None) -> BaseValidator:
        """
        根据文件类型获取适合的验证器

        Args:
            file_path: 文件路径
            config: 配置参数

        Returns:
            适合的验证器实例
        """
        # 根据文件扩展名判断类型
        _, ext = os.path.splitext(file_path.lower())

        if ext in [".yaml", ".yml"]:
            # 进一步判断是什么类型的YAML
            try:
                import yaml

                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if isinstance(data, dict):
                    # 根据内容判断类型
                    if "epics" in data or "milestones" in data:
                        logger.info(f"文件 {file_path} 识别为路线图文件")
                        return cls.get_validator("roadmap")
                    elif data.get("type") == "rule" or "rule" in file_path.lower():
                        logger.info(f"文件 {file_path} 识别为规则文件")
                        return cls.get_validator("rule")
                    elif data.get("type") == "template" or "template" in file_path.lower():
                        logger.info(f"文件 {file_path} 识别为模板文件")
                        return cls.get_validator("template")
            except Exception as e:
                logger.warning(f"尝试解析文件 {file_path} 时出错: {str(e)}")

            # 默认返回YAML验证器
            return cls.get_validator("yaml")
        elif ext in [".json"]:
            # 可以添加JSON验证器
            return cls.get_validator("yaml")  # 暂时使用YAML验证器
        elif ext in [".md", ".mdc"]:
            # 对于Markdown文件，判断是否是规则
            if "rule" in file_path.lower():
                return cls.get_validator("rule")

        # 默认返回基本验证器
        logger.info(f"文件 {file_path} 没有匹配特定验证器，使用默认YAML验证器")
        return cls.get_validator("yaml")

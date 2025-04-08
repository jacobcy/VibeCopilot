"""
验证器工厂模块

根据需要创建不同类型的验证器
"""

import logging
import os
from typing import Any, Dict, Optional, Type

from src.validation.core.base_validator import BaseValidator
from src.validation.core.rule_validator import RuleValidator
from src.validation.core.template_validator import TemplateValidator
from src.validation.core.yaml_validator import YamlValidator

logger = logging.getLogger(__name__)


class ValidatorFactory:
    """验证器工厂，负责创建各种类型的验证器"""

    # 预定义的验证器映射
    _validators = {
        "rule": RuleValidator,
        "template": TemplateValidator,
        "yaml": YamlValidator,
    }

    @classmethod
    def get_validator(cls, validator_type: str, schema_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> BaseValidator:
        """
        获取指定类型的验证器

        Args:
            validator_type: 验证器类型
            schema_path: 模式文件路径
            config: 配置参数

        Returns:
            验证器实例
        """
        validator_class = cls._validators.get(validator_type.lower())

        if not validator_class:
            logger.warning(f"未找到类型为 {validator_type} 的验证器，使用默认YAML验证器")
            validator_class = YamlValidator

        return validator_class(schema_path, config)

    @classmethod
    def register_validator(cls, validator_type: str, validator_class: Type[BaseValidator]) -> None:
        """
        注册新的验证器类型

        Args:
            validator_type: 验证器类型名称
            validator_class: 验证器类
        """
        if not issubclass(validator_class, BaseValidator):
            raise TypeError(f"验证器类必须继承自BaseValidator")

        cls._validators[validator_type.lower()] = validator_class
        logger.info(f"已注册验证器类型: {validator_type}")

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
                    if data.get("type") == "rule" or "rule" in file_path.lower():
                        return cls.get_validator("rule", config=config)
                    elif data.get("type") == "template" or "template" in file_path.lower():
                        return cls.get_validator("template", config=config)
            except Exception:
                pass

            # 默认返回YAML验证器
            return cls.get_validator("yaml", config=config)
        elif ext in [".json"]:
            # 可以添加JSON验证器
            return cls.get_validator("yaml", config=config)  # 暂时使用YAML验证器
        elif ext in [".md", ".mdc"]:
            # 对于Markdown文件，判断是否是规则
            if "rule" in file_path.lower():
                return cls.get_validator("rule", config=config)

        # 默认返回基本验证器
        return YamlValidator(config=config)

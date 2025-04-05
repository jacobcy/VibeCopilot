"""
模板模型模块 (已重定向)

注意: 此模块已被重定向到src.models.db
请使用 from src.models.db import Template 替代 from src.rule_engine.models.template import Template

包含规则模板相关的所有数据模型:
- 模板变量
- 模板元数据
- 模板模型
"""

# 导入相关类型
from pathlib import Path
from typing import Dict, List, Optional, Union

# 从新位置导入
from src.models.db import (
    Template,
    TemplateMetadata,
    TemplateRepository,
    TemplateVariable,
    TemplateVariableType,
)

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = [
    "Template",
    "TemplateVariable",
    "TemplateMetadata",
    "TemplateRepository",
    "TemplateVariableType",
]

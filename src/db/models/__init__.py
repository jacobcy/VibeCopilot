"""
数据库模型包

导出所有数据模型类，方便其他模块导入
注意: 这个包已经废弃，请直接从src.models.db导入
"""

# 从标准模型包导入所有需要的类
from src.models.db import MemoryItem, Rule, RuleExample, RuleItem, Template, TemplateVariable, WorkflowDefinition

__all__ = ["MemoryItem", "Rule", "RuleItem", "RuleExample", "Template", "TemplateVariable", "WorkflowDefinition"]

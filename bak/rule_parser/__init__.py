"""
规则解析器模块 - 直接转发到新的统一解析框架

此模块已被 src.parsing 和相关处理器替代，此文件仅做转发以保持最小兼容性。
"""

from src.parsing import create_parser
from src.parsing.processors.rule_processor import RuleProcessor

# 为了保持兼容
RuleParser = RuleProcessor


# 兼容函数
def parse_rule_file(file_path, backend="openai"):
    """解析规则文件 (兼容函数)"""
    processor = RuleProcessor(backend=backend)
    return processor.process_rule_file(file_path)


def detect_rule_conflicts(rules_data):
    """检测规则冲突 (简化兼容函数)"""
    # 简化实现，实际可能需要更复杂的逻辑
    rule_ids = set()
    conflicts = []

    for rule in rules_data:
        rule_id = rule.get("rule_id") or rule.get("id")
        if rule_id in rule_ids:
            conflicts.append(rule_id)
        else:
            rule_ids.add(rule_id)

    return conflicts


# 导出所需内容
__all__ = ["RuleParser", "parse_rule_file", "detect_rule_conflicts"]

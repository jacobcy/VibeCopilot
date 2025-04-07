"""
规则引擎模块

负责：
- 规则加载和解析
- 规则优先级处理
- 规则执行上下文管理
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from src.core.exceptions import RuleError

logger = logging.getLogger(__name__)


class RuleEngine:
    """规则引擎类"""

    def __init__(self):
        """初始化规则引擎"""
        self.rules = {}
        self.rule_priorities = {}
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化规则集"""
        try:
            rules_dir = os.getenv("VIBE_RULES_DIR", "rules")
            if os.path.exists(rules_dir):
                self.load_rules(rules_dir)
        except Exception as e:
            logger.warning(f"初始化规则失败: {e}")

    def _validate_rule(self, rule_def: Dict[str, Any]) -> bool:
        """验证规则定义

        Args:
            rule_def: 规则定义字典

        Returns:
            bool: 验证是否通过

        Raises:
            RuleError: 规则验证失败
        """
        required_fields = ["name", "pattern", "action"]

        # 检查必要字段
        for field in required_fields:
            if field not in rule_def:
                raise RuleError(f"规则缺少必要字段: {field}", "E202")

        # 验证规则模式
        if not isinstance(rule_def["pattern"], str):
            raise RuleError("规则模式必须是字符串", "E202")

        # 验证规则动作
        if not isinstance(rule_def["action"], dict):
            raise RuleError("规则动作必须是字典", "E202")

        return True

    def load_rules(self, rules_dir: str) -> None:
        """加载规则文件

        Args:
            rules_dir: 规则文件目录

        Raises:
            RuleError: 规则加载失败
        """
        try:
            for root, _, files in os.walk(rules_dir):
                for file in files:
                    if file.endswith((".yml", ".yaml")):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            rule_def = yaml.safe_load(f)
                            if self._validate_rule(rule_def):
                                self.add_rule(rule_def["name"], rule_def, priority=rule_def.get("priority", 0))
        except Exception as e:
            raise RuleError(f"加载规则失败: {str(e)}", "E201")

    def add_rule(self, rule_name: str, rule_def: Dict[str, Any], priority: int = 0):
        """添加规则

        Args:
            rule_name: 规则名称
            rule_def: 规则定义
            priority: 规则优先级（数字越大优先级越高）
        """
        if self._validate_rule(rule_def):
            self.rules[rule_name] = rule_def
            self.rule_priorities[rule_name] = priority

    def get_rule(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """获取规则

        Args:
            rule_name: 规则名称

        Returns:
            Optional[Dict[str, Any]]: 规则定义，不存在时返回None
        """
        return self.rules.get(rule_name)

    def get_matching_rules(self, command: str) -> List[Dict[str, Any]]:
        """获取匹配的规则列表

        Args:
            command: 命令字符串

        Returns:
            List[Dict[str, Any]]: 匹配的规则列表，按优先级排序
        """
        matching_rules = []
        for name, rule in self.rules.items():
            if rule["pattern"] in command:  # 简单的字符串匹配，可以改进为正则匹配
                matching_rules.append((name, rule))

        # 按优先级排序
        return [rule for _, rule in sorted(matching_rules, key=lambda x: self.rule_priorities[x[0]], reverse=True)]

    def process_command(self, command: str) -> Dict[str, Any]:
        """处理命令

        Args:
            command: 要处理的命令字符串

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            matching_rules = self.get_matching_rules(command)

            if not matching_rules:
                return {"handled": False}

            # 执行优先级最高的规则
            rule = matching_rules[0]
            logger.info(f"使用规则 {rule['name']} 处理命令")

            return {
                "handled": True,
                "success": True,
                "rule": rule["name"],
                "action": rule["action"],
            }

        except Exception as e:
            error_msg = f"规则引擎处理失败: {str(e)}"
            logger.error(error_msg)
            return {"handled": True, "success": False, "error": error_msg}

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """获取可用命令列表

        Returns:
            List[Dict[str, Any]]: 可用命令列表
        """
        commands = []
        for name, rule in self.rules.items():
            if "command" in rule:
                commands.append(
                    {
                        "name": name,
                        "description": rule.get("description", "无描述"),
                        "handler": rule.get("action", {}).get("handler", "unknown"),
                    }
                )
        return commands

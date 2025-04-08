#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Rule:
    """规则数据类"""

    name: str
    type: str
    description: str
    priority: int
    enabled: bool = True
    content: str = ""


class RuleManager:
    """规则管理器"""

    def __init__(self):
        """初始化规则管理器"""
        self.rules_dir = os.path.join(os.getcwd(), "rules")
        os.makedirs(self.rules_dir, exist_ok=True)

    def list_rules(self, rule_type: Optional[str] = None) -> List[Rule]:
        """列出规则"""
        rules = []
        for rule_file in os.listdir(self.rules_dir):
            if not rule_file.endswith(".md"):
                continue

            rule = self._load_rule(rule_file)
            if rule and (not rule_type or rule.type == rule_type):
                rules.append(rule)

        return sorted(rules, key=lambda x: (-x.priority, x.name))

    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """获取规则"""
        rule_path = os.path.join(self.rules_dir, f"{rule_name}.md")
        if not os.path.exists(rule_path):
            return None
        return self._load_rule(f"{rule_name}.md")

    def create_rule(self, name: str, rule_type: str, description: str, priority: int = 50) -> None:
        """创建规则"""
        rule_path = os.path.join(self.rules_dir, f"{name}.md")
        if os.path.exists(rule_path):
            raise ValueError(f"规则 '{name}' 已存在")

        content = f"""---
type: {rule_type}
description: {description}
priority: {priority}
enabled: true
---

# {name}

{description}

## 使用场景

## 规则内容

## 示例
"""
        with open(rule_path, "w", encoding="utf-8") as f:
            f.write(content)

    def edit_rule(self, rule_name: str) -> None:
        """编辑规则"""
        rule_path = os.path.join(self.rules_dir, f"{rule_name}.md")
        if not os.path.exists(rule_path):
            raise ValueError(f"规则 '{rule_name}' 不存在")

        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, rule_path])

    def delete_rule(self, rule_name: str, force: bool = False) -> None:
        """删除规则"""
        rule_path = os.path.join(self.rules_dir, f"{rule_name}.md")
        if not os.path.exists(rule_path):
            raise ValueError(f"规则 '{rule_name}' 不存在")

        if not force:
            rule = self._load_rule(f"{rule_name}.md")
            if rule and rule.enabled:
                raise ValueError(f"规则 '{rule_name}' 当前处于启用状态，请先禁用或使用 --force 强制删除")

        os.remove(rule_path)

    def enable_rule(self, rule_name: str) -> None:
        """启用规则"""
        self._update_rule_status(rule_name, True)

    def disable_rule(self, rule_name: str) -> None:
        """禁用规则"""
        self._update_rule_status(rule_name, False)

    def _load_rule(self, filename: str) -> Optional[Rule]:
        """从文件加载规则"""
        rule_path = os.path.join(self.rules_dir, filename)
        if not os.path.exists(rule_path):
            return None

        with open(rule_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析Front Matter
        if not content.startswith("---"):
            return None

        end_index = content.find("---", 3)
        if end_index == -1:
            return None

        try:
            front_matter = content[3:end_index].strip()
            metadata = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in front_matter.split("\n") if ":" in line}

            return Rule(
                name=os.path.splitext(filename)[0],
                type=metadata.get("type", ""),
                description=metadata.get("description", ""),
                priority=int(metadata.get("priority", "50")),
                enabled=metadata.get("enabled", "true").lower() == "true",
                content=content[end_index + 3 :].strip(),
            )
        except Exception:
            return None

    def _update_rule_status(self, rule_name: str, enabled: bool) -> None:
        """更新规则状态"""
        rule_path = os.path.join(self.rules_dir, f"{rule_name}.md")
        if not os.path.exists(rule_path):
            raise ValueError(f"规则 '{rule_name}' 不存在")

        with open(rule_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith("---"):
            raise ValueError(f"规则 '{rule_name}' 格式错误")

        end_index = content.find("---", 3)
        if end_index == -1:
            raise ValueError(f"规则 '{rule_name}' 格式错误")

        front_matter = content[3:end_index].strip()
        updated_front_matter = []
        found_enabled = False

        for line in front_matter.split("\n"):
            if line.startswith("enabled:"):
                updated_front_matter.append(f"enabled: {str(enabled).lower()}")
                found_enabled = True
            else:
                updated_front_matter.append(line)

        if not found_enabled:
            updated_front_matter.append(f"enabled: {str(enabled).lower()}")

        new_content = f"---\n{chr(10).join(updated_front_matter)}\n---\n{content[end_index + 3:].strip()}"

        with open(rule_path, "w", encoding="utf-8") as f:
            f.write(new_content)

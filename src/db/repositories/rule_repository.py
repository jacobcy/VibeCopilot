"""
规则仓库模块

提供Rule、RuleItem和RuleExample数据访问实现，使用统一的Repository模式。
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Rule, RuleExample, RuleItem


class RuleRepository(Repository[Rule]):
    """Rule仓库类 (无状态)"""

    def __init__(self):
        """初始化Rule仓库"""
        super().__init__(Rule)

    def get_by_name(self, session: Session, name: str) -> Optional[Rule]:
        """根据名称获取规则

        Args:
            session: SQLAlchemy会话对象
            name: 规则名称

        Returns:
            Rule对象或None
        """
        return session.query(Rule).filter(Rule.name == name).first()

    def get_by_type(self, session: Session, rule_type: str) -> List[Rule]:
        """根据类型获取规则

        Args:
            session: SQLAlchemy会话对象
            rule_type: 规则类型

        Returns:
            Rule对象列表
        """
        return session.query(Rule).filter(Rule.type == rule_type).all()

    def get_for_file(self, session: Session, file_path: str) -> List[Rule]:
        """获取适用于指定文件的规则

        Args:
            session: SQLAlchemy会话对象
            file_path: 文件路径

        Returns:
            适用的Rule对象列表
        """
        # 获取所有规则
        all_rules = self.get_all(session)

        # 筛选出始终应用的规则和文件模式匹配的规则
        applicable_rules = []

        for rule in all_rules:
            # 检查是否始终应用
            if rule.always_apply:
                applicable_rules.append(rule)
                continue

            # 检查文件模式匹配
            rule_globs = json.loads(rule.globs) if rule.globs else []
            if not rule_globs:
                continue

            # 文件路径匹配检查（简化实现）
            # 在实际应用中，应该使用glob模块进行更准确的匹配
            for pattern in rule_globs:
                if self._glob_match(file_path, pattern):
                    applicable_rules.append(rule)
                    break

        return applicable_rules

    def _glob_match(self, path: str, pattern: str) -> bool:
        """简化的glob匹配实现

        Args:
            path: 文件路径
            pattern: glob模式

        Returns:
            是否匹配
        """
        # 注意：这是一个简化实现，真实场景应使用glob模块
        import fnmatch

        return fnmatch.fnmatch(path, pattern)

    def search_by_tags(self, session: Session, tags: List[str]) -> List[Rule]:
        """根据标签搜索规则

        Args:
            session: SQLAlchemy会话对象
            tags: 标签列表

        Returns:
            匹配的Rule对象列表
        """
        rules = self.get_all(session)
        if not tags:
            return rules

        results = []
        for rule in rules:
            rule_tags = json.loads(rule.tags) if rule.tags else []
            if any(tag in rule_tags for tag in tags):
                results.append(rule)

        return results

    def create_rule(self, session: Session, rule_data: Dict[str, Any], items: List[Dict[str, Any]], examples: List[Dict[str, Any]]) -> Rule:
        """创建规则及其条目和示例

        Args:
            session: SQLAlchemy会话对象
            rule_data: 规则数据
            items: 规则条目数据列表
            examples: 规则示例数据列表

        Returns:
            创建的Rule对象
        """
        if "id" not in rule_data or not rule_data["id"]:
            if "name" in rule_data and rule_data["name"]:
                from ..utils.text import normalize_string

                rule_data["id"] = normalize_string(rule_data["name"])
            else:
                rule_data["id"] = f"rule_{uuid.uuid4().hex[:8]}"

        rule = self.create(session, rule_data)

        item_repo = RuleItemRepository()
        for item_data in items:
            item_id = f"{rule.id}-item-{len(rule.items) + 1}"
            item = item_repo.create(session, {**item_data, "id": item_id})
            rule.items.append(item)

        example_repo = RuleExampleRepository()
        for example_data in examples:
            example_id = f"{rule.id}-example-{len(rule.examples) + 1}"
            example = example_repo.create(session, {**example_data, "id": example_id})
            rule.examples.append(example)

        return rule

    def update_rule_with_relations(
        self,
        session: Session,
        rule_id: str,
        rule_data: Dict[str, Any],
        items: Optional[List[Dict[str, Any]]] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Rule]:
        """更新规则及其关联数据

        Args:
            session: SQLAlchemy会话对象
            rule_id: 规则ID
            rule_data: 规则数据
            items: 规则条目数据列表
            examples: 规则示例数据列表

        Returns:
            更新后的Rule对象或None
        """
        rule = self.get_by_id(session, rule_id)
        if not rule:
            return None

        for key, value in rule_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        if items is not None:
            rule.items = []
            item_repo = RuleItemRepository()
            for item_data in items:
                item_id = f"{rule.id}-item-{len(rule.items) + 1}"
                item = item_repo.create(session, {**item_data, "id": item_id})
                rule.items.append(item)

        if examples is not None:
            rule.examples = []
            example_repo = RuleExampleRepository()
            for example_data in examples:
                example_id = f"{rule.id}-example-{len(rule.examples) + 1}"
                example = example_repo.create(session, {**example_data, "id": example_id})
                rule.examples.append(example)

        return rule


class RuleItemRepository(Repository[RuleItem]):
    """RuleItem仓库类 (无状态)"""

    def __init__(self):
        """初始化RuleItem仓库"""
        super().__init__(RuleItem)

    def get_by_rule(self, session: Session, rule_id: str) -> List[RuleItem]:
        """获取规则的所有条目

        Args:
            session: SQLAlchemy会话对象
            rule_id: 规则ID

        Returns:
            RuleItem对象列表
        """
        return session.query(RuleItem).filter(RuleItem.rules.any(id=rule_id)).all()

    def get_by_category(self, session: Session, category: str) -> List[RuleItem]:
        """获取特定分类的规则条目

        Args:
            session: SQLAlchemy会话对象
            category: 分类名称

        Returns:
            RuleItem对象列表
        """
        return session.query(RuleItem).filter(RuleItem.category == category).all()

    def get_high_priority_items(self, session: Session, priority_threshold: int = 5) -> List[RuleItem]:
        """获取高优先级的规则条目

        Args:
            session: SQLAlchemy会话对象
            priority_threshold: 优先级阈值，默认为5

        Returns:
            RuleItem对象列表
        """
        return session.query(RuleItem).filter(RuleItem.priority >= priority_threshold).all()


class RuleExampleRepository(Repository[RuleExample]):
    """RuleExample仓库类 (无状态)"""

    def __init__(self):
        """初始化RuleExample仓库"""
        super().__init__(RuleExample)

    def get_by_rule(self, session: Session, rule_id: str) -> List[RuleExample]:
        """获取规则的所有示例

        Args:
            session: SQLAlchemy会话对象
            rule_id: 规则ID

        Returns:
            RuleExample对象列表
        """
        return session.query(RuleExample).filter(RuleExample.rules.any(id=rule_id)).all()

    def get_valid_examples(self, session: Session) -> List[RuleExample]:
        """获取所有有效示例

        Returns:
            有效的RuleExample对象列表
        """
        return session.query(RuleExample).filter(RuleExample.is_valid == True).all()

    def get_invalid_examples(self, session: Session) -> List[RuleExample]:
        """获取所有无效示例

        Returns:
            无效的RuleExample对象列表
        """
        return session.query(RuleExample).filter(RuleExample.is_valid == False).all()

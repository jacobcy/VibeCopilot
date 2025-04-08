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
    """Rule仓库类"""

    def __init__(self, session: Session):
        """初始化Rule仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Rule)

    def get_by_name(self, name: str) -> Optional[Rule]:
        """根据名称获取规则

        Args:
            name: 规则名称

        Returns:
            Rule对象或None
        """
        return self.session.query(Rule).filter(Rule.name == name).first()

    def get_by_type(self, rule_type: str) -> List[Rule]:
        """根据类型获取规则

        Args:
            rule_type: 规则类型

        Returns:
            Rule对象列表
        """
        return self.session.query(Rule).filter(Rule.type == rule_type).all()

    def get_for_file(self, file_path: str) -> List[Rule]:
        """获取适用于指定文件的规则

        Args:
            file_path: 文件路径

        Returns:
            适用的Rule对象列表
        """
        # 获取所有规则
        all_rules = self.get_all()

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

    def search_by_tags(self, tags: List[str]) -> List[Rule]:
        """根据标签搜索规则

        Args:
            tags: 标签列表

        Returns:
            匹配的Rule对象列表
        """
        rules = self.get_all()
        if not tags:
            return rules

        results = []
        for rule in rules:
            rule_tags = json.loads(rule.tags) if rule.tags else []
            if any(tag in rule_tags for tag in tags):
                results.append(rule)

        return results

    def create_rule(self, rule_data: Dict[str, Any], items: List[Dict[str, Any]], examples: List[Dict[str, Any]]) -> Rule:
        """创建规则及其条目和示例

        Args:
            rule_data: 规则数据
            items: 规则条目数据列表
            examples: 规则示例数据列表

        Returns:
            创建的Rule对象
        """
        # 确保rule_data中有id字段
        if "id" not in rule_data or not rule_data["id"]:
            # 如果id不存在或为空，则自动生成一个id
            if "name" in rule_data and rule_data["name"]:
                # 如果有名称，则使用名称生成id
                from ..utils.text import normalize_string

                rule_data["id"] = normalize_string(rule_data["name"])
            else:
                # 否则生成一个随机id
                rule_data["id"] = f"rule_{uuid.uuid4().hex[:8]}"

        # 创建规则
        rule = self.create(rule_data)

        # 创建规则条目
        item_repo = RuleItemRepository(self.session)
        for item_data in items:
            item_id = f"{rule.id}-item-{len(rule.items) + 1}"
            item = item_repo.create({**item_data, "id": item_id})
            rule.items.append(item)

        # 创建规则示例
        example_repo = RuleExampleRepository(self.session)
        for example_data in examples:
            example_id = f"{rule.id}-example-{len(rule.examples) + 1}"
            example = example_repo.create({**example_data, "id": example_id})
            rule.examples.append(example)

        self.session.commit()
        return rule

    def update_rule_with_relations(
        self, rule_id: str, rule_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None, examples: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Rule]:
        """更新规则及其关联数据

        Args:
            rule_id: 规则ID
            rule_data: 规则数据
            items: 规则条目数据列表
            examples: 规则示例数据列表

        Returns:
            更新后的Rule对象或None
        """
        rule = self.get_by_id(rule_id)
        if not rule:
            return None

        # 更新规则属性
        for key, value in rule_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        # 更新规则条目
        if items is not None:
            # 清除现有条目
            rule.items = []

            # 添加新条目
            item_repo = RuleItemRepository(self.session)
            for item_data in items:
                item_id = f"{rule.id}-item-{len(rule.items) + 1}"
                item = item_repo.create({**item_data, "id": item_id})
                rule.items.append(item)

        # 更新规则示例
        if examples is not None:
            # 清除现有示例
            rule.examples = []

            # 添加新示例
            example_repo = RuleExampleRepository(self.session)
            for example_data in examples:
                example_id = f"{rule.id}-example-{len(rule.examples) + 1}"
                example = example_repo.create({**example_data, "id": example_id})
                rule.examples.append(example)

        self.session.commit()
        return rule


class RuleItemRepository(Repository[RuleItem]):
    """RuleItem仓库类"""

    def __init__(self, session: Session):
        """初始化RuleItem仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, RuleItem)

    def get_by_rule(self, rule_id: str) -> List[RuleItem]:
        """获取规则的所有条目

        Args:
            rule_id: 规则ID

        Returns:
            RuleItem对象列表
        """
        return self.session.query(RuleItem).filter(RuleItem.rules.any(id=rule_id)).all()

    def get_by_category(self, category: str) -> List[RuleItem]:
        """获取特定分类的规则条目

        Args:
            category: 分类名称

        Returns:
            RuleItem对象列表
        """
        return self.session.query(RuleItem).filter(RuleItem.category == category).all()

    def get_high_priority_items(self, priority_threshold: int = 5) -> List[RuleItem]:
        """获取高优先级的规则条目

        Args:
            priority_threshold: 优先级阈值，默认为5

        Returns:
            RuleItem对象列表
        """
        return self.session.query(RuleItem).filter(RuleItem.priority >= priority_threshold).all()


class RuleExampleRepository(Repository[RuleExample]):
    """RuleExample仓库类"""

    def __init__(self, session: Session):
        """初始化RuleExample仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, RuleExample)

    def get_by_rule(self, rule_id: str) -> List[RuleExample]:
        """获取规则的所有示例

        Args:
            rule_id: 规则ID

        Returns:
            RuleExample对象列表
        """
        return self.session.query(RuleExample).filter(RuleExample.rules.any(id=rule_id)).all()

    def get_valid_examples(self) -> List[RuleExample]:
        """获取所有有效示例

        Returns:
            有效的RuleExample对象列表
        """
        return self.session.query(RuleExample).filter(RuleExample.is_valid is True).all()

    def get_invalid_examples(self) -> List[RuleExample]:
        """获取所有无效示例

        Returns:
            无效的RuleExample对象列表
        """
        return self.session.query(RuleExample).filter(RuleExample.is_valid is False).all()

"""
规则数据库操作模块

处理规则的数据库存储、检索和删除操作
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.db import RuleRepository
from src.models.rule_model import Example, Rule, RuleItem

logger = logging.getLogger(__name__)


class RuleDBOperations:
    """规则数据库操作类，处理规则的持久化存储"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化规则数据库操作类

        Args:
            session: 数据库会话，用于规则存储
        """
        self.session = session
        self.rule_repository = RuleRepository(session) if session else None
        self._db_available = bool(session)

    def save_rule(self, rule: Rule, overwrite: bool = False) -> Optional[Rule]:
        """
        保存规则到数据库

        Args:
            rule: 要保存的规则
            overwrite: 是否覆盖已存在的规则

        Returns:
            保存后的规则，如果失败则返回None
        """
        if not self._db_available or not self.rule_repository:
            logger.warning(f"数据库不可用，无法保存规则: {rule.id}")
            return None

        try:
            # 检查规则是否已存在
            existing_rule = self.rule_repository.get_by_id(rule.id)
            if existing_rule and not overwrite:
                logger.warning(f"规则已存在，未启用覆盖模式: {rule.id}")
                return Rule.parse_obj(existing_rule.to_pydantic().dict())

            # 保存规则到数据库
            if existing_rule:
                # 更新现有规则
                updated_rule = self.rule_repository.update(rule.id, rule.dict(exclude={"items", "examples"}))
                # 更新规则与其条目和示例的关联
                self.rule_repository.update_rule_with_relations(
                    rule.id,
                    rule.dict(exclude={"items", "examples"}),
                    [item.dict() for item in rule.items],
                    [example.dict() for example in rule.examples],
                )
                logger.info(f"规则更新成功: {rule.id}")
                return Rule.parse_obj(updated_rule.to_pydantic().dict())
            else:
                # 创建新规则
                try:
                    # 准备数据库存储所需的完整数据
                    db_rule_data = self._prepare_rule_data(rule)
                    items_data = [item.dict() for item in rule.items]
                    examples_data = [example.dict() for example in rule.examples]

                    new_rule = self.rule_repository.create_rule(db_rule_data, items_data, examples_data)
                    logger.info(f"规则创建成功: {rule.id}")
                    return Rule.parse_obj(new_rule.to_pydantic().dict())
                except Exception as e:
                    logger.error(f"创建规则失败: {str(e)}")
                    # 由于无法存储到数据库，返回None
                    return None
        except SQLAlchemyError as e:
            logger.error(f"数据库操作错误: {str(e)}")
            # 标记数据库不可用
            self._db_available = False
            return None
        except Exception as e:
            logger.error(f"处理规则时出错: {str(e)}")
            return None

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        从数据库获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，如果不存在则返回None
        """
        if not self._db_available or not self.rule_repository:
            logger.warning(f"数据库不可用，无法获取规则: {rule_id}")
            return None

        try:
            rule_entity = self.rule_repository.get_by_id(rule_id)
            if not rule_entity:
                logger.warning(f"规则不存在: {rule_id}")
                return None

            # 将数据库实体转换为Pydantic模型
            rule_pydantic = rule_entity.to_pydantic()
            return Rule.parse_obj(rule_pydantic.dict())
        except Exception as e:
            logger.error(f"获取规则时出错: {str(e)}")
            return None

    def list_rules(self, rule_type: Optional[str] = None) -> List[Rule]:
        """
        列出数据库中的规则

        Args:
            rule_type: 规则类型过滤

        Returns:
            规则列表
        """
        if not self._db_available or not self.rule_repository:
            logger.warning("数据库不可用，无法列出规则")
            return []

        try:
            # 根据规则类型获取规则
            if rule_type:
                rule_entities = self.rule_repository.get_by_type(rule_type)
            else:
                rule_entities = self.rule_repository.get_all()

            # 将数据库实体转换为Pydantic模型
            rules = []
            for entity in rule_entities:
                try:
                    rule_pydantic = entity.to_pydantic()
                    rules.append(Rule.parse_obj(rule_pydantic.dict()))
                except Exception as e:
                    logger.error(f"处理规则 {entity.id} 时出错: {str(e)}")

            return rules
        except Exception as e:
            logger.error(f"列出规则时出错: {str(e)}")
            return []

    def delete_rule(self, rule_id: str) -> bool:
        """
        从数据库删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        if not self._db_available or not self.rule_repository:
            logger.warning(f"数据库不可用，无法删除规则: {rule_id}")
            return False

        try:
            success = self.rule_repository.delete(rule_id)
            if success:
                logger.info(f"规则删除成功: {rule_id}")
            else:
                logger.warning(f"规则删除失败: {rule_id}")
            return success
        except Exception as e:
            logger.error(f"删除规则时出错: {str(e)}")
            return False

    def _prepare_rule_data(self, rule: Rule) -> Dict[str, Any]:
        """
        准备规则数据以便存储到数据库

        Args:
            rule: 规则对象

        Returns:
            格式化的规则数据
        """
        return {
            "id": rule.id,
            "name": rule.name,
            "type": rule.type,
            "description": rule.description,
            "content": rule.content,
            "globs": rule.globs if rule.globs else [],
            "always_apply": rule.always_apply,
            "author": rule.metadata.author if rule.metadata and rule.metadata.author else "系统",
            "version": rule.metadata.version if rule.metadata and rule.metadata.version else "1.0.0",
            "tags": rule.metadata.tags if rule.metadata and rule.metadata.tags else [],
            "dependencies": rule.metadata.dependencies if rule.metadata and rule.metadata.dependencies else [],
        }

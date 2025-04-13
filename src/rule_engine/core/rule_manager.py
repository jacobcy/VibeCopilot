"""
规则管理器模块

提供规则的生命周期管理、数据库操作和导入导出功能
"""

import logging
from typing import Dict, List, Optional, Union

from src.models.rule_model import Rule
from src.parsing.processors.rule_processor import RuleProcessor
from src.rule_engine.core.rule_importer import import_rule_from_content, import_rule_from_file
from src.rule_engine.exporters.rule_exporter import export_rule_to_yaml

logger = logging.getLogger(__name__)


class RuleManager:
    """规则管理器类"""

    def __init__(self, db_session=None):
        """
        初始化规则管理器

        Args:
            db_session: 数据库会话对象
        """
        self.db_session = db_session
        self.rule_processor = RuleProcessor()
        logger.info("规则管理器初始化完成")

    def import_rule(self, rule_path: str) -> Rule:
        """
        从文件导入规则

        Args:
            rule_path: 规则文件路径

        Returns:
            导入的规则对象
        """
        try:
            rule = import_rule_from_file(rule_path)
            if self.db_session:
                self.db_session.add(rule)
                self.db_session.commit()
            return rule
        except Exception as e:
            logger.error(f"导入规则失败: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def import_rule_content(self, content: str) -> Rule:
        """
        从内容导入规则

        Args:
            content: 规则内容

        Returns:
            导入的规则对象
        """
        try:
            rule = import_rule_from_content(content)
            if self.db_session:
                self.db_session.add(rule)
                self.db_session.commit()
            return rule
        except Exception as e:
            logger.error(f"导入规则内容失败: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def export_rule(self, rule_id: str, format: str = "yaml") -> str:
        """
        导出规则

        Args:
            rule_id: 规则ID
            format: 导出格式，默认为yaml

        Returns:
            导出的规则内容
        """
        rule = self.get_rule(rule_id)
        if not rule:
            raise ValueError(f"规则不存在: {rule_id}")

        if format == "yaml":
            return export_rule_to_yaml(rule)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，如果不存在则返回None
        """
        if self.db_session:
            return self.db_session.query(Rule).filter(Rule.id == rule_id).first()
        return None

    def list_rules(self, rule_type: Optional[str] = None) -> List[Rule]:
        """
        列出规则

        Args:
            rule_type: 规则类型过滤器

        Returns:
            规则列表
        """
        if self.db_session:
            query = self.db_session.query(Rule)
            if rule_type:
                query = query.filter(Rule.type == rule_type)
            return query.all()
        return []

    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        if not self.db_session:
            return False

        try:
            rule = self.get_rule(rule_id)
            if rule:
                self.db_session.delete(rule)
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            self.db_session.rollback()
            raise

    def validate_rule(self, rule_content: Union[str, Dict]) -> bool:
        """
        验证规则

        Args:
            rule_content: 规则内容或字典

        Returns:
            是否验证通过
        """
        try:
            if isinstance(rule_content, str):
                self.rule_processor.process_rule_text(rule_content)
            else:
                self.rule_processor.validate_rule_dict(rule_content)
            return True
        except Exception as e:
            logger.error(f"规则验证失败: {e}")
            return False

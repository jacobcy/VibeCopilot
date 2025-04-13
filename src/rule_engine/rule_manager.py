"""
规则管理器模块

提供规则管理的核心功能，包括解析、验证、存储和导出
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.models.rule_model import Example, Rule, RuleItem, RuleMetadata
from src.rule_engine.core.rule_db_operations import RuleDBOperations
from src.rule_engine.core.rule_importer import export_rule_to_format, import_rule_from_content, import_rule_from_file

logger = logging.getLogger(__name__)


class RuleManager:
    """规则管理器，管理规则的全生命周期"""

    def __init__(self, session: Optional[Session] = None):
        """
        初始化规则管理器

        Args:
            session: 数据库会话，用于规则存储。如果为None，则自动创建新会话
        """
        self._db_available = True

        try:
            if session is None:
                # 如果没有提供会话，创建一个新的会话
                try:
                    session_factory = get_session_factory()
                    self.session = session_factory()
                    self._should_close_session = True
                except Exception as e:
                    logger.warning(f"无法创建数据库会话: {str(e)}，规则管理器将工作在非持久化模式")
                    self.session = None
                    self._should_close_session = False
                    self._db_available = False
            else:
                self.session = session
                self._should_close_session = False

            # 初始化数据库操作类
            self.db_ops = RuleDBOperations(self.session) if self._db_available else None

        except Exception as e:
            logger.warning(f"初始化规则管理器时出错: {str(e)}，将使用非持久化模式")
            self.session = None
            self.db_ops = None
            self._should_close_session = False
            self._db_available = False

    def __del__(self):
        """析构函数，确保会话被关闭"""
        if hasattr(self, "_should_close_session") and self._should_close_session and self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"关闭数据库会话时出错: {str(e)}")

    def import_rule_from_file(
        self, file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None, validate: bool = True, overwrite: bool = False
    ) -> Rule:
        """
        从文件导入规则

        Args:
            file_path: 规则文件路径
            parser_type: 解析器类型
            model: 模型名称
            validate: 是否验证规则
            overwrite: 是否覆盖已存在的规则

        Returns:
            解析后的规则数据（Pydantic模型）
        """
        # 使用导入模块导入规则
        rule = import_rule_from_file(file_path, parser_type, model, validate)

        # 如果数据库不可用，仅返回内存中的规则
        if not self._db_available or not self.db_ops:
            logger.info(f"数据库不可用，规则将仅在内存中使用: {rule.id}")
            return rule

        # 保存规则到数据库
        saved_rule = self.db_ops.save_rule(rule, overwrite)
        return saved_rule if saved_rule else rule

    def import_rule_from_content(
        self,
        content: str,
        context: str = "",
        parser_type: Optional[str] = None,
        model: Optional[str] = None,
        validate: bool = True,
        overwrite: bool = False,
    ) -> Rule:
        """
        从内容导入规则

        Args:
            content: 规则内容
            context: 上下文信息
            parser_type: 解析器类型
            model: 模型名称
            validate: 是否验证规则
            overwrite: 是否覆盖已存在的规则

        Returns:
            解析后的规则数据（Pydantic模型）
        """
        # 使用导入模块导入规则
        rule = import_rule_from_content(content, context, parser_type, model, validate)

        # 如果数据库不可用，仅返回内存中的规则
        if not self._db_available or not self.db_ops:
            logger.info(f"数据库不可用，规则将仅在内存中使用: {rule.id}")
            return rule

        # 保存规则到数据库
        saved_rule = self.db_ops.save_rule(rule, overwrite)
        return saved_rule if saved_rule else rule

    def export_rule(self, rule_id: str, format_type: str = "yaml", output_path: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        导出规则

        Args:
            rule_id: 规则ID
            format_type: 导出格式类型
            output_path: 输出路径

        Returns:
            根据format_type返回相应格式的规则数据
        """
        # 获取规则
        rule = self.get_rule(rule_id)
        if not rule:
            logger.warning(f"规则不存在: {rule_id}")
            return {"error": f"规则不存在: {rule_id}"}

        # 使用导出模块导出规则
        return export_rule_to_format(rule, format_type, output_path)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，如果不存在则返回None
        """
        if self._db_available and self.db_ops:
            # 从数据库获取规则
            return self.db_ops.get_rule(rule_id)
        else:
            logger.warning(f"数据库不可用，无法获取规则: {rule_id}")
            return None

    def list_rules(self, rule_type: Optional[str] = None) -> List[Rule]:
        """
        列出规则

        Args:
            rule_type: 规则类型过滤

        Returns:
            规则列表
        """
        if self._db_available and self.db_ops:
            # 从数据库列出规则
            return self.db_ops.list_rules(rule_type)
        else:
            logger.warning("数据库不可用，无法列出规则")
            return []

    def delete_rule(self, rule_id: str) -> bool:
        """
        删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        if self._db_available and self.db_ops:
            # 从数据库删除规则
            return self.db_ops.delete_rule(rule_id)
        else:
            logger.warning(f"数据库不可用，无法删除规则: {rule_id}")
            return False

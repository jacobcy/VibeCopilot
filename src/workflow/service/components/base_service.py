#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础服务组件

提供FlowService的核心初始化和公共功能。
"""

import logging
from typing import Any, Dict, Optional

from src.db import get_session_factory
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager
from src.workflow.workflow_operations import validate_workflow_files

logger = logging.getLogger(__name__)


class BaseService:
    """流程服务基类，提供数据库会话和核心管理器"""

    def __init__(self, verbose=False):
        """初始化基础服务

        Args:
            verbose: 是否显示详细日志
        """
        # 创建会话工厂
        self._session_factory = get_session_factory()
        # 创建数据库会话
        self.db_session = self._session_factory()

        # 设置详细模式
        self.verbose = verbose

        # 初始化会话管理器
        self.session_manager = FlowSessionManager(self.db_session)
        self.stage_manager = StageInstanceManager(self.db_session)

        # 启动时验证工作流文件一致性
        self._validate_on_startup()

    def _validate_on_startup(self):
        """启动时验证工作流文件一致性"""
        try:
            if self.verbose:
                logger.info("正在验证工作流文件一致性...")
            validation_result = validate_workflow_files(auto_fix=False)
            if validation_result["invalid"] > 0:
                if self.verbose:
                    logger.warning(f"发现 {validation_result['invalid']} 个不一致的工作流文件。" "请运行 'flow validate --fix' 命令修复这些问题。")
                    # 记录详细信息
                    for detail in validation_result["details"]:
                        if detail["status"] != "valid":
                            logger.warning(f"文件问题: {detail['file']} - {detail.get('issue', '未知问题')}")
            elif self.verbose:
                logger.info("所有工作流文件一致性验证通过")
        except Exception as e:
            logger.error(f"验证工作流文件一致性时出错: {str(e)}")

    def session_factory(self):
        """获取数据库会话工厂

        Returns:
            数据库会话工厂
        """
        return self._session_factory

    def validate_workflows(self, auto_fix: bool = False) -> Dict[str, Any]:
        """
        验证工作流文件一致性

        Args:
            auto_fix: 是否自动修复问题

        Returns:
            验证结果
        """
        return validate_workflow_files(auto_fix=auto_fix)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行服务组件

提供工作流执行功能，连接workflow和flow_session模块。
"""

import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExecutionService:
    """工作流执行服务类，负责工作流的执行和状态管理"""

    def __init__(self, session_manager, verbose=False):
        """初始化执行服务

        Args:
            session_manager: 会话管理器实例
            verbose: 是否显示详细日志
        """
        self.session_manager = session_manager
        self.verbose = verbose

    def execute_workflow(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None, task_id: Optional[str] = None, session_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行工作流

        这是一个重要的连接点，它将工作流执行职责委托给flow_session模块。
        不在workflow模块中实现执行逻辑，而是创建会话并启动它。

        Args:
            workflow_id: 工作流ID
            context: 可选的执行上下文数据
            task_id: 可选的特定任务ID
            session_name: 可选的会话名称

        Returns:
            执行结果字典
        """
        if self.verbose:
            logger.info(f"准备执行工作流: {workflow_id}")

        execution_id = str(uuid.uuid4())

        try:
            # 步骤1: 创建工作流会话
            session_params = {"execution_id": execution_id, "context": context or {}}

            if task_id:
                session_params["task_id"] = task_id

            # 创建会话
            session = self.session_manager.create_session(workflow_id, name=session_name or f"执行-{execution_id[:8]}", params=session_params)

            if not session:
                return {"execution_id": execution_id, "workflow_id": workflow_id, "status": "failed", "message": "无法创建会话"}

            # 步骤2: 启动会话执行
            result = self.session_manager.start_session(session.id)

            if not result:
                return {"execution_id": execution_id, "workflow_id": workflow_id, "session_id": session.id, "status": "failed", "message": "无法启动会话执行"}

            # 步骤3: 返回执行结果
            session_data = (
                session.to_dict()
                if hasattr(session, "to_dict")
                else {"id": session.id, "name": session.name, "status": getattr(session, "status", "unknown")}
            )

            return {"execution_id": execution_id, "workflow_id": workflow_id, "session_id": session.id, "status": "started", "session": session_data}

        except Exception as e:
            logger.error(f"执行工作流时出错: {str(e)}")
            return {"execution_id": execution_id, "workflow_id": workflow_id, "status": "error", "message": f"执行出错: {str(e)}"}

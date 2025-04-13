#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理命令行工具

提供创建、查看、管理工作流等功能，以及与n8n的同步操作。
工作流执行现在由flow_session模块处理。
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.core.log_init import get_workflow_logger
from src.workflow.execution.executor import WorkflowExecutor
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage
from src.workflow.models.workflow import Workflow
from src.workflow.operations import (  # execute_workflow, # 已移除，由flow_session处理
    create_workflow,
    delete_workflow,
    list_workflows,
    sync_n8n,
    update_workflow,
    view_workflow,
)
from src.workflow.service.flow_service import FlowService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="工作流管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list命令
    list_parser = subparsers.add_parser("list", help="列出所有工作流")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    list_parser.set_defaults(func=list_workflows)

    # view命令
    view_parser = subparsers.add_parser("view", help="查看工作流详情")
    view_parser.add_argument("id", help="工作流ID")
    view_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    view_parser.set_defaults(func=view_workflow)

    # create命令
    create_parser = subparsers.add_parser("create", help="创建工作流")
    create_parser.add_argument("name", help="工作流名称")
    create_parser.add_argument("-d", "--description", help="工作流描述")
    create_parser.add_argument("--active", action="store_true", help="设置为活跃状态")
    create_parser.add_argument("--n8n-id", help="关联的n8n工作流ID")
    create_parser.set_defaults(func=create_workflow)

    # update命令
    update_parser = subparsers.add_parser("update", help="更新工作流")
    update_parser.add_argument("id", help="工作流ID")
    update_parser.add_argument("-n", "--name", help="工作流名称")
    update_parser.add_argument("-d", "--description", help="工作流描述")
    update_parser.add_argument("-s", "--status", choices=["active", "inactive", "archived"], help="工作流状态")
    update_parser.add_argument("--n8n-id", help="关联的n8n工作流ID")
    update_parser.set_defaults(func=update_workflow)

    # delete命令
    delete_parser = subparsers.add_parser("delete", help="删除工作流")
    delete_parser.add_argument("id", help="工作流ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="强制删除，不确认")
    delete_parser.set_defaults(func=delete_workflow)

    # execute命令
    execute_parser = subparsers.add_parser("execute", help="执行工作流")
    execute_parser.add_argument("id", help="工作流ID")
    execute_parser.add_argument("-s", "--stage", help="指定要执行的阶段")
    execute_parser.add_argument("-c", "--context", help="执行上下文，JSON格式")
    execute_parser.set_defaults(func=execute_workflow_handler)

    # sync命令
    sync_parser = subparsers.add_parser("sync", help="同步n8n工作流")
    sync_parser.add_argument("-w", "--workflow-id", help="工作流ID")
    sync_parser.add_argument("-e", "--execution-id", help="执行ID")
    sync_parser.add_argument("-n", "--n8n-execution-id", help="n8n执行ID")
    sync_parser.add_argument("--import-workflows", action="store_true", help="导入n8n工作流")
    sync_parser.add_argument("--update-from-n8n", action="store_true", help="从n8n更新执行状态")
    sync_parser.add_argument("--sync-pending", action="store_true", help="同步所有待处理的执行")
    sync_parser.set_defaults(func=sync_n8n)

    # 解析命令行参数
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def execute_workflow_handler(args):
    """处理flow execute命令"""
    try:
        if not args.workflow_id and not args.session_id:
            return (StatusCode.ERROR, "请指定工作流ID或会话ID")

        # 创建服务
        verbose = args.verbose if hasattr(args, "verbose") else False
        flow_service = FlowService(verbose=verbose)

        # 如果指定了会话ID，则恢复会话
        if args.session_id:
            return flow_service.resume_workflow_execution(session_id=args.session_id, stage_id=args.stage_id, auto_advance=args.auto_advance)

        # 如果指定了工作流ID，则创建新会话
        if args.workflow_id:
            return flow_service.execute_workflow(
                workflow_id=args.workflow_id, session_name=args.session_name, stage_id=args.stage_id, auto_advance=args.auto_advance
            )

    except Exception as e:
        logger.error(f"执行工作流错误: {str(e)}")
        if hasattr(args, "verbose") and args.verbose:
            logger.exception(e)
        return (StatusCode.ERROR, f"执行工作流错误: {str(e)}")


class WorkflowManager:
    """工作流管理器类"""

    def __init__(self):
        """初始化工作流管理器"""
        self.flow_service = FlowService()
        self.logger = get_workflow_logger("manager")
        self._workflows: Dict[str, Workflow] = {}

    def create_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """
        创建新的工作流

        Args:
            workflow_data: 工作流配置数据

        Returns:
            str: 工作流ID
        """
        workflow_id = str(uuid4())
        self.logger.info(
            "创建新工作流", extra={"workflow_id": workflow_id, "workflow_type": workflow_data.get("type"), "workflow_name": workflow_data.get("name")}
        )

        try:
            workflow = Workflow(workflow_id, workflow_data)
            self._workflows[workflow_id] = workflow
            return workflow_id
        except Exception as e:
            self.logger.error("创建工作流失败", extra={"workflow_id": workflow_id, "error": str(e)})
            raise

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        获取工作流实例

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[Workflow]: 工作流实例或None
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            self.logger.warning("工作流不存在", extra={"workflow_id": workflow_id})
        return workflow

    def execute_workflow(self, workflow_id: str, session_name: Optional[str] = None, stage_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            workflow_id: 工作流ID
            session_name: 会话名称
            stage_id: 起始阶段ID

        Returns:
            Dict[str, Any]: 执行结果
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            self.logger.error("执行失败：工作流不存在", extra={"workflow_id": workflow_id})
            raise ValueError(f"Workflow {workflow_id} not found")

        self.logger.info("开始执行工作流", extra={"workflow_id": workflow_id, "session_name": session_name, "stage_id": stage_id})

        try:
            executor = WorkflowExecutor(workflow)
            result = executor.execute(session_name=session_name, start_stage=stage_id)

            self.logger.info(
                "工作流执行完成", extra={"workflow_id": workflow_id, "status": result.get("status"), "execution_time": result.get("execution_time")}
            )

            return result
        except Exception as e:
            self.logger.error("工作流执行失败", extra={"workflow_id": workflow_id, "error": str(e)})
            raise

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        列出所有工作流

        Returns:
            List[Dict[str, Any]]: 工作流列表
        """
        self.logger.debug(f"列出工作流，共{len(self._workflows)}个")
        return [{"id": wf_id, "name": wf.name, "type": wf.type, "status": wf.status} for wf_id, wf in self._workflows.items()]

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            bool: 是否删除成功
        """
        if workflow_id in self._workflows:
            self.logger.info("删除工作流", extra={"workflow_id": workflow_id})
            del self._workflows[workflow_id]
            return True
        else:
            self.logger.warning("删除失败：工作流不存在", extra={"workflow_id": workflow_id})
            return False


if __name__ == "__main__":
    main()

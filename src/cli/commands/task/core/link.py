"""
任务关联工作流命令模块
"""

import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.db.session_manager import session_scope
from src.services.task import TaskService

logger = logging.getLogger(__name__)
console = Console()


def is_agent_mode() -> bool:
    """检查是否处于 Agent 模式"""
    return False


@click.command(name="link", help="关联任务到工作流")
@click.argument("task_id", type=str, required=False)
@click.option("-f", "--flow", type=str, required=False, help="工作流ID或名称 (如不指定则使用默认工作流)")
def link_task(task_id: Optional[str] = None, flow: Optional[str] = None):
    """关联任务到工作流命令

    将任务关联到指定的工作流定义。如果不指定工作流，则使用默认工作流。

    示例:
        vibecopilot task link abc123 --flow wf_dev_process   # 关联任务到开发工作流
        vibecopilot task link --flow wf_test_process         # 使用当前任务关联到测试工作流
        vibecopilot task link abc123                         # 使用默认工作流
    """
    try:
        result = execute_link_flow_task(task_id, flow)

        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("workflow"):
                workflow_info = result["workflow"]
                console.print(f"工作流ID: {workflow_info.get('id')}")
                console.print(f"工作流名称: {workflow_info.get('name')}")
                console.print(f"工作流类型: {workflow_info.get('type')}")
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")

        return result
    except Exception as e:
        logger.error(f"执行关联任务到工作流命令时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return {"status": "error", "message": str(e)}


def execute_link_flow_task(task_id: Optional[str] = None, workflow_id: Optional[str] = None) -> Dict[str, Any]:
    """关联任务到工作流的核心逻辑"""
    results = {"status": "success", "message": "", "workflow": None}

    try:
        with session_scope() as session:
            task_service = TaskService()
            current_task_id = task_id

            if not current_task_id:
                current_task = task_service.get_current_task(session)
                if not current_task:
                    results["status"] = "error"
                    results["message"] = "没有指定任务ID且没有当前任务"
                    return results
                current_task_id = current_task["id"]
                logger.info(f"未指定task_id，使用当前任务: {current_task_id}")

            # 如果没有指定工作流ID，使用默认工作流
            if not workflow_id:
                logger.info("未指定工作流ID，将尝试使用默认工作流")
                try:
                    # 获取默认工作流 (假设是 wf_general 或 wf_dev_process)
                    from src.workflow.utils.workflow_search import get_workflow_fuzzy

                    default_workflows = ["wf_general", "wf_dev_process", "wf_basic"]

                    for wf_id in default_workflows:
                        default_workflow = get_workflow_fuzzy(wf_id)
                        if default_workflow:
                            workflow_id = wf_id
                            logger.info(f"使用默认工作流: {workflow_id}")
                            break

                    # 如果仍未找到默认工作流，查找任何可用的工作流
                    if not workflow_id:
                        from src.workflow.service import list_workflows

                        all_workflows = list_workflows()
                        if all_workflows:
                            workflow_id = all_workflows[0].get("id")
                            logger.info(f"未找到预定义默认工作流，使用首个可用工作流: {workflow_id}")
                        else:
                            results["status"] = "error"
                            results["message"] = "找不到任何可用的工作流，请指定工作流ID或添加工作流定义"
                            return results
                except Exception as e:
                    logger.error(f"获取默认工作流时出错: {e}")
                    results["status"] = "error"
                    results["message"] = f"必须指定工作流(--flow): {e}"
                    return results

            try:
                # 注意: 需要修改TaskService中的方法以支持直接关联到工作流，而不是会话
                workflow_info = task_service.link_to_workflow(session, current_task_id, workflow_id=workflow_id)
                if workflow_info:
                    results["message"] = f"任务 {current_task_id} 关联到工作流 {workflow_id} 成功"
                    results["workflow"] = workflow_info
                else:
                    results["status"] = "error"
                    results["message"] = "关联任务失败 (服务层返回失败)"
            except ValueError as e:
                logger.warning(f"关联任务时发生值错误: {e}")
                results["status"] = "error"
                results["message"] = str(e)
                raise e

    except Exception as e:
        logger.error(f"关联任务数据库操作期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["message"] = f"关联任务失败: {e}"

    return results

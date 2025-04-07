"""
工作流状态提供者模块

实现工作流的状态提供者接口。
"""

import logging
from typing import Any, Dict, List, Optional

from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class WorkflowStatusProvider(IStatusProvider):
    """工作流状态提供者"""

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "workflow"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取工作流状态

        Args:
            entity_id: 可选，实体ID。格式为 "workflow:<id>" 或 "execution:<id>"。
                       不提供则获取整个工作流系统的状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            # 导入工作流模块
            import argparse

            from src.workflow.workflow_operations import list_workflows, view_workflow

            # 创建参数解析器
            parser = argparse.ArgumentParser()
            parser.add_argument("-v", "--verbose", action="store_true")

            # 获取整个工作流系统状态
            if not entity_id:
                workflows = list_workflows(parser.parse_args([]))

                # 转换为字典
                workflow_data = workflows if isinstance(workflows, dict) else {}
                workflow_data["domain"] = self.domain
                return workflow_data

            # 解析实体ID
            if ":" in entity_id:
                entity_type, real_id = entity_id.split(":", 1)
            else:
                # 默认为工作流
                entity_type = "workflow"
                real_id = entity_id

            # 获取特定实体状态
            if entity_type == "workflow":
                args = parser.parse_args([])
                args.id = real_id
                workflow = view_workflow(args)

                # 转换为字典
                workflow_data = workflow if isinstance(workflow, dict) else {}
                workflow_data["domain"] = self.domain
                return workflow_data
            elif entity_type == "execution":
                # TODO: 实现执行状态查询
                return {"error": "执行状态查询尚未实现"}
            else:
                return {"error": f"未知实体类型: {entity_type}"}

        except Exception as e:
            logger.error(f"获取工作流状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新工作流实体状态

        Args:
            entity_id: 实体ID，格式为 "workflow:<id>" 或 "execution:<id>"
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 导入工作流模块
            import argparse

            from src.workflow.workflow_operations import update_workflow

            # 解析实体ID
            if ":" in entity_id:
                entity_type, real_id = entity_id.split(":", 1)
            else:
                # 默认为工作流
                entity_type = "workflow"
                real_id = entity_id

            # 更新状态
            if entity_type == "workflow":
                # 创建参数
                args = argparse.Namespace()
                args.id = real_id
                args.status = status
                args.name = kwargs.get("name")
                args.description = kwargs.get("description")
                args.n8n_id = kwargs.get("n8n_id")

                result = update_workflow(args)

                # 转换为字典
                result_dict = result if isinstance(result, dict) else {}
                if "success" in result_dict and result_dict["success"]:
                    return {**result_dict, "updated": True}
                else:
                    return {**result_dict, "updated": False}
            elif entity_type == "execution":
                # TODO: 实现执行状态更新
                return {"error": "执行状态更新尚未实现", "updated": False}
            else:
                return {"error": f"未知实体类型: {entity_type}", "updated": False}

        except Exception as e:
            logger.error(f"更新工作流状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工作流系统中的实体

        Args:
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        try:
            # 导入工作流模块
            import argparse

            from src.workflow.workflow_operations import list_workflows

            # 创建参数解析器
            parser = argparse.ArgumentParser()
            parser.add_argument("-v", "--verbose", action="store_true")

            # 获取所有工作流
            workflows_result = list_workflows(parser.parse_args([]))

            # 解析结果
            workflows = []
            if isinstance(workflows_result, dict) and "workflows" in workflows_result:
                workflows = workflows_result.get("workflows", [])

            # 筛选并格式化
            entities = []
            for workflow in workflows:
                if status and workflow.get("status") != status:
                    continue

                entities.append(
                    {
                        "id": f"workflow:{workflow.get('id')}",
                        "name": workflow.get("name", "未命名工作流"),
                        "type": "workflow",
                        "status": workflow.get("status"),
                        "description": workflow.get("description", ""),
                    }
                )

            return entities

        except Exception as e:
            logger.error(f"列出工作流实体时出错: {e}")
            return []

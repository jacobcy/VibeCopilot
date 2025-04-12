"""
路线图更新处理器模块

提供更新路线图元素状态的处理逻辑。
"""

from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


class RoadmapUpdateHandlers:
    """路线图更新处理器"""

    VALID_TYPES = ["milestone", "story", "task"]
    VALID_STATUSES = {
        "milestone": ["planned", "in_progress", "completed", "cancelled"],
        "story": ["planned", "in_progress", "completed", "blocked"],
        "task": ["todo", "in_progress", "review", "done", "blocked"],
    }

    @staticmethod
    def handle_update_command(args: Dict[str, Any], service) -> Dict[str, Any]:
        """处理更新命令

        Args:
            args: 命令参数
            service: 路线图服务实例

        Returns:
            Dict[str, Any]: 处理结果
        """
        # 验证参数
        validation_result = RoadmapUpdateHandlers.validate_args(args)
        if not validation_result.get("success"):
            return validation_result

        element_type = args["type"]
        element_id = args["id"]
        status = args["status"]

        # 准备更新参数
        update_params = {
            "status": status,
            "comment": args.get("comment", ""),
            "assignee": args.get("assignee"),
            "labels": args.get("labels", "").split(",") if args.get("labels") else None,
        }

        try:
            # 调用服务方法更新状态
            result = service.update_element_status(element_type=element_type, element_id=element_id, **update_params)

            if not result.get("success", False):
                return {"status": "error", "code": result.get("code", 1), "message": result.get("message", "更新失败"), "data": result.get("data")}

            # 如果需要同步到GitHub
            if args.get("sync", False):
                sync_result = service.sync_to_github(element_type=element_type, element_id=element_id)
                if not sync_result.get("success", False):
                    return {
                        "status": "warning",
                        "code": 0,
                        "message": "状态已更新，但GitHub同步失败",
                        "data": {"update": result.get("data"), "sync_error": sync_result.get("message")},
                    }

            return {
                "status": "success",
                "code": 0,
                "message": f"成功更新{element_type} {element_id}的状态为{status}",
                "data": {
                    "type": element_type,
                    "id": element_id,
                    "old_status": result.get("old_status"),
                    "new_status": status,
                    "params": update_params,
                    "sync_status": "synced" if args.get("sync") else "not_synced",
                },
            }

        except Exception as e:
            return {"status": "error", "code": 1, "message": f"更新过程出错: {str(e)}", "data": {"error": str(e)}}

    @staticmethod
    def validate_args(args: Dict[str, Any]) -> Dict[str, Any]:
        """验证命令参数

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 验证结果
        """
        # 验证必需参数
        required_params = ["type", "id", "status"]
        for param in required_params:
            if param not in args:
                return {"success": False, "status": "error", "message": f"缺少必需参数: {param}"}

        # 验证元素类型
        if args["type"] not in RoadmapUpdateHandlers.VALID_TYPES:
            return {"success": False, "status": "error", "message": f"无效的元素类型: {args['type']}。有效类型为: {', '.join(RoadmapUpdateHandlers.VALID_TYPES)}"}

        # 验证状态
        element_type = args["type"]
        status = args["status"]
        if status not in RoadmapUpdateHandlers.VALID_STATUSES[element_type]:
            return {
                "success": False,
                "status": "error",
                "message": f"无效的{element_type}状态: {status}。有效状态为: {', '.join(RoadmapUpdateHandlers.VALID_STATUSES[element_type])}",
            }

        return {"success": True}

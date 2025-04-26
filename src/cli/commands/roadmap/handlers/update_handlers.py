"""
路线图更新处理器模块

提供更新路线图元素状态的处理逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from rich.console import Console

from src.db.session_manager import session_scope

logger = logging.getLogger(__name__)

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

        # 准备要更新的数据字典
        update_data = {"status": status}
        if "comment" in args and args["comment"] is not None:
            pass
        if "assignee" in args and args["assignee"] is not None:
            update_data["assignee"] = args["assignee"]
        if "labels" in args and args["labels"] is not None:
            update_data["labels"] = args["labels"]

        logger.debug(f"Preparing to update {element_type} {element_id} with data: {update_data}")

        updated_entity = None
        update_success = False
        try:
            # 使用 session_scope 和 Repository 更新
            with session_scope() as session:
                repo = None
                if element_type == "milestone":
                    repo = getattr(service, "milestone_repo", None)
                elif element_type == "story":
                    repo = service.story_repo
                elif element_type == "task":
                    repo = service.task_repo

                if not repo:
                    raise AttributeError(f"RoadmapService does not have a repository for type '{element_type}'")

                # 调用 repository 的 update 方法
                updated_entity = repo.update(session, element_id, update_data)
                if updated_entity:
                    update_success = True
                    logger.info(f"Successfully updated {element_type} {element_id} in DB.")
                else:
                    logger.warning(f"Repository update for {element_type} {element_id} returned None.")
                    pass
            # ------------------------------------------

            if not update_success:
                # Attempt to get the entity to confirm if it exists but wasn't updated
                with session_scope() as session:
                    entity_exists = repo.get_by_id(session, element_id) is not None
                if not entity_exists:
                    return {"status": "error", "message": f"未找到要更新的 {element_type}: {element_id}"}
                else:
                    return {"status": "error", "message": f"更新 {element_type} {element_id} 失败，仓库未返回成功信号"}

            # 处理 GitHub 同步
            sync_success = True
            sync_error_msg = None
            if args.get("sync", False):
                logger.info(f"Initiating GitHub sync for {element_type} {element_id}")
                try:
                    from src.roadmap.service.roadmap_operations import sync_to_github

                    sync_result = sync_to_github(service, roadmap_id=None, element_type=element_type, element_id=element_id)
                    if not sync_result.get("success", False):
                        sync_success = False
                        sync_error_msg = sync_result.get("error", "未知同步错误")
                        logger.warning(f"GitHub sync failed for {element_type} {element_id}: {sync_error_msg}")
                    else:
                        logger.info(f"GitHub sync successful for {element_type} {element_id}")
                except Exception as sync_e:
                    sync_success = False
                    sync_error_msg = str(sync_e)
                    logger.error(f"GitHub sync process raised an exception for {element_type} {element_id}: {sync_e}", exc_info=True)
            # ------------------------

            # 构造返回结果
            entity_dict = service._object_to_dict(updated_entity) if updated_entity and hasattr(service, "_object_to_dict") else {"id": element_id}

            response_status = "success" if sync_success else "warning"
            message = f"成功更新 {element_type} {element_id} 的状态为 {status}"
            if not sync_success:
                message += "，但 GitHub 同步失败。"

            return {
                "status": response_status,
                "message": message,
                "data": {
                    "type": element_type,
                    "id": element_id,
                    "new_status": status,
                    "updated_data": update_data,
                    "sync_status": "SYNCED" if args.get("sync") and sync_success else ("SYNC_FAILED" if args.get("sync") else "NOT_SYNCED"),
                    "sync_error": sync_error_msg if not sync_success else None,
                },
            }

        except AttributeError as ae:
            logger.error(f"更新 {element_type} {element_id} 时出错: {ae}", exc_info=True)
            return {"status": "error", "message": f"服务配置错误: {str(ae)}"}
        except Exception as e:
            logger.error(f"更新 {element_type} {element_id} 时出错: {e}", exc_info=True)
            return {"status": "error", "message": f"更新过程出错: {str(e)}"}

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

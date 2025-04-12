"""
路线图状态提供者模块

实现路线图的状态提供者接口，适配 RoadmapStatus。
"""

import logging
from typing import Any, Dict, List, Optional

from src.roadmap.service.roadmap_service import RoadmapService
from src.roadmap.service.roadmap_status import RoadmapStatus
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class RoadmapStatusProvider(IStatusProvider):
    """路线图状态提供者"""

    def __init__(self, roadmap_service: RoadmapService):
        """初始化路线图状态提供者

        Args:
            roadmap_service: 路线图服务
        """
        self.roadmap_service = roadmap_service
        self.roadmap_status = RoadmapStatus(roadmap_service)

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "roadmap"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取路线图状态

        Args:
            entity_id: 可选的实体ID，格式为 'type:id' 或直接使用ID。
                      如果不提供，则返回整个路线图的状态。

        Returns:
            包含状态信息的字典
        """
        try:
            # 获取整个路线图状态
            if not entity_id:
                result = self.roadmap_service.check_roadmap_status(check_type="roadmap", element_id=None)
                if not result.get("success", False):
                    return {"error": result.get("error", "获取路线图状态失败")}

                status_data = result.get("status", {})
                status_data["domain"] = self.domain
                return status_data

            # 解析实体ID
            if ":" in entity_id:
                entity_type, real_id = entity_id.split(":", 1)
            else:
                # 尝试猜测类型
                if entity_id.startswith("M"):
                    entity_type = "milestone"
                elif entity_id.startswith("T"):
                    entity_type = "task"
                else:
                    return {
                        "error": f"无法识别实体类型: {entity_id}",
                        "code": "INVALID_ENTITY_TYPE",
                        "suggestions": ["使用格式 'milestone:M001' 或 'task:T001' 指定实体类型", "检查实体ID是否正确"],
                    }

                real_id = entity_id

            # 获取特定实体状态
            if entity_type == "milestone":
                result = self.roadmap_service.check_roadmap_status(check_type="milestone", element_id=real_id)
            elif entity_type == "task":
                result = self.roadmap_service.check_roadmap_status(check_type="task", element_id=real_id)
            else:
                return {
                    "error": f"未知实体类型: {entity_type}",
                    "code": "UNKNOWN_ENTITY_TYPE",
                    "suggestions": ["支持的实体类型: milestone, task"],
                }

            if not result.get("success", False):
                return {
                    "error": result.get("error", f"获取{entity_type}状态失败"),
                    "code": "STATUS_FETCH_FAILED",
                    "suggestions": [f"确认 {entity_type} '{real_id}' 是否存在", "检查路线图服务配置"],
                }

            status_data = result.get("status", {})
            status_data["domain"] = self.domain
            return status_data

        except RuntimeError as e:
            # 特殊处理Task模型错误
            if "Task类未正确定义为SQLAlchemy模型" in str(e):
                logger.error(f"路线图状态提供者数据库错误: {e}")
                return {
                    "error": "路线图数据库结构错误: Task模型未正确配置",
                    "code": "DB_MODEL_ERROR",
                    "health": 0,
                    "suggestions": [
                        "将 src/models/db/roadmap.py 中的 Task 类转换为 SQLAlchemy 模型",
                        "修改 TaskRepository 实现方式，使其支持非SQLAlchemy模型",
                        "临时使用静态数据作为 list_tasks 函数的返回值",
                    ],
                }
        except Exception as e:
            logger.error(f"获取路线图状态时出错: {e}")
            return {
                "error": str(e),
                "code": "UNKNOWN_ERROR",
                "health": 50,
                "suggestions": ["检查路线图服务日志获取详细错误信息", "运行 'vibecopilot db check' 验证数据库完整性"],
            }

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新路线图实体状态

        Args:
            entity_id: 实体ID，格式为 "milestone:<id>" 或 "task:<id>"
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 解析实体ID
            if ":" in entity_id:
                entity_type, real_id = entity_id.split(":", 1)
            else:
                # 尝试猜测类型
                if entity_id.startswith("M"):
                    entity_type = "milestone"
                elif entity_id.startswith("T"):
                    entity_type = "task"
                else:
                    return {"error": f"无法识别实体类型: {entity_id}", "updated": False}

                real_id = entity_id

            # 更新状态
            result = self.roadmap_status.update_element(element_id=real_id, element_type=entity_type, status=status)

            if "error" in result:
                return {**result, "updated": False}

            return {**result, "updated": True}

        except Exception as e:
            logger.error(f"更新路线图状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出路线图中的实体

        Args:
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        try:
            result = self.roadmap_service.check_roadmap_status(check_type="roadmap", element_id=None)
            if not result.get("success", False):
                logger.warning(f"获取路线图状态失败: {result.get('error', '未知错误')}")
                return []

            status_data = result.get("status", {})
            entities = []

            # 添加里程碑
            milestones = status_data.get("milestone_status", {})
            for milestone_id, milestone in milestones.items():
                if status and milestone.get("status") != status:
                    continue

                entities.append(
                    {
                        "id": f"milestone:{milestone_id}",
                        "name": milestone.get("name", "未命名里程碑"),
                        "type": "milestone",
                        "status": milestone.get("status"),
                        "progress": milestone.get("progress", 0),
                    }
                )

            try:
                # 尝试获取任务列表
                all_tasks = self.roadmap_service.get_tasks()

                # 添加任务
                for task in all_tasks:
                    if status and task.get("status") != status:
                        continue

                    entities.append(
                        {
                            "id": f"task:{task.get('id')}",
                            "title": task.get("title") or task.get("name", "未命名任务"),
                            "type": "task",
                            "status": task.get("status"),
                            "milestone": task.get("milestone"),
                        }
                    )
            except RuntimeError as e:
                # 特殊处理Task模型错误
                if "Task类未正确定义为SQLAlchemy模型" in str(e):
                    logger.error(f"获取任务列表时出错 (数据库模型问题): {e}")
                    # 添加一个错误标记实体
                    entities.append(
                        {
                            "id": "error:task_model",
                            "name": "路线图任务模型错误",
                            "type": "error",
                            "status": "error",
                            "error_code": "DB_MODEL_ERROR",
                            "description": "Task类未正确定义为SQLAlchemy模型",
                        }
                    )
            except Exception as e:
                logger.error(f"获取任务列表时出错: {e}")
                # 添加一个通用错误标记实体
                entities.append(
                    {
                        "id": "error:tasks",
                        "name": "任务列表获取失败",
                        "type": "error",
                        "status": "error",
                        "error_code": "TASK_FETCH_ERROR",
                        "description": str(e),
                    }
                )

            return entities

        except Exception as e:
            logger.error(f"列出路线图实体时出错: {e}")
            # 返回一个包含错误信息的实体列表而不是空列表
            return [
                {
                    "id": "error:global",
                    "name": "路线图实体获取失败",
                    "type": "error",
                    "status": "error",
                    "error_code": "ENTITY_LIST_ERROR",
                    "description": str(e),
                }
            ]

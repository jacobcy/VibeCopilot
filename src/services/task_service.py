"""
任务服务模块

提供任务相关的服务层接口，整合数据访问和业务逻辑。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from src.db.repositories.task_repository import TaskRepository
from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类，整合任务相关的业务逻辑

    提供任务的创建、查询、更新、删除等功能，封装底层数据访问操作，
    并实现任务相关的业务规则和校验逻辑。
    """

    def __init__(self, db_service: Optional[DatabaseService] = None):
        """初始化任务服务

        Args:
            db_service: 数据库服务实例，如果为None则创建新实例
        """
        self._db_service = db_service or DatabaseService()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果找不到则返回None
        """
        try:
            return self._db_service.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务 {task_id} 失败: {e}")
            return None

    def list_tasks(
        self,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取任务列表，支持多种过滤条件

        Args:
            status: 按状态过滤
            assignee: 按负责人过滤
            labels: 按标签过滤
            story_id: 按关联的Story ID过滤
            is_independent: 是否只返回独立任务
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            任务列表
        """
        try:
            # 注意：实际实现需要根据DatabaseService的能力来调整
            # 这里简化处理，假设DatabaseService有类似的方法
            tasks = self._db_service.list_tasks()

            # 简单的筛选逻辑，实际中可能需要更复杂的实现或直接由数据库层处理
            filtered_tasks = []
            for task in tasks:
                # 状态过滤
                if status and task.get("status") not in status:
                    continue

                # 负责人过滤
                if assignee and task.get("assignee") != assignee:
                    continue

                # 标签过滤
                if labels:
                    task_labels = task.get("labels", [])
                    if not any(label in task_labels for label in labels):
                        continue

                # 关联Story过滤
                if story_id and task.get("story_id") != story_id:
                    continue

                # 独立任务过滤
                if is_independent is not None:
                    is_task_independent = not task.get("story_id")
                    if is_independent != is_task_independent:
                        continue

                filtered_tasks.append(task)

            # 分页处理
            if offset:
                filtered_tasks = filtered_tasks[offset:]
            if limit:
                filtered_tasks = filtered_tasks[:limit]

            return filtered_tasks

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建新任务

        Args:
            task_data: 任务数据字典，包含标题、描述等信息

        Returns:
            创建的任务信息，失败返回None
        """
        try:
            # 数据验证
            if not task_data.get("title"):
                raise ValueError("任务标题不能为空")

            # 业务规则处理
            if "status" not in task_data:
                task_data["status"] = "open"  # 设置默认状态

            # 自动生成任务ID (如果没有提供)，使用更短的UUID
            if "id" not in task_data:
                task_data["id"] = f"task_{uuid.uuid4().hex[:8]}"
                logger.info(f"为任务自动生成ID: {task_data['id']}")

            # 确保字段名称正确，防止错误的字段名导致创建失败
            # 将roadmap_item_id重命名为story_id (如果存在)
            if "roadmap_item_id" in task_data:
                story_id = task_data.pop("roadmap_item_id")
                if story_id:  # 只有在不为空时才添加
                    task_data["story_id"] = story_id

            # 将workflow_stage_instance_id重命名为flow_session_id (如果存在)
            if "workflow_stage_instance_id" in task_data:
                flow_id = task_data.pop("workflow_stage_instance_id")
                if flow_id:  # 只有在不为空时才添加
                    task_data["flow_session_id"] = flow_id

            return self._db_service.create_task(task_data)
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新任务信息

        Args:
            task_id: 任务ID
            task_data: 更新的任务数据

        Returns:
            更新后的任务信息，失败返回None
        """
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            # 业务规则校验
            if "status" in task_data and task_data["status"] not in ["open", "in_progress", "done", "cancelled"]:
                raise ValueError(f"无效的任务状态: {task_data['status']}")

            # 确保字段名称正确
            # 将roadmap_item_id重命名为story_id (如果存在)
            if "roadmap_item_id" in task_data:
                story_id = task_data.pop("roadmap_item_id")
                if story_id is not None:  # 允许设置为空值来取消关联
                    task_data["story_id"] = story_id

            # 将workflow_stage_instance_id重命名为flow_session_id (如果存在)
            if "workflow_stage_instance_id" in task_data:
                flow_id = task_data.pop("workflow_stage_instance_id")
                if flow_id is not None:  # 允许设置为空值来取消关联
                    task_data["flow_session_id"] = flow_id

            return self._db_service.update_task(task_id, task_data)
        except Exception as e:
            logger.error(f"更新任务 {task_id} 失败: {e}")
            return None

    def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            return self._db_service.delete_task(task_id)
        except Exception as e:
            logger.error(f"删除任务 {task_id} 失败: {e}")
            return False

    def add_task_comment(self, task_id: str, comment: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """添加任务评论

        Args:
            task_id: 任务ID
            comment: 评论内容
            author: 评论作者

        Returns:
            添加的评论信息，失败返回None
        """
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            # 假设有一个添加评论的方法
            # 注意：这里简化处理，实际实现可能需要调用特定的评论仓库或方法
            comment_data = {"id": f"comment_{uuid.uuid4().hex[:8]}", "task_id": task_id, "content": comment, "author": author or "系统"}

            # 这里需要根据实际的数据库服务接口调整
            # 假设有一个create_task_comment方法
            result = self._db_service.create_entity("task_comment", comment_data)
            return result
        except Exception as e:
            logger.error(f"为任务 {task_id} 添加评论失败: {e}")
            return None

    def link_task(self, task_id: str, link_type: str, target_id: str) -> bool:
        """关联任务到其他实体

        Args:
            task_id: 任务ID
            link_type: 关联类型，如'story', 'flow', 'github'等
            target_id: 目标实体ID

        Returns:
            是否关联成功
        """
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            # 根据关联类型确定更新字段
            update_data = {}

            if link_type == "story":
                update_data["story_id"] = target_id
            elif link_type == "flow":
                update_data["flow_session_id"] = target_id
            elif link_type == "github":
                update_data["github_issue_number"] = target_id
            else:
                raise ValueError(f"不支持的关联类型: {link_type}")

            # 执行更新
            result = self.update_task(task_id, update_data)
            return result is not None
        except Exception as e:
            logger.error(f"关联任务 {task_id} 到 {link_type}:{target_id} 失败: {e}")
            return False

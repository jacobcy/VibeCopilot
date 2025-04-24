"""
任务服务核心模块

提供TaskService类的主要实现，包括初始化和基本操作。
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from sqlalchemy.orm import Session

from src.core.config import get_config
from src.db.service import DatabaseService
from src.memory import get_memory_service  # 导入MemoryService获取函数
from src.models.db.task import Task
from src.services.task.comment import TaskCommentService
from src.services.task.query import TaskQueryService
from src.services.task.session import TaskSessionService
from src.utils.file_utils import ensure_directory_exists, get_relative_path

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类，整合任务相关的业务逻辑

    提供任务的创建、查询、更新、删除等功能，封装底层数据访问操作，
    并实现任务相关的业务规则和校验逻辑。
    """

    def __init__(self):
        self._db_service = DatabaseService()
        # 获取状态服务实例
        from src.status.service import StatusService

        self._status_service = StatusService.get_instance()

        # 获取MemoryService实例
        self._memory_service = get_memory_service()

        # 初始化子服务
        self._comment_service = TaskCommentService(self._db_service)
        self._query_service = TaskQueryService(self._db_service)
        self._session_service = TaskSessionService(self._db_service, self._status_service)

        # 获取配置
        self._config = get_config()
        self._project_root = self._config.get("paths.project_root", str(Path.cwd()))
        self._agent_work_dir = self._config.get("paths.agent_work_dir", ".ai")

    def get_current_task(self, session: Session) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        return self._query_service.get_current_task()

    def set_current_task(self, session: Session, task_id: str) -> bool:
        """设置当前任务

        设置指定任务为当前任务，同时如果任务有关联的会话，将该会话设置为当前会话。
        """
        return self._session_service.set_current_task(task_id)

    def create_task(
        self, session: Session, task_data: Union[str, Dict[str, Any]], story_id: Optional[str] = None, github_issue: Optional[Dict[str, Any]] = None
    ) -> Task:
        """创建任务

        Args:
            session: 数据库会话
            task_data: 任务数据，可以是标题字符串或包含完整任务信息的字典
            story_id: 关联的故事ID
            github_issue: GitHub Issue 信息

        Returns:
            Task: 创建的任务
        """
        try:
            # 如果 task_data 是字符串，将其作为标题
            if isinstance(task_data, str):
                data = {"title": task_data}
            else:
                data = task_data.copy()  # 创建副本以避免修改原始数据

            # 添加 story_id（如果提供）
            if story_id:
                data["story_id"] = story_id

            # 添加 GitHub Issue 信息（如果提供）
            if github_issue:
                data["github_issue_number"] = github_issue.get("number")

            # 确保必要的字段存在
            if "title" not in data:
                raise ValueError("任务必须包含标题")

            # 创建任务
            task_orm = self._db_service.task_repo.create_task(session, **data)

            # 设置为当前任务
            try:
                # 从状态服务获取TaskStatusProvider
                task_provider = self._status_service.provider_manager.get_provider("task")
                if task_provider and hasattr(task_provider, "set_current_task"):
                    task_provider.set_current_task(task_orm.id)
                    logger.info(f"已将任务 {task_orm.id} 设置为当前任务")
            except Exception as e:
                logger.warning(f"设置当前任务失败: {e}")

            # 记录任务创建
            logger.info(f"创建任务成功: {task_orm.id}")

            return task_orm

        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise

    def update_task(self, session: Session, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新任务信息

        Args:
            session: 数据库会话
            task_id: 任务ID
            data: 要更新的字段和值的字典，可包含以下字段:
                - title: 任务标题
                - description: 任务描述
                - status: 任务状态
                - priority: 任务优先级
                - assignee: 任务负责人
                - labels: 任务标签列表
                - due_date: 截止日期
                - memory_link: 关联的知识库文档链接
                - story_id: 关联的故事ID
                - github_issue_number: 关联的GitHub Issue编号
                - github_repo: 关联的GitHub仓库

        Returns:
            更新后的任务信息字典，失败时返回None

        Raises:
            ValueError: 提供了无效的字段或值
        """
        try:
            # 验证status字段的值
            if "status" in data and data["status"] not in ["todo", "in_progress", "done", "blocked", "review", "backlog"]:
                valid_statuses = ", ".join(["todo", "in_progress", "done", "blocked", "review", "backlog"])
                raise ValueError(f"无效的任务状态值: {data['status']}。有效值为: {valid_statuses}")

            # 执行任务更新
            task_orm = self._db_service.task_repo.update_task(session, task_id, data)

            if task_orm:
                # 转换为字典格式并返回
                return task_orm.to_dict() if hasattr(task_orm, "to_dict") else self._convert_task_to_dict(task_orm)
            else:
                logger.error(f"更新任务失败: 任务 {task_id} 不存在或更新操作失败")
                return None

        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            raise

    def _convert_task_to_dict(self, task) -> Dict[str, Any]:
        """将任务对象转换为字典

        用于处理没有to_dict方法的Task对象
        """
        result = {}
        for key in dir(task):
            if not key.startswith("_") and not callable(getattr(task, key)):
                result[key] = getattr(task, key)
        return result

    def get_task(self, session: Session, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        return self._query_service.get_task(session, task_id)

    def get_task_by_identifier(self, session: Session, identifier: str) -> Optional[Dict[str, Any]]:
        """通过ID或名称查找任务

        先按ID精确查找，如果找不到，则按名称（不区分大小写）查找。

        Args:
            session: 数据库会话
            identifier: 任务ID或任务名称

        Returns:
            任务信息字典，如果找不到则返回None
        """
        return self._query_service.get_task_by_identifier(session, identifier)

    def delete_task(self, session: Session, task_id: str) -> bool:
        """删除任务"""
        return self._query_service.delete_task(session, task_id)

    def link_task(self, session: Session, task_id: str, link_type: str, target_id: str) -> bool:
        """关联任务到其他实体"""
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(session, task_id)
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
            result = self.update_task(session, task_id, update_data)
            return result is not None
        except Exception as e:
            logger.error(f"关联任务 {task_id} 到 {link_type}:{target_id} 失败: {e}")
            return False

    # 任务评论相关方法代理
    def add_task_comment(self, session: Session, task_id: str, comment: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """添加任务评论"""
        return self._comment_service.add_task_comment(session, task_id, comment, author)

    # 任务会话相关方法代理
    def link_to_flow_session(self, session: Session, task_id: str, flow_type: str = None, session_id: str = None) -> Optional[Dict[str, Any]]:
        """关联任务到工作流会话"""
        return self._session_service.link_to_flow_session(session, task_id, flow_type, session_id)

    def create_task_with_flow(self, session: Session, task_data: Dict[str, Any], workflow_id: str) -> Optional[Dict[str, Any]]:
        """创建任务并自动关联工作流会话"""
        return self._session_service.create_task_with_flow(session, self, task_data, workflow_id)

    def get_task_sessions(self, session: Session, task_id: str):
        """获取任务关联的所有工作流会话"""
        return self._session_service.get_task_sessions(session, task_id)

    def get_current_task_session(self, session: Session):
        """获取当前任务的当前工作流会话"""
        return self._session_service.get_current_task_session(session)

    def set_current_task_session(self, session: Session, session_id: str) -> bool:
        """设置当前任务的当前工作流会话"""
        return self._session_service.set_current_task_session(session, session_id)

    def get_task_comments(self, session: Session, task_id: str) -> List[Dict[str, Any]]:
        """获取任务评论列表"""
        return self._comment_service.get_task_comments(session, task_id)

    def search_tasks(
        self,
        session: Session,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        roadmap_item_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
        is_temporary: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """搜索和过滤任务

        Args:
            session: 数据库会话 (注意: 此参数当前未传递给下一层)
            status: 状态列表
            assignee: 负责人
            labels: 标签列表
            roadmap_item_id: 关联的故事ID
            is_independent: 是否为独立任务
            is_temporary: 是否为临时任务
            limit: 限制数量
            offset: 偏移量

        Returns:
            符合条件的任务列表
        """
        # 移除作为位置参数传递的 session，所有参数都通过关键字传递
        return self._query_service.search_tasks(
            status=status,
            assignee=assignee,
            labels=labels,
            roadmap_item_id=roadmap_item_id,
            is_independent=is_independent,
            is_temporary=is_temporary,
            limit=limit,
            offset=offset,
        )

    def get_task_log_path(self, task_id: str) -> tuple[str, str]:
        """获取任务日志路径

        Args:
            task_id: 任务ID

        Returns:
            元组，包含 (日志文件路径, 日志目录路径)
        """
        # 构建日志路径
        log_dir = os.path.join(self._project_root, self._agent_work_dir, "tasks", task_id)
        log_path = os.path.join(log_dir, "task.log")

        return log_path, log_dir

    def read_task_log(self, task_id: str, last_n: Optional[int] = None) -> Optional[str]:
        """读取任务日志内容

        Args:
            task_id: 任务ID
            last_n: 读取最后几行，None表示读取全部

        Returns:
            日志内容字符串，如果失败则返回None
        """
        try:
            # 获取日志路径
            log_path, _ = self.get_task_log_path(task_id)

            # 检查日志文件是否存在
            if not os.path.exists(log_path):
                logger.warning(f"任务日志文件不存在: {log_path}")
                return None

            # 读取日志内容
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if last_n is not None and last_n > 0:
                    return "".join(lines[-last_n:])
                return "".join(lines)

        except Exception as e:
            logger.error(f"读取任务日志失败: {e}")
            return None

    def append_to_task_log(self, task_id: str, content: str) -> bool:
        """追加内容到任务日志

        Args:
            task_id: 任务ID
            content: 要追加的内容

        Returns:
            是否追加成功
        """
        try:
            # 获取日志路径
            log_path, log_dir = self.get_task_log_path(task_id)

            # 确保日志目录存在
            ensure_directory_exists(log_dir)

            # 追加内容到日志文件
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{content}\n")

            return True

        except Exception as e:
            logger.error(f"追加任务日志失败: {e}")
            return False

    def log_task_activity(self, session: Session, task_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """记录任务活动

        将任务活动信息记录到任务日志文件中，格式为Markdown

        Args:
            session: 数据库会话
            task_id: 任务ID
            action: 活动名称/类型
            details: 活动详情，可选

        Returns:
            是否记录成功
        """
        try:
            # 获取当前时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 构造日志内容
            log_content = f"### {action} ({now})\n\n"

            # 如果有详情，添加到日志内容
            if details:
                details_content = "\n".join([f"- **{k}**: {v}" for k, v in details.items() if v is not None])
                if details_content:
                    log_content += f"{details_content}\n\n"

            # 追加到任务日志
            return self.append_to_task_log(task_id, log_content)

        except Exception as e:
            logger.error(f"记录任务活动失败: {e}")
            return False

    def get_task_metadata(self, session: Session, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务元数据

        Args:
            session: 数据库会话
            task_id: 任务ID

        Returns:
            元数据字典，如果失败则返回None
        """
        try:
            # 获取任务目录
            _, task_dir = self.get_task_log_path(task_id)
            metadata_path = os.path.join(task_dir, "metadata.json")

            # 检查元数据文件是否存在
            if not os.path.exists(metadata_path):
                logger.warning(f"任务元数据文件不存在: {metadata_path}")
                return None

            # 读取元数据
            import json

            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"获取任务元数据失败: {e}")
            return None

"""
数据库命令主模块

整合所有数据库命令处理器，提供统一命令接口
"""

from typing import Any, Dict

from .base import BaseDatabaseCommand
from .create_handler import CreateHandler
from .delete_handler import DeleteHandler
from .init_handler import InitHandler
from .query_handler import QueryHandler
from .update_handler import UpdateHandler


class DatabaseCommand(BaseDatabaseCommand):
    """数据库命令处理器"""

    def __init__(self):
        """初始化数据库命令"""
        super().__init__()

        # 注册参数
        self.register_args(
            required=["action"],
            optional={
                "type": None,  # 操作的实体类型(epic/story/task/label/template)
                "id": None,  # 实体ID
                "data": None,  # JSON格式的数据
                "format": "text",  # 输出格式(text/json)
                "query": None,  # 查询字符串
                "tags": None,  # 标签列表，逗号分隔
            },
        )

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库命令

        Args:
            args: 命令参数
                - action: 要执行的操作(init/query/create/update/delete)
                - type: 实体类型(可选)
                - id: 实体ID(可选)
                - data: JSON格式的数据(可选)
                - format: 输出格式(可选)
                - query: 查询字符串(可选)
                - tags: 标签列表，逗号分隔(可选)

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 初始化服务
        self._init_services()

        # 获取操作类型
        action = args["action"]

        # 根据操作类型执行不同逻辑
        if action == "init":
            return InitHandler.handle(self, args)
        elif action == "query":
            return QueryHandler.handle(self, args)
        elif action == "create":
            return CreateHandler.handle(self, args)
        elif action == "update":
            return UpdateHandler.handle(self, args)
        elif action == "delete":
            return DeleteHandler.handle(self, args)
        else:
            return {"success": False, "error": f"未知操作: {action}"}

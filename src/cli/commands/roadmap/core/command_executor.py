"""
路线图命令执行模块

提供执行路线图命令的具体逻辑。
"""

import logging
import os
from typing import Any, Dict, Optional

from rich.console import Console

from src.cli.commands.roadmap.handlers.detail_handlers import RoadmapDetailHandlers
from src.cli.commands.roadmap.handlers.edit_handlers import RoadmapEditHandlers
from src.cli.commands.roadmap.handlers.list_handlers import RoadmapListHandlers
from src.cli.commands.roadmap.handlers.show_handler import handle_show_roadmap
from src.cli.commands.roadmap.handlers.status_handler import handle_roadmap_status
from src.cli.commands.roadmap.handlers.sync_handlers import RoadmapSyncHandlers
from src.db.service import DatabaseService
from src.roadmap import RoadmapService

logger = logging.getLogger(__name__)
console = Console()


class RoadmapCommandExecutor:
    """路线图命令执行器"""

    def __init__(self, service: Optional[RoadmapService] = None, db_service: Optional[DatabaseService] = None, db_path: Optional[str] = None):
        """
        初始化路线图命令执行器

        Args:
            service: 路线图服务
            db_service: 数据库服务
            db_path: 数据库路径
        """
        self.service = service or RoadmapService()

        # 设置数据库服务
        if db_service:
            self.db_service = db_service
        else:
            # 创建一个新的数据库服务实例
            self.db_service = DatabaseService()

        # 存储数据库路径供后续使用（某些处理器可能需要它）
        self.db_path = db_path
        if not self.db_path:
            db_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "roadmap.db")

        # 初始化处理器
        self.list_handlers = RoadmapListHandlers(self.service, self.db_service)
        self.detail_handlers = RoadmapDetailHandlers(self.service, self.db_service)
        self.edit_handlers = RoadmapEditHandlers(self.service, self.db_service)
        self.sync_handlers = RoadmapSyncHandlers(self.service, self.db_service)

    def execute_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行路线图命令

        Args:
            args: 命令参数字典

        Returns:
            执行结果
        """
        # 获取操作类型
        roadmap_action = args.get("roadmap_action")

        # 根据操作类型执行相应命令
        if roadmap_action == "list":
            return self._list_roadmaps(args)
        elif roadmap_action == "show":
            return self._show_roadmap(args)
        elif roadmap_action == "create":
            return self._create_roadmap(args)
        elif roadmap_action == "update":
            return self._update_roadmap(args)
        elif roadmap_action == "delete":
            return self._delete_roadmap(args)
        elif roadmap_action == "sync":
            return self._sync_roadmap(args)
        elif roadmap_action == "switch":
            return self._switch_roadmap(args)
        elif roadmap_action == "status":
            return self._roadmap_status(args)
        else:
            logger.error(f"未知的路线图操作: {roadmap_action}")
            return {"success": False, "error": f"未知的路线图操作: {roadmap_action}"}

    def _list_roadmaps(self, args: Dict) -> Dict[str, Any]:
        """执行list命令"""
        verbose = args.get("verbose", False)
        agent_mode = args.get("agent_mode", False)

        # 获取路线图列表
        roadmaps = self.list_handlers.get_roadmaps()

        if not roadmaps:
            return {"success": True, "message": "没有找到任何路线图。"}

        # 根据不同模式输出
        if agent_mode:
            return {"success": True, "data": roadmaps, "count": len(roadmaps)}
        else:
            # 格式化输出结果
            return {"success": True, "message": f"共找到 {len(roadmaps)} 个路线图：", "data": roadmaps}

    def _show_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行show命令"""
        roadmap_id = args.get("id")
        format_type = args.get("format", "text")

        if not roadmap_id:
            return {"success": False, "error": "未提供路线图ID"}

        return handle_show_roadmap(self.service, self.db_service, roadmap_id, format_type)

    def _create_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行create命令"""
        name = args.get("name")
        description = args.get("description", "")

        if not name:
            return {"success": False, "error": "未提供路线图名称"}

        return self.edit_handlers.create_roadmap(name, description)

    def _update_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行update命令"""
        roadmap_id = args.get("id")
        name = args.get("name")
        description = args.get("description")

        if not roadmap_id:
            return {"success": False, "error": "未提供路线图ID"}

        if not name and not description:
            return {"success": False, "error": "未提供任何要更新的内容"}

        # 创建更新数据字典
        update_data = {}
        if name:
            update_data["name"] = name
        if description:
            update_data["description"] = description

        return self.edit_handlers.update_roadmap(roadmap_id, update_data)

    def _delete_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行delete命令"""
        roadmap_id = args.get("id")
        force = args.get("force", False)

        if not roadmap_id:
            return {"success": False, "error": "未提供路线图ID"}

        return self.edit_handlers.delete_roadmap(roadmap_id, force)

    def _sync_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行sync命令"""
        source = args.get("source", "github")
        verbose = args.get("verbose", False)

        # 创建正确的参数字典
        sync_args = {"source": source, "verbose": verbose}

        # 调用处理器，传递正确的参数
        return self.sync_handlers.sync_roadmap(self.service, sync_args)

    def _switch_roadmap(self, args: Dict) -> Dict[str, Any]:
        """执行switch命令"""
        roadmap_id = args.get("id")

        if not roadmap_id:
            return {"success": False, "error": "未提供路线图ID"}

        return self.edit_handlers.switch_roadmap(roadmap_id)

    def _roadmap_status(self, args: Dict) -> Dict[str, Any]:
        """执行status命令"""
        roadmap_id = args.get("id")

        if not roadmap_id:
            # 如果未提供ID，尝试获取当前活动的路线图
            try:
                active_roadmap = self.service.get_active_roadmap()
                if active_roadmap:
                    roadmap_id = active_roadmap.id
                else:
                    return {"success": False, "error": "没有活动的路线图，请提供路线图ID"}
            except Exception as e:
                logger.error(f"获取活动路线图失败: {str(e)}")
                return {"success": False, "error": "获取活动路线图失败，请提供路线图ID"}

        return handle_roadmap_status(self.service, self.db_service, roadmap_id)

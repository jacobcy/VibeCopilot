"""
数据库删除处理模块

处理数据库删除相关命令
"""

import logging
from typing import Dict

from rich.console import Console

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class DeleteHandler(BaseDatabaseCommand):
    """数据库删除处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理删除命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        force = args.get("force", False)
        verbose = args.get("verbose", False)

        if verbose:
            self.console.print(f"删除 {entity_type} (ID: {entity_id})")

        try:
            # 检查实体是否存在
            entity = self._get_entity(entity_type, entity_id)
            if not entity:
                self.console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            # 确认删除
            if not force:
                self.console.print(f"[yellow]警告: 即将删除 {entity_type} (ID: {entity_id})[/yellow]")
                self.console.print("添加 --force 参数确认此操作")
                return 1

            # 删除实体
            success = self._delete_entity(entity_type, entity_id)
            if not success:
                self.console.print(f"[red]删除 {entity_type} (ID: {entity_id}) 失败[/red]")
                return 1

            # 输出结果
            self.console.print(f"[green]成功删除 {entity_type} (ID: {entity_id})[/green]")
            return 0

        except Exception as e:
            logger.error(f"删除 {entity_type} (ID: {entity_id}) 失败: {e}")
            self.console.print(f"[red]删除 {entity_type} (ID: {entity_id}) 失败: {e}[/red]")
            return 1

    def _get_entity(self, entity_type: str, entity_id: str) -> Dict:
        """获取实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        # 使用数据库服务查询
        if self.db_service:
            try:
                return self.db_service.get_entity(entity_type, entity_id)
            except Exception as e:
                logger.error(f"查询数据库失败: {e}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

    def _delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """删除实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        # 使用数据库服务删除
        if self.db_service:
            try:
                return self.db_service.delete_entity(entity_type, entity_id)
            except Exception as e:
                logger.error(f"删除实体失败: {e}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

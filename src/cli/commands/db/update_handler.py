"""
数据库更新处理模块

处理数据库更新相关命令
"""

import json
import logging
from datetime import datetime
from typing import Dict

from rich.console import Console
from rich.table import Table

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class UpdateHandler(BaseDatabaseCommand):
    """数据库更新处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理更新命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        data_str = args.get("data")
        verbose = args.get("verbose", False)

        if verbose:
            self.console.print(f"更新 {entity_type} (ID: {entity_id})")

        try:
            # 检查实体是否存在
            entity = self._get_entity(entity_type, entity_id)
            if not entity:
                self.console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            # 解析JSON数据
            data = json.loads(data_str)

            # 验证数据
            if not isinstance(data, dict):
                self.console.print("[red]数据必须是JSON对象[/red]")
                return 1

            # 禁止修改ID
            if "id" in data and data["id"] != entity_id:
                self.console.print("[red]不允许修改实体ID[/red]")
                return 1

            # 更新时间戳
            data["updated_at"] = datetime.now().isoformat()

            # 更新实体
            updated_entity = self._update_entity(entity_type, entity_id, data)
            if not updated_entity:
                self.console.print(f"[red]更新 {entity_type} (ID: {entity_id}) 失败[/red]")
                return 1

            # 输出结果
            self.console.print(f"[green]成功更新 {entity_type} (ID: {entity_id})[/green]")

            # 显示更新后的实体中被修改的字段
            table = Table(show_header=False, box=None)
            table.add_column("字段", style="cyan")
            table.add_column("值")

            for key, value in updated_entity.items():
                if key in data:  # 只显示被更新的字段
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, ensure_ascii=False)
                    table.add_row(key, str(value))

            self.console.print(table)
            return 0

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            self.console.print(f"[red]JSON解析失败: {e}[/red]")
            return 1
        except Exception as e:
            logger.error(f"更新 {entity_type} (ID: {entity_id}) 失败: {e}")
            self.console.print(f"[red]更新 {entity_type} (ID: {entity_id}) 失败: {e}[/red]")
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

    def _update_entity(self, entity_type: str, entity_id: str, data: Dict) -> Dict:
        """更新实体

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        # 使用数据库服务更新
        if self.db_service:
            try:
                return self.db_service.update_entity(entity_type, entity_id, data)
            except Exception as e:
                logger.error(f"更新实体失败: {e}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

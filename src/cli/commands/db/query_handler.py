"""
数据库查询处理模块

处理数据库查询相关命令
"""

import json
import logging
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class QueryHandler(BaseDatabaseCommand):
    """数据库查询处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理查询命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        query = args.get("query")
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        if verbose:
            if entity_id:
                self.console.print(f"查询 {entity_type} (ID: {entity_id})")
            elif query:
                self.console.print(f"搜索 {entity_type}，查询: {query}")
            else:
                self.console.print(f"查询所有 {entity_type}")

        try:
            # 单个实体查询
            if entity_id:
                return self._handle_single_query(entity_type, entity_id, output_format)

            # 带条件的查询
            if query:
                return self._handle_search_query(entity_type, query, output_format)

            # 列表查询
            return self._handle_list_query(entity_type, output_format)

        except Exception as e:
            logger.error(f"查询 {entity_type} 失败: {e}")
            self.console.print(f"[red]查询 {entity_type} 失败: {e}[/red]")
            return 1

    def _handle_single_query(self, entity_type: str, entity_id: str, output_format: str) -> int:
        """处理单个实体查询

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            output_format: 输出格式

        Returns:
            执行结果代码
        """
        entity = self._get_entity(entity_type, entity_id)

        if not entity:
            self.console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
            return 1

        if output_format == "json":
            # JSON输出
            print(json.dumps(entity, indent=2, ensure_ascii=False))
        else:
            # 表格输出
            self.console.print(f"[bold]{entity_type} (ID: {entity_id})[/bold]")

            table = Table(show_header=False, box=None)
            table.add_column("字段", style="cyan")
            table.add_column("值")

            for key, value in entity.items():
                if key != "id":  # ID已在标题显示
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, ensure_ascii=False)
                    table.add_row(key, str(value))

            self.console.print(table)

        return 0

    def _handle_search_query(self, entity_type: str, query: str, output_format: str) -> int:
        """处理搜索查询

        Args:
            entity_type: 实体类型
            query: 查询字符串
            output_format: 输出格式

        Returns:
            执行结果代码
        """
        entities = self._search_entities(entity_type, query)

        return self._format_and_display_entities(entities, entity_type, output_format)

    def _handle_list_query(self, entity_type: str, output_format: str) -> int:
        """处理列表查询

        Args:
            entity_type: 实体类型
            output_format: 输出格式

        Returns:
            执行结果代码
        """
        entities = self._get_entities(entity_type)

        return self._format_and_display_entities(entities, entity_type, output_format)

    def _format_and_display_entities(
        self, entities: List[Dict], entity_type: str, output_format: str
    ) -> int:
        """格式化并显示实体列表

        Args:
            entities: 实体列表
            entity_type: 实体类型
            output_format: 输出格式

        Returns:
            执行结果代码
        """
        if output_format == "json":
            # JSON输出
            print(json.dumps(entities, indent=2, ensure_ascii=False))
        else:
            # 表格输出
            if not entities:
                self.console.print(f"[yellow]未找到 {entity_type} 类型的条目[/yellow]")
                return 0

            table = Table(title=f"{entity_type} 列表")

            # 添加表头
            columns = entities[0].keys() if entities else []
            for column in columns:
                table.add_column(column, style="cyan")

            # 添加数据行
            for entity in entities:
                row = [str(entity.get(col, "")) for col in columns]
                table.add_row(*row)

            self.console.print(table)

        return 0

    def _get_entity(self, entity_type: str, entity_id: str) -> Dict:
        """获取单个实体

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

    def _get_entities(self, entity_type: str) -> List[Dict]:
        """获取实体列表

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        # 使用数据库服务查询
        if self.db_service:
            try:
                return self.db_service.get_entities(entity_type)
            except Exception as e:
                logger.error(f"查询数据库失败: {e}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

    def _search_entities(self, entity_type: str, query: str) -> List[Dict]:
        """搜索实体

        Args:
            entity_type: 实体类型
            query: 查询字符串

        Returns:
            实体列表
        """
        # 使用数据库服务查询
        if self.db_service:
            try:
                return self.db_service.search_entities(entity_type, query)
            except Exception as e:
                logger.error(f"查询数据库失败: {e}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

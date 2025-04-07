"""
数据库创建处理模块

处理数据库创建相关命令
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict

from rich.console import Console
from rich.panel import Panel

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class CreateHandler(BaseDatabaseCommand):
    """数据库创建处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理创建命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        data_str = args.get("data")
        verbose = args.get("verbose", False)

        if verbose:
            self.console.print(f"创建 {entity_type} 实体")

        try:
            # 解析JSON数据
            data = json.loads(data_str)
            logger.info(f"解析后的JSON数据: {data}")

            # 验证数据
            if not isinstance(data, dict):
                self.console.print("[red]数据必须是JSON对象[/red]")
                return 1

            if "title" not in data and entity_type not in ["label"]:
                self.console.print("[red]数据必须包含title字段[/red]")
                return 1

            # 生成ID（如果未提供）
            if "id" not in data:
                # 生成ID逻辑，根据实体类型使用不同前缀
                prefix = entity_type[0].upper()
                unique_id = str(uuid.uuid4())[:6]
                data["id"] = f"{prefix}{unique_id}"
                logger.info(f"自动生成ID: {data['id']}")

            # 添加创建时间戳
            if "created_at" not in data:
                data["created_at"] = datetime.now().isoformat()
            if "updated_at" not in data:
                data["updated_at"] = data["created_at"]

            logger.info(f"最终数据: {data}")

            # 直接尝试添加基本必需字段的最简单版本
            if entity_type == "task":
                # 确保数据中包含任务创建必需的字段
                simple_task_data = {
                    "id": data["id"],
                    "title": data["title"],
                    "description": data.get("description", ""),
                    "status": data.get("status", "todo"),
                    "priority": data.get("priority", "P2"),
                }
                logger.info(f"简化的任务数据: {simple_task_data}")
                data = simple_task_data

            # 添加实体到数据库
            logger.info(f"准备调用_create_entity方法，entity_type={entity_type}, data={data}")
            entity = self._create_entity(entity_type, data)

            # 输出结果
            title = data.get("title", data.get("name", data.get("id", "")))
            self.console.print(
                Panel(f"[green]成功创建 {entity_type}[/green]\nID: {entity['id']}\n标题: {title}")
            )
            return 0

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            self.console.print(f"[red]JSON解析失败: {e}[/red]")
            return 1
        except Exception as e:
            logger.error(f"创建 {entity_type} 失败: {e}")
            self.console.print(f"[red]创建 {entity_type} 失败: {e}[/red]")
            return 1

    def _create_entity(self, entity_type: str, data: Dict) -> Dict:
        """创建实体

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        # 使用数据库服务创建
        logger.info(f"_create_entity: entity_type={entity_type}, data={data}")

        if self.db_service:
            try:
                logger.info("调用self.db_service.create_entity")
                entity = self.db_service.create_entity(entity_type, data)
                logger.info(f"创建实体成功: {entity}")
                return entity
            except Exception as e:
                logger.error(f"创建实体过程出现异常: {e}")
                import traceback

                logger.error(f"异常堆栈: {traceback.format_exc()}")
                raise
        else:
            logger.error("数据库服务未初始化")
            raise RuntimeError("数据库服务未初始化")

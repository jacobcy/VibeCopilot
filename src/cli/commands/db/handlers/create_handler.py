"""
数据库创建处理模块

处理数据库创建相关命令
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel

from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository

# +++ 导入 Repositories 和 session_scope +++
from src.db.session_manager import session_scope

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

# 移除旧的 pass_service 导入
# from src.cli.core.decorators import pass_service


# 假设 LabelRepository 和 TemplateRepository 存在于适当的位置 (如果需要)
# from src.db.repositories.label_repository import LabelRepository
# from src.db.repositories.template_repository import TemplateRepository


logger = logging.getLogger(__name__)
console = Console()


class CreateHandler(ClickBaseHandler):
    """创建实体处理器"""

    VALID_TYPES = {"epic", "story", "task", "roadmap", "milestone"}  # 更新支持的类型
    # VALID_TYPES = {"epic", "story", "task", "label", "template"} # 旧代码

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证创建命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        data = kwargs.get("data")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        # 使用更新后的 VALID_TYPES
        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}. 支持的类型: {', '.join(self.VALID_TYPES)}")

        if not data:
            raise ValidationError("实体数据不能为空")

        try:
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data

            if not isinstance(data_dict, dict):
                raise ValidationError("数据必须是JSON对象")

            # 简单的 title 检查，可以根据类型细化
            if "title" not in data_dict and "name" not in data_dict:
                # 允许没有 title/name 的类型，例如 label? 如果有这种类型需要调整
                pass  # 假设所有类型都需要 title 或 name
                # raise ValidationError("数据必须包含 title 或 name 字段")

        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON解析失败: {str(e)}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理创建命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        data = kwargs.get("data")
        verbose = kwargs.get("verbose", False)
        # --- 移除 service 参数的使用 ---
        # service = kwargs.get("service")

        if verbose:
            console.print(f"创建 {entity_type} 实体")

        # --- 移除旧的 service 检查 ---
        # if not service:
        #     raise DatabaseError("数据库服务未初始化")

        try:
            # 验证参数 (在 handle 内部或外部调用皆可，这里放在内部)
            self.validate(entity_type=entity_type, data=data)

            # 解析JSON数据
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data.copy()  # 使用副本避免修改原始输入

            logger.info(f"解析后的JSON数据: {data_dict}")

            # 验证并丰富数据 (根据需要调整)
            enriched_data = self._enrich_data(entity_type, data_dict)
            logger.info(f"最终数据: {enriched_data}")

            # +++ 选择 Repository +++
            repo_map = {
                "epic": EpicRepository(),
                "story": StoryRepository(),
                "task": TaskRepository(),
                "roadmap": RoadmapRepository(),
                "milestone": MilestoneRepository(),
                # "label": LabelRepository(),
                # "template": TemplateRepository(),
            }
            if entity_type not in repo_map:
                raise DatabaseError(f"不支持的实体类型或未映射 Repository: {entity_type}")

            selected_repo = repo_map[entity_type]

            # +++ 使用 session_scope 和 Repository 创建实体 +++
            created_entity = None
            with session_scope() as session:
                logger.debug(f"使用 Repository '{selected_repo.__class__.__name__}' 创建实体")
                # 调用 Repository 的 create 方法
                created_entity_orm = selected_repo.create(session=session, **enriched_data)
                # 需要一种方式将 ORM 对象转回字典以便记录和显示
                if hasattr(created_entity_orm, "to_dict"):
                    created_entity = created_entity_orm.to_dict()
                else:
                    # 简单的回退，仅获取 ID
                    created_entity = {"id": getattr(created_entity_orm, "id", None)}
                    logger.warning(f"实体类型 '{entity_type}' 的 ORM 对象没有 to_dict 方法，仅返回 ID")

                # session_scope 会自动 commit 或 rollback

            if created_entity and created_entity.get("id"):
                logger.info(f"创建实体成功: {created_entity}")
                # 输出结果
                # 尝试获取 title 或 name，否则用 ID
                display_title = enriched_data.get("title", enriched_data.get("name", created_entity["id"]))
                console.print(Panel(f"[green]成功创建 {entity_type}[/green]\nID: {created_entity['id']}\n标题/名称: {display_title}"))
                return 0
            else:
                raise DatabaseError(f"创建 {entity_type} 失败，数据库操作未返回有效实体或ID")

        except (ValidationError, DatabaseError, NotImplementedError) as e:
            # 处理预期的错误
            logger.error(f"处理创建命令时出错: {e}")
            self.error_handler(e)
            return 1
        except json.JSONDecodeError as e:
            # 处理 JSON 错误
            logger.error(f"JSON 解析错误: {e}")
            self.error_handler(ValidationError(f"提供的 JSON 数据无效: {e}"))
            return 1
        except Exception as e:
            # 处理其他意外错误
            logger.error(f"处理创建命令时发生意外错误: {e}", exc_info=True)
            self.error_handler(e)
            return 1

    def _enrich_data(self, entity_type: str, data: Dict) -> Dict:
        """
        验证并丰富实体数据

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            Dict: 丰富后的数据

        Raises:
            ValidationError: 验证失败时抛出
        """
        # 生成ID（如果未提供）
        if "id" not in data:
            prefix_map = {"roadmap": "R", "epic": "E", "story": "S", "task": "T", "milestone": "M"}
            prefix = prefix_map.get(entity_type, entity_type[0].upper())  # 使用映射或首字母大写
            unique_id = str(uuid.uuid4())[:8]  # 增加长度避免碰撞
            data["id"] = f"{prefix}-{unique_id}"
            logger.info(f"自动生成ID: {data['id']}")

        # 添加时间戳
        current_time_iso = datetime.now().isoformat()
        data.setdefault("created_at", current_time_iso)
        data.setdefault("updated_at", current_time_iso)

        # 根据类型设置默认值或进行转换
        if entity_type == "task":
            data.setdefault("status", "todo")
            data.setdefault("priority", "medium")  # 使用枚举值？Repo层会处理
            data.setdefault("description", "")
            data.setdefault("labels", [])
            data.setdefault("memory_references", [])
            data.setdefault("linked_prs", [])
            data.setdefault("linked_commits", [])
        elif entity_type == "story":
            data.setdefault("status", "todo")
            data.setdefault("description", "")
            data.setdefault("points", 0)
            # ... 其他默认值 ...
        elif entity_type == "epic":
            data.setdefault("status", "todo")
            data.setdefault("description", "")
            # ... 其他默认值 ...
        elif entity_type == "milestone":
            data.setdefault("status", "open")
            data.setdefault("description", "")
            # ... 其他默认值 ...
        elif entity_type == "roadmap":
            data.setdefault("version", "1.0")
            data.setdefault("description", "")
            # ... 其他默认值 ...

        # 可以在这里添加更严格的字段验证，确保只包含模型允许的字段

        return data

    def error_handler(self, error: Exception) -> None:
        """
        处理创建命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)

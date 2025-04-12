"""
通用异常模块

包含项目中使用的基础异常类。
"""

from src.core.exceptions import VibeCopilotError


class EntityNotFoundError(VibeCopilotError):
    """实体找不到异常"""

    def __init__(self, message: str, entity_type: str = None, entity_id: str = None, code: str = "E803"):
        """初始化实体找不到异常

        Args:
            message: 错误消息
            entity_type: 实体类型（可选）
            entity_id: 实体ID（可选）
            code: 错误代码（默认E803）
        """
        if entity_type and entity_id:
            detail_message = f"{message} - {entity_type} with id {entity_id} not found"
        elif entity_type:
            detail_message = f"{message} - {entity_type} not found"
        else:
            detail_message = message

        super().__init__(detail_message, code)
        self.entity_type = entity_type
        self.entity_id = entity_id

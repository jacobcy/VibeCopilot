"""
ID生成器工具模块

提供统一的实体ID生成功能，确保ID格式一致且符合规范。
"""

import uuid
from enum import Enum
from typing import Optional


class EntityType(Enum):
    """实体类型枚举"""

    WORKFLOW = "wf"
    SESSION = "ss"
    STAGE = "st"
    STAGE_INSTANCE = "si"
    TASK = "tk"
    TRANSITION = "tr"
    USER = "ur"
    PROJECT = "pj"
    RULE = "rl"
    GENERIC = "id"  # 通用类型


class IdGenerator:
    """ID生成器"""

    @staticmethod
    def generate_id(entity_type: EntityType, prefix: Optional[str] = None) -> str:
        """生成唯一ID

        Args:
            entity_type: 实体类型
            prefix: 可选前缀，如项目代码等

        Returns:
            格式化的唯一ID
        """
        # 生成随机UUID部分(8个字符)
        random_part = uuid.uuid4().hex[:8]

        # 构建ID格式: {实体类型缩写}_{随机部分}
        # 如果提供了前缀，则为: {前缀}_{实体类型缩写}_{随机部分}
        if prefix:
            return f"{prefix}_{entity_type.value}_{random_part}"
        else:
            return f"{entity_type.value}_{random_part}"

    @staticmethod
    def generate_workflow_id(prefix: Optional[str] = None) -> str:
        """生成工作流定义ID"""
        return IdGenerator.generate_id(EntityType.WORKFLOW, prefix)

    @staticmethod
    def generate_session_id(prefix: Optional[str] = None) -> str:
        """生成工作流会话ID"""
        return IdGenerator.generate_id(EntityType.SESSION, prefix)

    @staticmethod
    def generate_stage_id(prefix: Optional[str] = None) -> str:
        """生成阶段ID"""
        return IdGenerator.generate_id(EntityType.STAGE, prefix)

    @staticmethod
    def generate_stage_instance_id(prefix: Optional[str] = None) -> str:
        """生成阶段实例ID"""
        return IdGenerator.generate_id(EntityType.STAGE_INSTANCE, prefix)

    @staticmethod
    def generate_task_id(prefix: Optional[str] = None) -> str:
        """生成任务ID"""
        return IdGenerator.generate_id(EntityType.TASK, prefix)

    @staticmethod
    def generate_transition_id(prefix: Optional[str] = None) -> str:
        """生成转换ID"""
        return IdGenerator.generate_id(EntityType.TRANSITION, prefix)

    @staticmethod
    def get_entity_type_from_id(entity_id: str) -> Optional[EntityType]:
        """从ID中获取实体类型

        Args:
            entity_id: 实体ID字符串

        Returns:
            实体类型枚举或None
        """
        if not entity_id or "_" not in entity_id:
            return None

        parts = entity_id.split("_")
        if len(parts) < 2:
            return None

        # 获取类型代码(第一部分或第二部分，取决于是否有前缀)
        type_code = parts[0]
        if len(parts) > 2:
            # 可能有前缀，检查第二部分
            type_code = parts[1]

        # 尝试查找匹配的枚举
        for entity_type in EntityType:
            if entity_type.value == type_code:
                return entity_type

        return None

    @staticmethod
    def is_valid_id(entity_id: str) -> bool:
        """验证ID是否有效

        Args:
            entity_id: 实体ID字符串

        Returns:
            ID是否有效
        """
        if not entity_id or "_" not in entity_id:
            return False

        parts = entity_id.split("_")
        if len(parts) < 2:
            return False

        # 验证最后部分是否为有效的8位hex字符串
        last_part = parts[-1]
        if len(last_part) != 8:
            return False

        try:
            int(last_part, 16)  # 尝试将其解析为16进制
            return True
        except ValueError:
            return False

"""
自定义异常模块
"""


class VibeCopilotError(Exception):
    """VibeCopilot基础异常类"""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "E000"
        super().__init__(self.message)


class CommandError(VibeCopilotError):
    """命令相关异常"""

    def __init__(self, message: str, code: str = "E100"):
        super().__init__(message, code)


class RuleError(VibeCopilotError):
    """规则相关异常"""

    def __init__(self, message: str, code: str = "E200"):
        super().__init__(message, code)


class ValidationError(VibeCopilotError):
    """验证相关异常"""

    def __init__(self, message: str, code: str = "E300"):
        super().__init__(message, code)


class ConfigError(VibeCopilotError):
    """配置相关异常"""

    def __init__(self, message: str, code: str = "E400"):
        super().__init__(message, code)


class ParseError(VibeCopilotError):
    """解析相关异常"""

    def __init__(self, message: str, code: str = "E500"):
        super().__init__(message, code)


class APIError(VibeCopilotError):
    """API调用相关异常"""

    def __init__(self, message: str, code: str = "E600"):
        super().__init__(message, code)


class WorkflowError(VibeCopilotError):
    """工作流相关异常"""

    def __init__(self, message: str, code: str = "E700"):
        super().__init__(message, code)


class DatabaseError(VibeCopilotError):
    """数据库相关异常"""

    def __init__(self, message: str, code: str = "E800"):
        super().__init__(message, code)


class EntityNotFoundError(DatabaseError):
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


class TemplateError(VibeCopilotError):
    """模板相关异常"""

    def __init__(self, message: str, code: str = "E900"):
        super().__init__(message, code)


# 错误码定义
ERROR_CODES = {
    # 通用错误 (E0xx)
    "E000": "未知错误",
    "E001": "操作失败",
    # 命令错误 (E1xx)
    "E100": "命令执行失败",
    "E101": "无效的命令格式",
    "E102": "命令不存在",
    "E103": "缺少必要参数",
    # 规则错误 (E2xx)
    "E200": "规则处理失败",
    "E201": "规则加载失败",
    "E202": "规则验证失败",
    "E203": "规则不存在",
    # 验证错误 (E3xx)
    "E300": "验证失败",
    "E301": "参数验证失败",
    "E302": "权限验证失败",
    # 配置错误 (E4xx)
    "E400": "配置错误",
    "E401": "配置加载失败",
    "E402": "配置验证失败",
    # 解析错误 (E5xx)
    "E500": "解析失败",
    "E501": "格式解析失败",
    "E502": "内容解析失败",
    # API错误 (E6xx)
    "E600": "API调用失败",
    "E601": "API连接失败",
    "E602": "API响应无效",
    # 工作流错误 (E7xx)
    "E700": "工作流执行失败",
    "E701": "工作流状态无效",
    "E702": "工作流转换失败",
    # 数据库错误 (E8xx)
    "E800": "数据库操作失败",
    "E801": "数据库连接失败",
    "E802": "数据查询失败",
    "E803": "实体找不到",
    # 模板错误 (E9xx)
    "E900": "模板处理失败",
    "E901": "模板渲染失败",
    "E902": "模板不存在",
}

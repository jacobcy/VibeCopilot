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
}

"""
模板系统异常类定义
"""


class TemplateError(Exception):
    """模板系统基础异常类"""

    pass


class TemplateNotFoundError(TemplateError):
    """模板未找到异常"""

    pass


class TemplateLoadError(TemplateError):
    """模板加载异常"""

    pass


class TemplateExportError(TemplateError):
    """模板导出异常"""

    pass


class TemplateValidationError(TemplateError):
    """模板验证异常"""

    pass

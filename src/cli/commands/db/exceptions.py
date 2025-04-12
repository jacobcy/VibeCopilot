"""
自定义异常类模块
"""


class DBCommandError(Exception):
    """DB命令基础异常类"""

    pass


class InitializationError(DBCommandError):
    """初始化错误"""

    pass


class ValidationError(DBCommandError):
    """验证错误"""

    pass


class DatabaseError(DBCommandError):
    """数据库操作错误"""

    pass


class QueryError(DBCommandError):
    """查询错误"""

    pass


class BackupError(DBCommandError):
    """备份错误"""

    pass


class RestoreError(DBCommandError):
    """恢复错误"""

    pass


class ConfigError(DBCommandError):
    """配置错误"""

    pass


class ServiceError(DBCommandError):
    """服务调用错误"""

    pass


class PermissionError(DBCommandError):
    """权限错误"""

    pass

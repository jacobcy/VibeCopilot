"""数据库操作相关异常类定义"""


class DBError(Exception):
    """数据库操作基础异常类"""

    pass


class InitializationError(DBError):
    """数据库初始化异常"""

    pass


class ConnectionError(DBError):
    """数据库连接异常"""

    pass


class QueryError(DBError):
    """数据库查询异常"""

    pass


class MigrationError(DBError):
    """数据库迁移异常"""

    pass

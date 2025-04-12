"""
工作流会话相关异常定义
"""


class SessionError(Exception):
    """会话基础异常类"""

    pass


class SessionNotFoundError(SessionError):
    """会话未找到异常"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionAlreadyExistsError(SessionError):
    """会话已存在异常"""

    def __init__(self, session_name: str):
        self.session_name = session_name
        super().__init__(f"Session already exists: {session_name}")


class SessionAlreadyClosedError(SessionError):
    """会话已关闭异常"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session is already closed: {session_id}")


class SessionStillActiveError(SessionError):
    """尝试删除活动会话异常"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Cannot delete active session: {session_id}. Close it first or use force delete.")

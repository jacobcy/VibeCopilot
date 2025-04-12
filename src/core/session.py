"""
会话管理核心类。
提供会话的创建、管理和状态追踪功能。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SessionStatus(Enum):
    """会话状态枚举"""

    CREATED = "created"  # 已创建
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    STOPPED = "stopped"  # 已停止


@dataclass
class Session:
    """会话类，用于追踪工作流执行状态"""

    session_id: str
    workflow_id: str
    status: SessionStatus = SessionStatus.CREATED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def start(self) -> None:
        """启动会话"""
        if self.status not in [SessionStatus.CREATED, SessionStatus.PAUSED]:
            raise ValueError(f"Cannot start session in {self.status.value} status")
        self.status = SessionStatus.RUNNING
        if not self.start_time:
            self.start_time = datetime.now()

    def stop(self) -> None:
        """停止会话"""
        if self.status == SessionStatus.STOPPED:
            return
        self.status = SessionStatus.STOPPED
        self.end_time = datetime.now()

    def pause(self) -> None:
        """暂停会话"""
        if self.status != SessionStatus.RUNNING:
            raise ValueError(f"Cannot pause session in {self.status.value} status")
        self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        """恢复会话"""
        if self.status != SessionStatus.PAUSED:
            raise ValueError(f"Cannot resume session in {self.status.value} status")
        self.status = SessionStatus.RUNNING

    def complete(self) -> None:
        """完成会话"""
        if self.status != SessionStatus.RUNNING:
            raise ValueError(f"Cannot complete session in {self.status.value} status")
        self.status = SessionStatus.COMPLETED
        self.end_time = datetime.now()

    def fail(self, error_message: str) -> None:
        """标记会话失败"""
        self.status = SessionStatus.FAILED
        self.error_message = error_message
        self.end_time = datetime.now()

    def update_step(self, step_name: str) -> None:
        """更新当前步骤"""
        self.current_step = step_name

    def add_metadata(self, key: str, value: any) -> None:
        """添加元数据"""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> any:
        """获取元数据"""
        return self.metadata.get(key)


class SessionManager:
    """会话管理器，管理所有活动会话"""

    _sessions: Dict[str, Session] = {}

    @classmethod
    def create_session(cls, session_id: str, workflow_id: str) -> Session:
        """创建新会话"""
        if session_id in cls._sessions:
            raise ValueError(f"Session {session_id} already exists")
        session = Session(session_id=session_id, workflow_id=workflow_id)
        cls._sessions[session_id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Session]:
        """获取会话"""
        return cls._sessions.get(session_id)

    @classmethod
    def list_sessions(cls) -> List[Session]:
        """列出所有会话"""
        return list(cls._sessions.values())

    @classmethod
    def remove_session(cls, session_id: str) -> None:
        """移除会话"""
        if session_id in cls._sessions:
            del cls._sessions[session_id]

    @classmethod
    def clear_sessions(cls) -> None:
        """清除所有会话"""
        cls._sessions.clear()

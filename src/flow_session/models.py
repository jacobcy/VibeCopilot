"""
工作流会话模型定义
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class FlowSession(BaseModel):
    """工作流会话模型"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    template: Optional[str] = None
    status: str = "active"  # active, closed
    created_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

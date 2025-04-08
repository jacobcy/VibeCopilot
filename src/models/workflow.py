#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模型

定义工作流相关的数据模型
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class WorkflowStep(BaseModel):
    """工作流步骤模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    name: str
    description: Optional[str] = None
    # 各类型步骤特有的属性通过额外字段支持
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class Workflow(BaseModel):
    """工作流模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    steps: List[WorkflowStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return self.dict(
            exclude_none=True,
            by_alias=True,
        )

    @validator("updated_at", always=True)
    def set_updated_at(cls, v, values):
        """更新时间默认为当前时间"""
        return datetime.now()


class WorkflowExecution(BaseModel):
    """工作流执行记录模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_name: str
    status: str = "pending"  # pending, running, completed, error
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps_results: List[Dict[str, Any]] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return self.dict(
            exclude_none=True,
            by_alias=True,
        )

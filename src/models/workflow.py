#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模型 (重定向模块)

此模块已被弃用，仅为保持兼容性而保留。
请直接使用src/models/db中的数据库模型。
"""

import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# 发出弃用警告
warnings.warn("src.models.workflow模块已弃用，请使用src.models.db中的数据库模型替代", DeprecationWarning, stacklevel=2)

# 从数据库模型重新导出，保持兼容性
from src.models.db import Workflow as DBWorkflow
from src.models.db import WorkflowStep as DBWorkflowStep


# 定义兼容性模型
class WorkflowStep(BaseModel):
    """
    工作流步骤模型 (兼容性保留)

    警告: 此类已被弃用，请使用src.models.db.WorkflowStep替代
    """

    id: str = Field(default="")
    type: str = Field(default="")
    name: str = Field(default="")
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class Workflow(BaseModel):
    """
    工作流模型 (兼容性保留)

    警告: 此类已被弃用，请使用src.models.db.Workflow替代
    """

    id: str = Field(default="")
    name: str = Field(default="")
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
        """将模型转换为字典"""
        warnings.warn("使用已弃用的Workflow.to_dict()方法，请切换到数据库模型", DeprecationWarning, stacklevel=2)
        return self.dict(exclude_none=True, by_alias=True)

    @validator("updated_at", always=True)
    def set_updated_at(cls, v, values):
        """更新时间默认为当前时间"""
        return datetime.now()


class WorkflowExecution(BaseModel):
    """
    工作流执行记录模型 (兼容性保留)

    警告: 此类已被弃用，请使用src.models.db.WorkflowExecution替代
    """

    id: str = Field(default="")
    workflow_id: str = Field(default="")
    workflow_name: str = Field(default="")
    status: str = "pending"
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
        """将模型转换为字典"""
        warnings.warn("使用已弃用的WorkflowExecution.to_dict()方法，请切换到数据库模型", DeprecationWarning, stacklevel=2)
        return self.dict(exclude_none=True, by_alias=True)

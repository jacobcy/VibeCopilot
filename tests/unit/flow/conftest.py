#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow模块测试fixtures
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from src.flow_session.session.manager import FlowSessionManager


@pytest.fixture
def mock_db_session():
    """提供模拟的数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def flow_session_manager(mock_db_session):
    """提供配置好的FlowSessionManager实例"""
    return FlowSessionManager(mock_db_session)


@pytest.fixture
def mock_workflow_definition():
    """提供模拟的工作流定义数据"""
    return {
        "id": "test-flow",
        "name": "Test Flow",
        "type": "test",
        "description": "Test workflow for unit tests",
        "stages": [
            {"id": "stage1", "name": "Stage 1", "description": "First stage", "checklist": ["Task 1", "Task 2"], "deliverables": ["Deliverable 1"]},
            {"id": "stage2", "name": "Stage 2", "description": "Second stage", "checklist": ["Task 3", "Task 4"], "deliverables": ["Deliverable 2"]},
        ],
    }


@pytest.fixture
def mock_flow_session():
    """提供模拟的工作流会话数据"""
    return {
        "id": "test-session",
        "workflow_id": "test-flow",
        "name": "Test Session",
        "status": "ACTIVE",
        "current_stage_id": "stage1",
        "completed_stages": [],
        "context": {},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_stage_instance():
    """提供模拟的阶段实例数据"""
    return {
        "id": "stage-instance-1",
        "session_id": "test-session",
        "stage_id": "stage1",
        "name": "Stage 1 Instance",
        "status": "ACTIVE",
        "completed_items": [],
        "context": {},
        "deliverables": {},
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": None,
    }

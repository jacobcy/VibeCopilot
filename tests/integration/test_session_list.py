#!/usr/bin/env python3

"""
会话列表测试脚本
"""

from src.db import get_session_factory, init_db
from src.flow_session.core.session_list import handle_list_sessions
from src.flow_session.manager import FlowSessionManager
from src.models.db import FlowSession

print("-- 直接查询数据库 --")
init_db()
s = get_session_factory()()
sessions = s.query(FlowSession).all()
print(f"会话总数: {len(sessions)}")
for fs in sessions[:3]:
    print(f"- ID: {fs.id}, 名称: {fs.name}, 工作流: {fs.workflow_id}")

print("\n-- 使用FlowSessionManager --")
manager = FlowSessionManager(s)
manager_sessions = manager.list_sessions()
print(f"manager返回会话总数: {len(manager_sessions)}")
for fs in manager_sessions[:3]:
    print(f"- ID: {fs.id}, 名称: {fs.name}, 工作流: {fs.workflow_id}")

print("\n-- 测试handle_list_sessions --")
result = handle_list_sessions(format="json")
print(f'找到会话: {len(result["sessions"])}')
for session in result["sessions"][:3]:
    print(f'- ID: {session.get("id")}, 名称: {session.get("name")}')
